#!/usr/bin/env python3

import os
import sys
import cgi
import netaddr
import yaml
import requests
import json
import hashlib
import time
import messaging
import re

root_path = '/x1/repos' # This is our base
# Get all sub sections of our repo dir, ignore those with dots in them.
sections = [x for x in os.listdir(root_path) if os.path.isdir(os.path.join(root_path, x)) and '.' not in x]



def updateTicket(ticket, name, txt, worklog):
    auth = open("/x1/jirauser.txt").read().strip()
    auth = str(base64.encodestring(bytes(auth))).strip()

    # Post comment or worklog entry!
    headers = {"Content-type": "application/json",
                 "Accept": "*/*",
                 "Authorization": "Basic %s" % auth
                 }
    try:
        where = 'comment'
        data = {
            'body': txt
        }
        if worklog:
            where = 'worklog'
            data = {
                'timeSpent': "10m",
                'comment': txt
            }

        rv = requests.post("https://issues.apache.org/jira/rest/api/latest/issue/%s/%s" % (ticket, where),headers=headers, json = data)
        if rv.status_code == 200 or rv.status_code == 201:
            return "Updated JIRA Ticket %s" % ticket
        else:
            return rv.text
    except:
        pass # Not much to do just yet

def remoteLink(ticket, url, prno):
    auth = open("/x1/jirauser.txt").read().strip()
    auth = str(base64.encodestring(bytes(auth))).strip()

    # Post comment or worklog entry!
    headers = {"Content-type": "application/json",
                 "Accept": "*/*",
                 "Authorization": "Basic %s" % auth
                 }
    try:
        urlid = url.split('#')[0] # Crop out anchor
        data = {
            'globalId': "github=%s" % urlid,
            'object':
                {
                    'url': urlid,
                    'title': "GitHub Pull Request #%s" % prno,
                    'icon': {
                        'url16x16': "https://github.com/favicon.ico"
                    }
                }
            }
        rv = requests.post("https://issues.apache.org/jira/rest/api/latest/issue/%s/remotelink" % ticket,headers=headers, json = data)
        if rv.status_code == 200 or rv.status_code == 201:
            return "Updated JIRA Ticket %s" % ticket
        else:
            return rv.txt
    except:
        pass # Not much to do just yet

def addLabel(ticket):
    auth = open("/x1/jirauser.txt").read().strip()
    auth = str(base64.encodestring(bytes(auth))).strip()

    # Post comment or worklog entry!
    headers = {"Content-type": "application/json",
                 "Accept": "*/*",
                 "Authorization": "Basic %s" % auth
                 }
    data = {
        "update": {
            "labels": [
                {"add": "pull-request-available"}
            ]
        }
    }
    rv = requests.put("https://issues.apache.org/jira/rest/api/latest/issue/%s" % ticket,headers=headers, json = data)
    if rv.status_code == 200 or rv.status_code == 201:
        return "Added PR label to Ticket %s\n" % ticket
    else:
        sys.stderr.write(rv.text)
        return rv.text


