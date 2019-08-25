#!/usr/bin/env python
import os
import sys
if not os.environ.get("ASFGIT_ADMIN"):
    print("Invalid server configuration.")
    sys.exit(1)
sys.path.append(os.environ["ASFGIT_ADMIN"])
import yaml
import subprocess
import asfpy.messaging
import asfgit.cfg as cfg
import asfgit.asfyaml

DEFAULT_CONTACT = 'team@infra.apache.org' # Set to none to go to default project ML

def has_feature(name):
    try:
        return callable(getattr(asfgit.asfyaml,name))
    except AttributeError:
        return False

def get_yaml():
    committer = cfg.committer
    blamemail = "%s@apache.org" % committer
    main_contact = DEFAULT_CONTACT or cfg.recips[0] #commits@project or whatever is set in git config?
    
    # We just need the first line, as that has the branch affected:
    line = sys.stdin.readline().strip()
    if not line:
        return
    [oldrev, newrev, refname] = line.split()
    try:
        FNULL = open(os.devnull, 'w')
        ydata = subprocess.check_output(("/usr/bin/git", "show", "%s:.asf.yaml" % refname), stderr = FNULL)
    except:
        ydata = ""
    if not ydata:
        return
    try:
        config = yaml.safe_load(ydata)
    except yaml.YAMLError as e:
        asfpy.messaging.mail(recipients = [blamemail, main_contact], subject = "Failed to parse .asf.yaml in %s.git!" % cfg.repo_name, message = str(e))
        return
    
    if config:
        
        # Validate
        errors = ""
        for k in config:
            if not has_feature(k):
                errors += "Found unknown feature entry '%s' in .asf.yaml!\n" % k
        if errors:
            subject = "Failed to parse .asf.yaml in %s!" % cfg.repo_name
            asfpy.messaging.mail(recipients = [blamemail, main_contact], subject = subject, message = errors)
            return
        
        # Run parts
        for k, v in config.iteritems():
            func = getattr(asfgit.asfyaml,k)
            try:
                func(cfg, v)
            except Exception as e:
                msg = "An error occurred while running %s feature in .asf.yaml!:\n%s" % e
                subject = "Error while running %s feature from .asf.yaml in %s!" % (k, cfg.repo_name)
                asfpy.messaging.mail(recipients = [blamemail, main_contact], subject = subject, message = msg)

if __name__ == '__main__':        
    get_yaml()
