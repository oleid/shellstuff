#!/bin/sh

for dir in $(/usr/local/sbin/thin_out.py /mirror/*); do
   btrfs subvol del $dir
done
