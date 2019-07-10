#!/usr/bin/env python3

import requests
import yaml
import json
import os
import sys
import fnmatch
import time
import ldap

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
    with open("/x1/gitbox/logs/relay-%s.log" % key, "a") as f:
        f.write(msg + "\n")
        f.close()

# determine what and where
repo = PAYLOAD['repository']['name']
what = 'commit'
if 'pull_request' in PAYLOAD:
    what = 'pr'
elif 'issue' in PAYLOAD:
    what = 'issue'
    
if what == 'pr':
  is_asf = gh_to_ldap(PAYLOAD['pull_request']['user']['login'])
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
                log_entry(key, "%s [%s]: Delivered %s payload for %s to %s: %u\n" % (DATE, GUID, what, repo, hook, rv.status_code))
        except requests.exceptions.RequestException as e:
            log_entry(key, "%s [%s]: Could not deliver %s payload for %s: %s" % (DATE, GUID, what, hook, e))
            
print("Status: 204 Handled\r\n\r\n")
