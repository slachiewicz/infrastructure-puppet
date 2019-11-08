local json = require 'cjson'
local https = require 'ssl.https'
local ip = require 'ip'
local stagger = math.random(0,60) -- stagger reloads by up to 60 seconds

local function getBans()
    local r, c, h, s = https.request("https://blocky.apache.org/blocky-public/bans")
    local data = json.decode(r)
    local blocks = {}
    for k, v in pairs(data.bans) do
        local block_parsed = ip.parse(v.ip)
        table.insert(blocks, {kind = block_parsed:kind(), cidr = block_parsed, reason = v.reason or "unknown"})
    end
    return blocks, os.time()
end

local blocks_cached, blocks_timestamp = getBans()
local block_index = {}

function handle(r)
    local now = os.time()
    if ( (now - (600 + stagger)) > blocks_timestamp) then
        blocks_cached, blocks_timestamp = getBans()
    end
    
    local is_blocked = false
    -- Check quick index first:
    if block_index[r.useragent_ip] then
        -- If we have a fresh index item, mark as blocked
        if block_index[r.useragent_ip] > (now - 600) then
            is_blocked = true
        -- If stale, remove and do full check
        else
            block_index[r.useragent_ip] = nil
        end
    end
    if not is_blocked then
        local myip = ip.parse(r.useragent_ip)
        local mykind = myip:kind()
        for _, block in pairs(blocks_cached) do
            if mykind == block.kind and myip:match(block.cidr) then
                is_blocked = block.reason
                break
            end
        end
    end
    
    -- If blocked, display bork
    if is_blocked then
        r.status = '429'
        r.content_type = 'text/html'
        r:puts(([[
                   <!DOCTYPE html>
                    <html>
                    <body>
                     
                        <h2>You've been banned from using services provided by The Apache Software Foundation.</h2>
                        <quote><p>The (automated) reason for your ban is: <kbd>%s</kbd>.<br/></quote>
                        <p><big>The following actions are <strong>NOT</strong> allowed on ASF services:</big></p>
                        <ul>
                            <li>Slow Loris-like abuse (too many request timeouts).</li>
                            <li>More than 200,000 pageviews on any box per 12 hours.</li>
                            <li>More than 100,000 JIRA requests per 24 hours.</li>
                            <li>More than 10,000 download page views per 24 hours.</li>
                            <li>More than 10,000 visits to our backup <code>dist/</code> area on www.apache.org per 24 hours.</li>
                            <li>More than 50 Gibibytes traffic per 12 hours (does not include mirrors, but does include archive.apache.org!).</li>
                            <li>More than 50,000 visits to archive.apache.org per 12 hours.</li>
                            <li>More than 100 mebibits/second sustained traffic for an hour or more.</li>
                            <li>More than 2,000 viewvc requests per 24 hours.</li>
                            <li>More than 100,000 confluence (cwiki.apache.org) page visits per 24 hours.</li>
                            <li>More than 10,000 bugzilla requests per 24 hours.</li>
                            <li>More than 1,000 gitbox requests per hour.</li>
                            <li>More than 75,000 repository.apache.org visits per 24 hours.</li>
                            <li>More than 100,000 builds.apache.org visits per 12 hours.</li>
                            <li>More than 2,500 code 429 (rate-limited) responses not respected per 12 hours.</li>
                        </ul>
                        <p>If you feel this has been in error, feel free to contact the ASF Infra team via the <a href="mailto:users@infra.apache.org">Infra Users list</a> with the subject "[IPBAN] InsertYourOrganizationHere", provide your IP address and any information or logs.</p>
                        <p><b>IMPORTANT:</b><br/>Before you contact the Apache Infrastructure team, make sure the above reported abuse activity is not taking place and will not take place in the future. If you have been banned for excessive use of a service, ensure that this activity is curbed <u>and make sure to notify infrastructure that you have taken these steps.</u></p>
                    </body>
                    </html>
               ]]):format(is_blocked))
        return apache2.DONE
    else
        return apache2.DECLINED
    end
end
