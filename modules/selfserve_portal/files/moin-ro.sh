#!/usr/bin/env bash

# This script marks the moin wiki read only.

if [ "$#" -ne 1 ]; then
    echo "Need to specify a moin project name as an arg: exiting."
exit 1;
fi

WIKI=$1.py
pushd config

if [[ ! -f $WIKI ]]; then
  echo "No config file named $WIKI exists! Exiting..."
  exit 1;
fi

/usr/bin/svn up
grep acl_enabled $WIKI
if [[ $? == 1 ]];then
cat >> $WIKI << EOL

    acl_enabled = 1
    acl_rights_default = "All:read"
EOL
  /usr/bin/svn ci -m "mark $WIKI read only, requested as part of moin -> cwiki migration."
else
  echo "wiki is already read only, doing nothing."
fi
popd
exit 0;

