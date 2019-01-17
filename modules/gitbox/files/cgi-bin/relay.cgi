#!/usr/bin/env python3

import requests
import yaml
import json
import sys
import fnmatch

YAML_PATH = "/x1/gitbox/conf/relay.yaml"
YML = yaml.load(open(YAML_PATH))

PAYLOAD = json.load(sys.stdin)
PAYLOAD_FORMDATA = {
    'payload': json.dumps(payload)
}

HEADERS = {'User-Agent': 'GitBox Hook Relay/0.1'}

# determine what and where
repo = PAYLOAD['repository']['name']
what = 'commit'
if 'pull_request' in PAYLOAD:
    what = 'pr'
elif 'issue' in PAYLOAD:
    what = 'issue'

for key, entry in YML['relays'].items():
    if fnmatch.fnmatch(entry['repos'], repo): # If yaml entry glob-matches the repo, then...
        hook = entry.get('hook') # Hook URL to post to
        fmt = entry.get('format', 'formdata') # www-formdata or raw json expected by hook?
        wanted = entry.get('events', 'all') # Which events to trigger on; all, pr, issue, commit or a mix.
        enabled = entry.get('enabled', False) # Default to false, so we don't trigger bootstrap example
        try:
            if enabled and hook and (wanted == 'all' or what in wanted):
                if fmt == 'formdata':
                    requests.post(hook, data = payload_formdata, headers = HEADERS)
                elif fmt == 'json':
                    requests.post(hook, json = payload, headers = HEADERS)
        except:
            pass # fail silently if hook doesn't respond well

print("Status: 204 Handled\r\n\r\n")
