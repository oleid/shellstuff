#!/bin/sh

for dir in $(/usr/local/sbin/thin_out.py /mirror/*); do
   btrfs subvol del $dir
   # or rm -Rf $dir in case of the hardlink version
done
