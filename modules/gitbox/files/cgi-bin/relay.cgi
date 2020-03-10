#!/usr/bin/env python3

import requests
import yaml
import json
import os
import sys
import fnmatch
import time
import ldap
import datetime

LDAP_BASE = "ou=people,dc=apache,dc=org"
LDAP_URI = "ldaps://ldap-us-ro.apache.org:636"
YAML_PATH = "/x1/gitbox/conf/relay.yaml"
YML = yaml.load(open(YAML_PATH))

PAYLOAD = json.load(sys.stdin)
PAYLOAD_FORMDATA = {
    'payload': json.dumps(PAYLOAD)
}

GUID = os.environ.get('HTTP_X_GITHUB_DELIVERY',"")
EVENT = os.environ.get('HTTP_X_GITHUB_EVENT', "push")
SIG = os.environ.get('HTTP_X_HUB_SIGNATURE', "")
DATE = int(time.time())

HEADERS = {
    'User-Agent': os.environ.get('HTTP_USER_AGENT', 'GitHub-Hookshot/abcd'),
    'X-GitHub-Delivery': GUID,
    'X-GitHub-Event': EVENT,
    'X-Hub-Signature': SIG,
  }


def gh_to_ldap(username):
    ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
    l = ldap.initialize(LDAP_URI)
    # this search for all objectClasses that user is in.
    # change this to suit your LDAP schema
    search_filter= "(githubUsername=%s)" % username
    groups = []
    results = l.search_s(LDAP_BASE, ldap.SCOPE_SUBTREE, search_filter, ['dn',])
    for res in results:
        cn = res[0]
        groups.append(cn)
    return sorted(groups)


def log_entry(key, msg):
    now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
    with open("/x1/gitbox/logs/relay-%s.log" % key, "a") as f:
        f.write("[%s] %s\n" % (now, msg))
        f.close()

# determine what and where
repo = PAYLOAD['repository']['name']
what = 'commit'
who = 'unknown'
how = 'commit'
if 'pull_request' in PAYLOAD:
    what = 'pr'
    how = "PR #%s" % PAYLOAD['pull_request']['number']
elif 'issue' in PAYLOAD:
    what = 'issue'
    how = "Issue #%s" % PAYLOAD['issue']['number']
    if 'pull_request' in PAYLOAD['issue']:
        what = 'pr_comment'
        how = "PR #%s" % PAYLOAD['issue']['number']
    elif 'comment' in PAYLOAD['issue']:
        what = 'issue_comment'

if what == 'pr':
  # Is Proper Committer?
  who = PAYLOAD['pull_request']['user']['login']
  is_asf = gh_to_ldap(who)
  # Deemed safe committer by .asf.yaml?
  if not is_asf and os.path.exists("/x1/gitbox/conf/ghprb-whitelist/%s.txt" % repo):
        ghprb_whitelist = open("/x1/gitbox/conf/ghprb-whitelist/%s.txt" % repo).read().split("\n")
        if PAYLOAD['pull_request']['user']['login'] in ghprb_whitelist:
            is_asf = True
            log_entry('whitelist', "%s [%s]: %s payload for %s allowed via GHPRB Whitelist for %s" % (DATE, GUID, what, repo, PAYLOAD['pull_request']['user']['login']))
  # If we don't trust, abort immediately
  if not is_asf:
    print("Status: 204 Handled\r\n\r\n")
    sys.exit(0)

if what == 'pr_comment':
  # Is Proper Committer?
  who = PAYLOAD['comment']['user']['login']
  is_asf = gh_to_ldap(who)
  # Deemed safe committer by .asf.yaml?
  if not is_asf and os.path.exists("/x1/gitbox/conf/ghprb-whitelist/%s.txt" % repo):
        ghprb_whitelist = open("/x1/gitbox/conf/ghprb-whitelist/%s.txt" % repo).read().split("\n")
        if PAYLOAD['comment']['user']['login'] in ghprb_whitelist:
            is_asf = True
            log_entry('whitelist', "%s [%s]: payload for %s allowed via GHPRB Whitelist for %s" % (DATE, GUID, what, repo, PAYLOAD['comment']['user']['login']))
  # If we don't trust, abort immediately
  if not is_asf:
    print("Status: 204 Handled\r\n\r\n")
    sys.exit(0)

    
for key, entry in YML['relays'].items():
    if fnmatch.fnmatch(repo, entry['repos']): # If yaml entry glob-matches the repo, then...
        hook = entry.get('hook') # Hook URL to post to
        fmt = entry.get('format', 'formdata') # www-formdata or raw json expected by hook?
        wanted = entry.get('events', 'all') # Which events to trigger on; all, pr, issue, commit or a mix.
        enabled = entry.get('enabled', False) # Default to false, so we don't trigger bootstrap example
        try:
            if enabled and hook and (wanted == 'all' or what in wanted):
                if fmt == 'formdata':
                    rv = requests.post(hook, data = PAYLOAD_FORMDATA, headers = HEADERS)
                elif fmt == 'json':
                    rv = requests.post(hook, json = PAYLOAD, headers = HEADERS)
                log_entry(key, "%s [%s]: Delivered %s payload from %s for %s (%s) to %s: %u\n" % (DATE, GUID, what, who, repo, how, hook, rv.status_code))
        except requests.exceptions.RequestException as e:
            log_entry(key, "%s [%s]: Could not deliver %s payload from %s for %s (%s): %s" % (DATE, GUID, what, who, hook, how, e))
            
print("Status: 204 Handled\r\n\r\n")
