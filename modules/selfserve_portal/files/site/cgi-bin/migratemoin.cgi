#!/usr/bin/env python
#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import json
import os
import sys
import time
import cgi
import requests
import base64
import subprocess
import re
import uuid
import sscommon

requser = os.environ['REMOTE_USER']

form = cgi.FieldStorage();

moinwiki = form.getvalue('moinwiki', None)
if not moinwiki or not re.match(r"^[a-z0-9]+$"], moinwiki):
    sscommn.buggo("Invalid Moin Wiki name!")

space = form.getvalue('space', None)
if not space or not re.match(r"^[A-Z0-9]+$", space):
    sscommon.buggo("Invalid Confluence Space name!")

moinpath = '/usr/local/etc/moin-to-cwiki/universal-wiki-converter'
moinscript = '%s/run_cmdline.sh' % moinpath
settingsconf = 'confluenceSettings.properties'
exporterconf = 'exporter.moinmoin.properties'
converterconf = 'converter.moinmoin.properties'

os.chdir(moinpath)

#try:

    # Check that the moin wiki exists before we start
    #subprocess.check_output([
    # ...
    #    ], stderr=subprocess.STDOUT)

#except:
#    print("Status: 500 Migration failed\r\n\r\n<h2>Moin to Confluence migration failed!</h2><pre>Invalid Moin wiki name: %s was not found!</pre>" % str(moinwiki))
#    sys.exit(0)

#try:

    # Check that the Confluence Space exists before we start
    #subprocess.check_output([
    # ...
    #    ], stderr=subprocess.STDOUT)

#except:
#    print("Status: 500 Migration failed\r\n\r\n<h2>Moin to Confluence migration failed!</h2><pre>Invalid Confluence Space name: %s was not found!</pre>" % str(space))
#    sys.exit(0)

try:

    # Test auth to Confluence via uwc.
    subprocess.check_output([
        moinscript, '-t', 'conf/%s' % settingsconf
        ], stderr=subprocess.STDOUT)
    # Todo: At this point update the progress bar to a hard coded 5% for now and feedback that the auth test is complete.

    # Fetch Moin wiki data subdirs 'pages' and 'user' from moin-vm

    # Export the moin pages to txt format before converting to Confluence format.
    # Save to a $moinwiki-pages-out directory for processing
    subprocess.check_output([
        moinscript, '-e', 'conf/%s' % exporterconf
        ], stderr=subprocess.STDOUT)
    # Todo: At this point update the progress bar to a hard codes 20% for now and inform that the initial export is complete.

    # Convert exported pages to Confluence format ..
    # .. and then import the pages to the Confluence space.
    subprocess.check_output([
        moinscript, '-c', 'conf/%s' % settingsconf, 'conf/%s' % converterconf,'%s/projects/%s/%s-pages-out' % (moinpath,moinwiki,moinwiki)
        ], stderr=subprocess.STDOUT)
    # Todo: Somewhere here we could count total pages exported in the previous step and update the progress bar as a percentage of 75%/numpages left

    # All done!

    sscommon.sendemail("%s@apache.org" % requser, "Moin wiki %s successfully migrated to Confluence space %s" % (moinwiki, space))
"""
Hi there,
As requested by %s@apache.org, migration from moin wiki %s to Confluence space has been completed at:
https://cwiki.apache.org/confluence/display/%s

""" % (requser, moinwiki, space))

    sscommon.slack("Migration from Moin wiki %s to Confluence space, <https://cwiki.apache.org/confluence/display/%s>, has been completed as requested by %s@apache.org." % (moinwiki, space, requser))
    print("Status: 201 Created\r\n\r\n<h2>Moin to Confluence migration completed!</h2>Your moin wiki has been migrated to Confluence, and can be accessed at: <a href='https://cwiki.apache.org/confluence/display/%s'>https://cwiki.apache.org/confluence/display/%s</a>." % (space, space))

except subprocess.CalledProcessError as err:
    uid = uuid.uuid4()
    with open("/tmp/%s.log" % uid, "w") as f:
        f.write(err.output)
        f.close()

    sscommon.slack("A moin wiki (%s) to Confluence migration, <kbd><a href='https://cwiki.apache.org/confluence/display/%s'>https://cwiki.apache.org/confluence/display/%s</a></kbd>, was attempted as requested by %s@apache.org, however one of more components of the setup failed. /tmp/%s.log may have more information" % (moinwiki, space, requser, uid))
    print("Status: 500 Creation failed\r\n\r\n<h2>Moin to Confluence migration failed!</h2><pre>Migration may have failed. Contact an administrator for more information. Error ID: %s</pre>" % uid)
