#!/bin/bash

MOINDATA="/usr/local/etc/moin-to-cwiki/universal-wiki-converter/projects"

cd $MOINDATA

  rsync -av --progress --password-file=/root/.pw-moin \
    --include data/\*/data/pages         \
    --include data/\*/data/user         \
    --exclude \*\*/data/event-log \
    --exclude cache \
    rsync://apb-moin@moin-vm/moin $MOINDATA

