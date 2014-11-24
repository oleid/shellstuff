
######################################################################
# Sync folder current with current state, use btrfs to make a snapshot

function doBackup {
    BACKUP_ROOT="${BACKUP_PREFIX}/$1"
    BACKUP_SOURCE="${2%/}/"
    RSYNC_DEST="$BACKUP_ROOT/current"

    if [ ! -d $BACKUP_PREFIX ]; then
       echo $BACKUP_PREFIX does not exist. Abort!
       exit 1
    fi

    if [ ! -d "$BACKUP_ROOT/current" ] ; then
        echo "Subvolume current doesn't exist. Create it"
        mkdir -p "$BACKUP_ROOT"
        /sbin/btrfs subvolume create  $RSYNC_DEST || exit 1
    fi

    if [ -z "$DATE_FORMAT" ]; then
        DATE_FORMAT="%Y-%m-%d@%H:%M:%S"
    fi

    # backup using a write lock to the root directory,
    # so that we don't have multiple rsyncs messing with the current folder

    # trying to aquire a lock here
    LCK="$BACKUP_ROOT/.lockfile"
    echo -n "Trying to aquire lock for $BACKUP_ROOT ."

    exec 8>$LCK;

    while true; do
       flock -w 180 -E 99 -x 8
       if [ $? -eq 99 ] ; then
          echo -n "."
          continue
       fi
       break
    done
    echo "done"
    # at this point, the operations are exclusive
    NEW_BACKUP=${BACKUP_ROOT}/$(date +$DATE_FORMAT)

    if [ ! -z "${BACKUP_SOURCE}" ] ; then
        echo "Doing a backup of $1, creating a read-only snapshot to $NEW_BACKUP"

        rsync -ax --delete ${EXTRA_OPTIONS} ${BACKUP_SOURCE} ${RSYNC_DEST}
        exit_code=$?

        case $exit_code in
            "24" | "0")
               # 24 means "file vanished" warning, which can be ignored
               /sbin/btrfs subvolume snapshot -r ${RSYNC_DEST} ${NEW_BACKUP}
               echo "Backup of $2 successfull"
               ;;
            * )
               echo "ERROR: Something went wrong during backup."
               informAdmin "Backup on $(hostname)" "Error backuping ${BACKUP_SOURCE}, exit code was $exit_code"
               ;;
        esac
    else
        echo "ERROR: I don't know how to backup $1"
    fi
    flock -u 8
}

