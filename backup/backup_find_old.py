#!/usr/bin/env python3

## not sure, what's broken in python2

## TODO: add possibility to load BackupAgeFreqDist from
##       a file in the root of the backup directory

from __future__ import print_function  # for python2
from os         import chdir, path
from glob       import iglob
from datetime   import date, datetime
from bisect     import bisect_left
from random     import sample
from sys        import stderr, argv, exit
from math       import floor, ceil

import pprint

pp = pprint.PrettyPrinter(indent=4)

DATE_FORMAT = "%Y-%m-%d@%H:%M:%S"
VERBOSE     = False

# maximum age in days ==> backup frequency (number / days)
# btrfs doesn't like too many snapshots
BackupAgeFreqDist = {     7 : 1,
                         15 : 0.75,
                         30 : 0.5,
                         60 : 10/30,
                        124 : 12/365,
                        355 : 1/300  # from there on...
                    }

##############################################################################

def getBackupDates(basedir):
    try:
        chdir(basedir)
        dirs = iglob("????-??-??@??:??:??")
        return ( datetime.strptime(x, DATE_FORMAT) for x in dirs)
    except NotADirectoryError:
        return []
   
##############################################################################

def getSortedBackupDates(basedir):
    today = datetime.today()
    skeys = sorted(BackupAgeFreqDist.keys())
    hist  = dict( ( (k, []) for k in skeys)) # dict of (empty) lists
    rest  = []
    oldest_so_far = -1

    for x in getBackupDates(basedir):
        delta  = today-x 
        keypos = bisect_left(skeys, delta.days)
        if keypos >= len(skeys):
            # special treatment for older entries
            oldest_so_far = max(delta.days, oldest_so_far)
            rest.append(x)
        else:
            key    = skeys[keypos]
            hist[key].append(x)

    if len(rest) > 0:
        # we have old backups, special handling for them
        oldest_age_configured = sorted(BackupAgeFreqDist.keys())[-1]
        oldest_age_freq       = BackupAgeFreqDist[oldest_age_configured]
        BackupAgeFreqDist[oldest_so_far] = oldest_age_freq
        hist[oldest_so_far] = rest

    if VERBOSE:
        print("Hist for dir %s:" % basedir)
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(hist)

    return hist

##############################################################################
def findBackupsForDeletion(basedir):
    if VERBOSE: print("Statistics for backup dir %s:" % basedir, file=stderr)

    hist      = getSortedBackupDates(basedir)
    todel     = []
    bins      = sorted(hist.keys())
    IVs       = map(lambda x,y: y-x, [0]+bins,bins) # calc interval len

    for int_len, key in zip(IVs, bins):
        wanted_events = ceil(BackupAgeFreqDist[key]*int_len)
        events        = hist[key]
        if VERBOSE:
            print("We have %i events (of %i) in slot: up to %i days (int len %i)" % (len(events), wanted_events, key, int_len))
            pp.pprint(events)

        if len(events) > wanted_events:
            # we'll have to select N backups which shall be deleted
            N = floor(len(events) - wanted_events)
            if VERBOSE: print("Will delete %i of %i " % (N, len(events)), file=stderr)
            todel.extend( sample( events, N))

    return todel

##############################################################################

def backupDateToDir(basedir, date):
    dirname = path.join(basedir, date.strftime(DATE_FORMAT))
    if not path.exists(dirname):
        print("Something must have gone wrong, %s doesn't exist!" % dirname, file=stderr)
    return dirname


##############################################################################

def main():
    if len(argv) <= 1:
        print("%s: expecting list of backup directories " % argv[0])
        exit(1)

    for backup_root in argv[1:]:
        if not path.exists(backup_root):
            if backup_root in [ "-v", "--verbose" ]:
                global VERBOSE
                VERBOSE=True
            else:
                print("Skipping not existing directory %s", file=stderr)
            continue
        
        for backup_date in findBackupsForDeletion(backup_root):
            print(backupDateToDir(backup_root, backup_date))



if __name__ == "__main__":
    main()
