#!/usr/bin/env python
import os
import sys
if not os.environ.get("ASFGIT_ADMIN"):
    print "Invalid server configuration."
    exit(1)
sys.path.append(os.environ["ASFGIT_ADMIN"])
import yaml
import subprocess
import asfpy.messaging
import asfgit.cfg as cfg

def get_yaml():
    committer = cfg.committer
    blamemail = cfg.remote_user
    
    # We just need the first line, as that has the branch affected:
    line = sys.stdin.readline()
    if not line:
        return
    [oldrev, newrev, refname] = line.split(None, 2)
    try:
        ydata = subprocess.check_output(("/usr/bin/git", "show", "%s:.asf.yaml" % refname))
    except:
        ydata = ""
    if not ydata:
        return
    try:
        config = yaml.safe_load(ydata)
    except yaml.YAMLError as e:
        asfpy.messaging.mail(recipients = [blamemail, 'team@infra.apache.org'], subject = "Failed to parse .asf.yaml in %s!" % cfg.repo_name, message = str(e))
        return
    
    if config:
        msg = "Found changes pushed by %s:\n\n%s" % (committer, ydata)
        asfpy.messaging.mail(recipient = 'team@infra.apache.org', subject = "Found .asf.yaml in %s (%s)" % (cfg.repo_name, refname), message = msg)

if __name__ == '__main__':        
    get_yaml()
