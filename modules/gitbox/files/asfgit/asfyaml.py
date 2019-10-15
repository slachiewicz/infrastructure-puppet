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
    'webservices': 'ws',
    'infrastructure': 'infra',
}

def pelican(cfg, yml):
    """ Pelican auto-build """
    
    # Don't build from asf-site, like...ever
    ref = yml.get('refname', 'master').replace('refs/heads/', '')
    if ref == 'asf-site':
        print("Not auto-building from asf-site, ever...")
        return
    
    # If whoami specified, ignore this payload if branch does not match
    whoami = yml.get('whoami')
    if whoami and whoami != ref:
        return
    
    # Get target branch, if any, default to same branch
    target = yml.get('target', ref)
    
    # Get optional theme
    theme = yml.get('theme', 'theme')
    
    # infer project name
    m = re.match(r"(?:incubator-)?([^-.]+)", cfg.repo_name)
    pname = m.group(1)
    pname = WSMAP.get(pname, pname)
    
    # Contact buildbot 2
    bbusr, bbpwd = open("/x1/gitbox/auth/bb2.txt").read().strip().split(':', 1)
    import requests
    s = requests.Session()
    s.get("https://ci2.apache.org/auth/login", auth= (bbusr, bbpwd))
    
    payload = {
        "method": "force",
        "jsonrpc": "2.0",
        "id":0,
        "params":{
            "reason": "Triggered pelican auto-build via .asf.yaml by %s" % cfg.committer,
            "builderid": "3",
            "source": "https://gitbox.apache.org/repos/asf/%s.git" % cfg.repo_name,
            "sourcebranch": ref,
            "outputbranch": target,
            "project": pname,
            "theme": theme,
        }
    }
    s.post('https://ci2.apache.org/api/v2/forceschedulers/pelican_websites', json = payload)


def github(cfg, yml):
    """ GitHub settings updated. Can set up description, web site and topics """
    # Test if we need to process this
    ref = yml.get('refname', 'master').replace('refs/heads/', '')
    if ref != 'master':
        print("Saw GitHub meta-data in .asf.yaml, but not master branch, not updating...")
        return
    # Check if cached yaml exists, compare if changed
    ymlfile = '/tmp/ghsettings.%s.yml' % cfg.repo_name
    try:
        if os.path.exists(ymlfile):
            oldyml = yaml.safe_load(open(ymlfile).read())
            if cmp(oldyml, yml) == 0:
                return
    except yaml.YAMLError as e: # Failed to parse old yaml? bah.
        pass
    
    # Update items
    print("GitHub meta-data changed, updating...")
    GH_TOKEN = open('/x1/gitbox/matt/tools/asfyaml.txt').read().strip()
    GH = pygithub.Github(GH_TOKEN)
    repo = GH.get_repo('apache/%s' % cfg.repo_name)
    # If repo is on github, update accordingly
    if repo:
        desc = yml.get('description')
        homepage = yml.get('homepage')
        merges = yml.get('enabled_merge_buttons:')
        topics = yml.get('labels')

        if desc:
            repo.edit(description=desc)
        if homepage:
            repo.edit(homepage=homepage)
        if merges:
             repo.edit(allow_squash_merge=merges.get("squash", False),
                allow_merge_commit=merges.get("merge", False),
                allow_rebase_merge=merges.get("rebase", False))
        if topics and type(topics) is list:
            for topic in topics:
                if not re.match(r"^[-a-z0-9]{1,35}$", topic):
                    raise Exception(".asf.yaml: Invalid GitHub label '%s' - must be lowercase alphanumerical and <= 35 characters!" % topic)
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
    
    # Get optional target domain:
    target = yml.get('hostname', pname)
    if 'apache.org' in target:
        raise Exception(".asf.yaml: Invalid hostname '%s' - you cannot specify *.apache.org hostnames, they must be inferred!" % target)
    
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
                'target': target,
            }
        }
        requests.post("http://%s:%s%s" %
                      (cfg.gitpubsub_host, cfg.gitpubsub_port, cfg.gitpubsub_path),
                      data = json.dumps(payload))
        
        print("Publishing contents at https://%s.apache.org/ ..." % pname)
    except Exception as e:
        print(e)
        asfgit.log.exception()
