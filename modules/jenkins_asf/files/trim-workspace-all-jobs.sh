#!/usr/local/bin/bash

# This script does a find for files older than an optional 
# arg or default value and deletes files that match. It 
# searches in directories based on $JENKINS_HOME and below
# based on a list provided below.

RUN_AS_USER=jenkins
NODES_DIR=/x1/jenkins/jenkins-home/nodes/
NODES_LIST='/tmp/nodeslist.txt'
LOGS_DIR='/x1/jenkins/logs'

# node specific vars
JENKINS_HOME=/home/jenkins
RANGE=31

# run this as the jenkins user
if [[ `whoami` != $RUN_AS_USER ]];then
  echo "Please run this script as the $RUN_AS_USER user only."
  exit 1
fi

# Below grep is disabled as it finds offline nodes we cant get to.
# So uses a static list until we maybe use a json file to get an
# upto date accurate live list.

# cd $NODES_DIR
# grep -ir host\> */config.xml | cut -d \> -f2 | cut -d \< -f1 > $NODES_LIST

# TODO Add check to only trim nodes if disk space more than 85% (?) full

if [[ -f "$NODES_LIST" ]]
  then
  while read -r node
  do
    echo "Logging in to node $node"
ssh -o BatchMode=yes -o ConnectionAttempts=1 -Ti $HOME/.ssh/id_rsa $node <<EOT

declare -a dirs=(
".m2/repository"
".yetus-m2"
".gradle"
"jenkins-slave/maven-repositories"
"jenkins-slave/workspace"
)

echo "Disk space before cleanup was:" > /tmp/diskcleanup.txt
df -h | grep ^/dev/sda1 >> /tmp/diskcleanup.txt

for dir in "\${dirs[@]}"
 do
  echo "checking for existance of $JENKINS_HOME/\$dir"
  if [[ -d "$JENKINS_HOME/\$dir" ]]
  then
    cd $JENKINS_HOME/\$dir    
    echo "Removing files older than $RANGE days"
    find $JENKINS_HOME/\$dir -type f -mtime +$RANGE -delete
  else
    echo "no results for $JENKINS_HOME/\$dir"
  fi
 done  # end of ssh and delete

echo "Disk space after cleanup is:" >> /tmp/diskcleanup.txt
df -h | grep ^/dev/sda1 >> /tmp/diskcleanup.txt

EOT
  echo "copying diskcleanup.txt to jenkins-master"
  echo "Value of node is $node"
  rsync $node:/tmp/diskcleanup.txt $LOGS_DIR/$node-diskcleanup-`date +%F`.txt
  done < $NODES_LIST # end of while read
fi # end nodes

