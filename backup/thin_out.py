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

DATE_FORMAT = "%Y-%m-%d@%H:%M:%S"
VERBOSE     = False

# maximum age in days ==> maximal number of backups per month
BackupAgeFreqDist = {   182 : 31,
                      1*365 : 20, 
                      2*356 : 15, 
                      3*365 : 1, 
                      4*365 : 1.0/12 }

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
    hist  = dict( ( (k, {}) for k in skeys)) # dict of (empty) dicts
    
    for x in getBackupDates(basedir):
        delta  = today-x 
        keypos = bisect_left(skeys, delta.days)
        keypos = len(skeys)-1 if keypos >= len(skeys) else keypos
        key    = skeys[keypos]
        
        # test, if year oder year+month shall be used depending on the given frequency
        where = x.year*366 + x.month if BackupAgeFreqDist[key] >= 1 else x.year*366
        # add backup to list of backups for this date
        if where in hist[key]:
            hist[key][where].append(x)
        else:
            hist[key][where] = [ x ]
    return hist

##############################################################################

def findBackupsForDeletion(basedir):
    if VERBOSE: print("Statistics for backup dir %s:" % basedir, file=stderr)

    hist  = getSortedBackupDates(basedir)
    todel = []

    for key in  sorted(BackupAgeFreqDist.keys()):
        wanted_freq = BackupAgeFreqDist[key]
        for period in sorted(hist[key]):
            year  = period / 366
            month = period % 366
            freq  = len(hist[key][period]) / (1.0 if wanted_freq >= 1 else 12.0)
            if VERBOSE: print("%i-%i : %f %f" % (year,month, freq, wanted_freq), file=stderr)
            
            if freq > wanted_freq:
                # we'll have to select N backups which shall be deleted
                N = round((freq - wanted_freq) * ( 1 if wanted_freq >= 1 else 12))
                what = hist[key][period]
                if VERBOSE: print("Will delete %i of %i " % (N, len(what)), file=stderr)
                if VERBOSE: print(what, file=stderr)
                todel.extend( sample( what, N))
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
                VERBOSE=True
            else:
                print("Skipping not existing directory %s", file=stderr)
            continue
        
        for backup_date in findBackupsForDeletion(backup_root):
            print(backupDateToDir(backup_root, backup_date))



if __name__ == "__main__":
    main()