def archive():
    # CGI interface
    xform = cgi.FieldStorage();

    # Check that this is GitHub calling
    from netaddr import IPNetwork, IPAddress
    GitHubNetwork = IPNetwork("192.30.252.0/22") # This is GitHub's current
                                                 # net block. May change!
    callerIP = IPAddress(os.environ.get('REMOTE_ADDR', '192.30.252.0'))
    if not callerIP in GitHubNetwork:
        print("Status: 401 Unauthorized\r\nContent-Type: text/plain\r\n\r\nI don't know you!\r\n")
        sys.exit(0)

    # Get JSON payload
    data = json.loads(xform.getvalue('payload', "{}"))

    if'repository' in data:
        repo = data['repository']['name']
    else:
        repo = None

    # Load the yaml
    yml = yaml.load(open("./archiver.yaml"))

    # Figure out which setting to use here
    default = 'default-unlisted'
    my_path = None
    for s in sections:
        tmp_path = "%s/%s/%s.git" % (root_path, s, repo)
        if os.path.isdir(tmp_path):
            my_path = tmp_path
            default = 'default-listed'
            break

    # Look for repo or project specific settings
    project = repo
    if my_path and repo:
        xrepo = repo.replace('incubator-', '')
        if '-' in xrepo:
            project, subrepo = xrepo.split('-', 1)
        if xrepo in yml:
            default = xrepo
        elif project in yml:
            default = project

    # Grab settings
    settings = yml[default]

    # Figure out which action happened

    action = None
    is_issue = False
    is_pr = False
    if 'action' in data:
        # PR or Issue??
        if 'issue' in data:
            is_issue = True
        elif 'pull_request' in data:
            is_pr = True

        # Issue opened or reopened
        if data['action'] in ['opened', 'reopened']:
            action = 'issue_opened'
        # Issue closed
        elif data['action'] == 'closed':
            action = 'issue_closed'
        elif data['action'] in ['created', 'edited']:
            action = 'commented'

        # Comment on issue or specific code (WIP)
        elif 'comment' in data:
            action = 'code_comment'
            # File-specific comment
            if 'path' in data['comment']:
                # Diff review
                if 'diff_hunk' in data['comment']:
                    action = 'diff_comment'
            # Standard commit comment
            elif 'commit_id' in data['comment']:
                action = 'commit_comment'


    # Okay, let's figure out what to do
    if action:
        user = data['sender']['login']
        subject = "[GitHub] [%s] " % (repo)
        body = ""
        link = None
        title = ""
        messageid = None
        if is_issue:
            no = data['issue']['number']
            title = data['issue']['title']
            if action == 'issue_opened':
                subject += "%s opened issue #%u: %s" % (user, data['issue']['number'], data['issue']['title'])
                body += data['issue']['body']
                messageid = "<%s-%s@gitbox.apache.org>" % (repo, no)
            elif action == 'issue_closed':
                subject += "%s closed issue #%u: %s" % (user, data['issue']['number'], data['issue']['title'])
                link = "<%s-%s@gitbox.apache.org>" % (repo, no)
                body = "[ issue closed by %s ]" % user
            elif action == 'commented':
                subject += "%s commented on issue #%u: %s" % (user, data['issue']['number'], data['issue']['title'])
                body += data['comment']['body']
                link = "<%s-%s@gitbox.apache.org>" % (repo, no)
            body += "\n\n[ Full content available at: %s ]\n" % data['issue']['html_url']
        elif is_pr:
            no = data['pull_request']['number']
            title = data['pull_request']['title']
            if action == 'issue_opened':
                subject += "%s opened pull request #%u: %s" % (user, data['pull_request']['number'], data['pull_request']['title'])
                body += data['pull_request']['body']
                messageid = "<%s-%s@gitbox.apache.org>" % (repo, no)
            elif action == 'issue_closed':
                subject += "%s closed pull request #%u: %s" % (user, data['pull_request']['number'], data['pull_request']['title'])
                body = "[ pull request closed by %s ]" % user
                link = "<%s-%s@gitbox.apache.org>" % (repo, no)
            elif action == 'commented':
                subject += "%s commented on pull request #%u: %s" % (user, data['pull_request']['number'], data['pull_request']['title'])
                body += data['comment']['body']
                link = "<%s-%s@gitbox.apache.org>" % (repo, no)
            body += "\n\n[ Full content available at: %s ]\n" % data['pull_request']['html_url']

        recipient = settings.get('pr', 'null')
        if recipient and '@' in recipient:
            sender = "%s (GitHub) <gitbox@apache.org>" % user
            body += "This message was relayed via gitbox.apache.org for %s\n" % recipient
            recipient = recipient.replace('$tlp', project)
            messaging.mail(link = link, sender = sender, subject = subject, recipient = recipient, message = body, messageid = messageid)

        # JIRA stuff?
        jira = settings.get('jira', 'null')
        if jira and jira != 'null':
            m = re.search(r"\b([A-Z]+-\d+)\b", title)
            if m:
                ticket = m.group(1)
                # Add PR label and remote link?
                if jira in ['link', 'worklog', 'comment']:
                    if is_pr:
                        addLabel(ticket)
                    remoteLink(ticket, url, no)
                # worklog or full-on comment?
                worklog = True if jira == 'worklog' else False
                # Update the ticket!
                updateTicket(ticket, user, body, worklog)


    # Tell github it's all okay
    print("Status: 204 Message received\r\n\r\n")


if __name__ == '__main__':
    archive()
