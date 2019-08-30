import requests
import json
import asfgit.log
import asfgit.git
import re

# LDAP to CNAME mappings for some projects
WSMAP = {
    'whimsy': 'whimsical',
    'empire': 'empire-db',
    'webservices': 'ws'
}

def pelican(cfg, yml):
    pass

def github(cfg, yml):
    pass

def staging(cfg, yml):
    """ Staging for websites. Sample entry .asf.yaml entry:
      staging:
        profile: gnomes
        # would stage current branch at https://$project-gnomes.staged.apache.org/
        # omit profile to stage at $project.staged.a.o
    """
    # infer project name
    m = re.match(r"(?:incubator-)?([^-.]+)", cfg.repo_name)
    pname = m.group(1)
    pname = WSMAP.get(pname, pname)
    
    # Get branch
    ref = yml.get('refname', 'master').replace('refs/heads/', '')
    
    # If whoami specified, ignore this payload if branch does not match
    whoami = yml.get('whoami')
    if whoami and whoami != ref:
        return
    
    # Get profile from .asf.yaml, if present
    profile = yml.get('profile', '')
    
    # Try sending staging payload to pubsub
    try:
        payload = {
            'staging': {
                'project': pname,
                'source': "https://gitbox.apache.org/repos/asf/%s.git" % cfg.repo_name,
                'branch': ref,
                'profile': profile,
                'pusher': cfg.committer,
            }
        }
        requests.post("http://%s:%s%s" %
                      (cfg.gitpubsub_host, cfg.gitpubsub_port, cfg.gitpubsub_path),
                      data = json.dumps(payload))
        wsname = pname
        if profile:
            wsname += '-%s' % profile
        print("Staging contents at https://%s.staged.apache.org/ ..." % wsname)
    except Exception as e:
        print(e)
        asfgit.log.exception()
def publish(cfg, yml):
    """ Publishing for websites. Sample entry .asf.yaml entry:
      publish:
        whoami: asf-site
        # would publish current branch (if asf-site) at https://$project.apache.org/
    """
    # infer project name
    m = re.match(r"(?:incubator-)?([^-.]+)", cfg.repo_name)
    pname = m.group(1)
    pname = WSMAP.get(pname, pname)
    # Get branch
    ref = yml.get('refname', 'master').replace('refs/heads/', '')
    
    # If whoami specified, ignore this payload if branch does not match
    whoami = yml.get('whoami')
    if whoami and whoami != ref:
        return
    # Try sending publish payload to pubsub
    try:
        payload = {
            'publish': {
                'project': pname,
                'source': "https://gitbox.apache.org/repos/asf/%s.git" % cfg.repo_name,
                'branch': ref,
                'pusher': cfg.committer,
            }
        }
        requests.post("http://%s:%s%s" %
                      (cfg.gitpubsub_host, cfg.gitpubsub_port, cfg.gitpubsub_path),
                      data = json.dumps(payload))
        
        print("Publishing contents at https://%s.apache.org/ ..." % pname)
    except Exception as e:
        print(e)
        asfgit.log.exception()
