#!/bin/sh
# $Id: create-jmeter-nightlies-index.sh 1046614 2019-06-20 12:55:04Z fschumacher $

# This script is used by:
# https://svn.apache.org/repos/infra/infrastructure/buildbot/aegis/buildmaster/master1/projects/jmeter.conf

DATE_BIN=/bin/date
TODAY=$($DATE_BIN "+%Y-%m-%d")
NIGHTLIES_DIR='/x1/buildmaster/master1/public_html/projects/jmeter/nightlies'

# remove r* directories older than 30 days first.
if cd "$NIGHTLIES_DIR";then
  find . -mindepth 1 -maxdepth 1 -type d -name "r*" -mtime +29 -exec rm -rf {} \; 
else
  echo "Nightlies directory doesnt exist, exiting script."
  exit 1;
fi

# create page header
cat header.inc > index.html
cat body-top.inc >> index.html
cat << 'EOD' >> index.html
  <table width="85%" cellpadding="1" cellspacing="1" border="1"> <!-- table 4 -->
    <thead>
      <tr>
        <th>Revision</th>
        <th>Build Date</th>
        <th colspan="6">Binary archives (choose one)</th>
        <th colspan="6">Source archives (choose one)</th>
      </tr>
    </thead>
  <tbody>
EOD

# Find all directories named r*; remove leading r; descending numeric sort; pick first and add back r prefix
REV=$(find . -mindepth 1 -maxdepth 1 -type d -name "r*" | sed -e 's!./r!!' | sort -gr | sed -ne '1s!^!r!p')
REAL_REVISION=$(basename "$REV"/apache-jmeter-*_src.tgz | sed -e 's/^apache-jmeter-//;s/_src.tgz$//')

# Show LATEST
echo '
<tr style="background-color:#F5F5AE;">
<td>LATEST ('$REV')</td>
<td>'$TODAY'</td>
<td><a href="'$REV'/apache-jmeter-r'${REAL_REVISION}'.tgz">apache-jmeter-r'${REAL_REVISION}'.tgz</a></td>
<td><a href="'$REV'/apache-jmeter-r'${REAL_REVISION}'.tgz.md5">MD5</a></td>
<td><a href="'$REV'/apache-jmeter-r'${REAL_REVISION}'.tgz.sha">SHA</a></td>
<td><a href="'$REV'/apache-jmeter-r'${REAL_REVISION}'.zip">apache-jmeter-r'${REAL_REVISION}'.zip</a></td>
<td><a href="'$REV'/apache-jmeter-r'${REAL_REVISION}'.zip.md5">MD5</a></td>
<td><a href="'$REV'/apache-jmeter-r'${REAL_REVISION}'.zip.sha">SHA</a></td>
<td><a href="'$REV'/apache-jmeter-r'${REAL_REVISION}'_src.tgz">apache-jmeter-r'${REAL_REVISION}'_src.tgz</a></td>
<td><a href="'$REV'/apache-jmeter-r'${REAL_REVISION}'_src.tgz.md5">MD5</a></td>
<td><a href="'$REV'/apache-jmeter-r'${REAL_REVISION}'_src.tgz.sha">SHA</a></td>
<td><a href="'$REV'/apache-jmeter-r'${REAL_REVISION}'_src.zip">apache-jmeter-r'${REAL_REVISION}'_src.zip</a></td>
<td><a href="'$REV'/apache-jmeter-r'${REAL_REVISION}'_src.zip.md5">MD5</a></td>
<td><a href="'$REV'/apache-jmeter-r'${REAL_REVISION}'_src.zip.sha">SHA</a></td>
</tr>' >> index.html


# List files in the format
# drwxrwxr-x  2 user  group  2  23 Mar 10:23 r2000
# Field: 1    2  3     4     5  6   7    8     9
# We assume that the user and group don't have spaces in them.

#  The --full-time flag has been removed , we are on FreeBSD 10 now.
ls -dlt r* | while read LINE
do
  REV=$(echo "$LINE" | cut -d ' ' -f9)
  REAL_REVISION=$(basename "$REV"/apache-jmeter-*_src.tgz | sed -e 's/^apache-jmeter-//;s/_src.tgz$//')
  DATE=$(echo "$LINE" | cut -d ' ' -f6,7)
  # Now list all existing entries in reverse order
  if [ -r "${REV}/apache-jmeter-${REAL_REVISION}.zip" ]
  then
    echo '<tr>
<!-- $LINE -->
<td>'$REV'</td>
<td>'$DATE'</td>
<td><a href="'$REV'/apache-jmeter-'${REAL_REVSION}'.tgz">apache-jmeter-'${REAL_REVISION}'.tgz</a></td>
<td><a href="'$REV'/apache-jmeter-'${REAL_REVSION}'.tgz.md5">MD5</a></td>
<td><a href="'$REV'/apache-jmeter-'${REAL_REVSION}'.tgz.sha">SHA</a></td>
<td><a href="'$REV'/apache-jmeter-'${REAL_REVSION}'.zip">apache-jmeter-'${REAL_REVISION}'.zip</a></td>
<td><a href="'$REV'/apache-jmeter-'${REAL_REVSION}'.zip.md5">MD5</a></td>
<td><a href="'$REV'/apache-jmeter-'${REAL_REVSION}'.zip.sha">SHA</a></td>
<td><a href="'$REV'/apache-jmeter-'${REAL_REVSION}'_src.tgz">apache-jmeter-'${REAL_REVISION}'_src.tgz</a></td>
<td><a href="'$REV'/apache-jmeter-'${REAL_REVSION}'_src.tgz.md5">MD5</a></td>
<td><a href="'$REV'/apache-jmeter-'${REAL_REVSION}'_src.tgz.sha">SHA</a></td>
<td><a href="'$REV'/apache-jmeter-'${REAL_REVSION}'_src.zip">apache-jmeter-'${REAL_REVISION}'_src.zip</a></td>
<td><a href="'$REV'/apache-jmeter-'${REAL_REVSION}'_src.zip.md5">MD5</a></td>
<td><a href="'$REV'/apache-jmeter-'${REAL_REVSION}'_src.zip.sha">SHA</a></td>
</tr>' >> index.html
  fi
done

# Add the footer
cat << 'EOD' >> index.html
    </tbody>
  </table> <!-- end table 4 -->
EOD
cat body-btm.inc >> index.html
