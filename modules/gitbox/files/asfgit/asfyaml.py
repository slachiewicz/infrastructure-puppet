import requests
import json
import asfgit.log
import asfgit.git
import re
import github as pygithub
import os
import yaml

# LDAP to CNAME mappings for some projects
WSMAP = {
    'whimsy': 'whimsical',
    'empire': 'empire-db',
    'webservices': 'ws'
}

def pelican(cfg, yml):
    pass

def github(cfg, yml):
    """ GitHub settings updated. Can set up description, web site and topics """
    # Test if we need to process this
    ref = yml.get('refname', 'master').replace('refs/heads/', '')
    if ref not in ['master', 'asf-site']:
        print("Saw GitHub meta-data in .asf.yaml, but not master or asf-site, not updating...")
        return
    process = True
    ymlfile = '/tmp/ghsettings.%s.yml' % cfg.repo_name
    try:
        if os.path.exists(ymlfile):
            oldyml = yaml.safe_load(open(ymlfile).read())
            if cmp(oldyml, yml) == 0:
                process = False
    except yaml.YAMLError as e: # Failed to parse old yaml? bah.
        pass
    
    # Update items
    if process:
        print("GitHub meta-data changed, updating...")
        GH_TOKEN = open('/x1/gitbox/matt/tools/asfyaml.txt').read().strip()
        GH = pygithub.Github(GH_TOKEN)
        repo = GH.get_repo('apache/%s' % cfg.repo_name)
        # If repo is on github, update accordingly
        if repo:
            desc = yml.get('description')
            topics = yml.get('labels')
            homepage = yml.get('homepage')
            if desc:
                repo.edit(description=desc)
            if homepage:
                repo.edit(homepage=homepage)
            if topics and type(topics) is list:
                canset = True
                for topic in topics:
                    if not re.match(r"^[-a-z0-9]{1,35}$", topic):
                        print(".asf.yaml: Invalid GitHub label '%s' - must be lowercase alphanumerical and <= 35 characters!" % topic)
                        canset = False
                        break
                if canset:
                    repo.replace_topics(topics)
            print("GitHub repository meta-data updated!")
            
            # Save cached version for late checks
            with open(ymlfile, "w") as f:
                f.write(yaml.dump(yml, default_flow_style=False))

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
