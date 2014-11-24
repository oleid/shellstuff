#!/bin/bash

BACKUP_PREFIX=/mirror

DATE_FORMAT="%Y-%m-%d@%H:%M:%S"
EXTRA_OPTIONS=""

#################################
# The backup function uses this function
# to inform the administrator in case something
# bad happens; adapt to your liking...
function informAdmin {
    SUBJECT="$1"
    BODY="$2"

    echo -e "Subject: $SUBJECT\n$BODY" | /usr/sbin/sendmail  root@localhost
}
#################################

# NOTE: you probably want to move this file to e.g.
#      /usr/local/share or similar
source ./rsync-backup-btrfs.inc



echo "Start of backup: $(date)"

if [ -z $(mount | awk "\$3 == \"$BACKUP_PREFIX\" {print \$1}") ]; then
   echo "$BACKUP_PREFIX not mounted, doing nuthing"
   exit 1
fi



# doBackup "directory below $BACKUP_PREFIX" "rsync source"
#doBackup "hercules_home" "home-srv::home"
#doBackup "hercules"      "home-srv::root"
doBackup "alef"          "alef::root"
#doBackup "alef_var"      "alef::var"
#doBackup "durga"         "durga::root"
#doBackup "hercules_client"  "home-srv::client"

echo "End of backup: $(date)"
echo

