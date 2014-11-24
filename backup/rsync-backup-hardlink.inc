######################################################################
# Use rsync to create to mirror the source folder, using hard links
# to the last existing copy, if possible
#
# NOTE: this is slow on btrfs, however, there are better ways
#       for btrfs volumes, anyway...

function doBackup {
    BACKUP_ROOT="${BACKUP_PREFIX}/$1"
    BACKUP_SOURCE="${2%/}/"
    EXTRA_OPTIONS="$3"

    if [ ! -d $BACKUP_PREFIX ]; then
       echo $BACKUP_PREFIX does not exist. Abort!
       exit 1
    fi

    mkdir -p "$BACKUP_ROOT"

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
    LAST_BACKUP_NAME=$(ls ${BACKUP_ROOT} | grep '@' | tail -n1)
    LAST_BACKUP=${BACKUP_ROOT}/${LAST_BACKUP_NAME}

    NEW_BACKUP=${BACKUP_ROOT}/$(date +$DATE_FORMAT)
    NEW_BACKUP_TMP=${BACKUP_ROOT}/working-$(date +%s)

    if [ ! -z "${BACKUP_SOURCE}" ] ; then
        echo -n "Doing a backup of $1 to $NEW_BACKUP,"
        if [ -z "${LAST_BACKUP_NAME}" ] ; then
            echo "using no reference"
            rsync -ax  ${EXTRA_OPTIONS} ${BACKUP_SOURCE} ${NEW_BACKUP_TMP}
        else
            echo "using $LAST_BACKUP as reference"
            rsync -ax --delete ${EXTRA_OPTIONS} --link-dest=${LAST_BACKUP} ${BACKUP_SOURCE} ${NEW_BACKUP_TMP}
        fi

        exit_code=$?

        case $exit_code in
            "24" | "0")
               # 24 means "file vanished" warning, which can be ignored
               mv ${NEW_BACKUP_TMP} ${NEW_BACKUP}
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

