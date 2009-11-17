#!/bin/bash
# based on code from http://www.contextualdevelopment.com/labs/

if [ $# -eq 2 ]; then
    REPODIR=$1
    BACKUPDIR=$2
else
    echo "Usage: svn-backup.sh REPOSITORYDIR BACKUPDIR"
    exit 1
fi

for REPOSITORY in $REPODIR/*
do
    
    REPO=`basename $REPOSITORY`
    BACKUP=$BACKUPDIR/$REPO

    REV_FILE=$BACKUP/rev
    mkdir -p $BACKUP/full $BACKUP/incremental

    REV1="" # instead of previous iteration's value
    [ -r $REV_FILE ]     && REV1=`head -1 $REV_FILE`
    [ "x$REV1" = "x" ]   && REV1=0

    REV2=`svnlook youngest $REPOSITORY`

    if [ $REV1 -eq 0 -o `date +%u` -eq 4 ]; then

        FNAME=$BACKUP/full/$REPO-`date +%Y%m%d`-R$REV2

        if [ -r $FNAME ]; then
            continue
        else
            svnadmin dump -q $REPOSITORY > $FNAME
            bzip2 $FNAME
        fi

    elif [ $REV1 != $REV2 ]; then

        REV1=`expr $REV1 + 1`
        FNAME=$BACKUP/incremental/$REPO-$REV1-$REV2
        svnadmin -q dump --incremental --revision $REV1:$REV2 $REPOSITORY > $FNAME
        bzip2 $FNAME

    else
        continue
    fi

    # update the state file
    echo $REV2 > $REV_FILE

    # delete backups older than 21 days
    find $BACKUP/full $BACKUP/incremental -type f -mtime +21 -exec rm {} \;

done
