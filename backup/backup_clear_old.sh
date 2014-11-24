#!/bin/sh

BACKUP_ROOT=/mirror

for dir in $(backup_find_old.py "$BACKUP_ROOT"/*); do
   btrfs subvol del $dir
   # or rm -Rf $dir in case of the hardlink version
done
