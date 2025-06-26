#! /usr/bin/env python
########################################################################
#
# Name: check_crt_merge.py
#
# Purpose: Check whether a file or dataset has proper crt merging.
#
# Usage:
#
# check_crt_merge.py [options]
#
# Options:
#
# -h|--help - Print help message.
# -f|--file - Specify single file.
# -d|--def  - Specify dataset.
# -n        - Number of dataset files to chedk (default 10).
#
########################################################################
#
# Created: 17-Nov-2023  H. Greenlee
#
########################################################################

from __future__ import print_function
import sys, os, random
import samweb_cli

# Global variables.

samweb = samweb_cli.SAMWebClient(experiment = 'uboone')


# Help function.

def help():

    filename = sys.argv[0]
    file = open(filename, 'r')

    doprint=0
    
    for line in file.readlines():
        if line[2:].startswith('check_crt_merge.py'):
            doprint = 1
        elif line.startswith('######') and doprint:
            doprint = 0
        if doprint:
            if len(line) > 2:
                print(line[2:], end='')
            else:
                print()


# Filter grandparents out of parent list.

def filter_parents(parents):

    result = set(parents)

    # Loop over original parents.

    for parent in parents:
        gparents = samweb.listFiles('isparentof:( file_name %s ) with availability anylocation' % parent)
        for gparent in gparents:
            if gparent in result:
                result.remove(gparent)

    # Done.

    return result


# Get CRT (re)merge fcl.
# Return name and ups version of fcl.

def get_crt_merge_fcl(f):

    fclname = ''
    fclversion = ''

    md = samweb.getMetadata(f)
    if 'fcl.name' in md:
        fclname = md['fcl.name']

        # If this is a standard merge fcl, check unmerged parents.

        if fclname.startswith('merge'):
            parents = samweb.listFiles('isparentof:( file_name %s ) and not file_name CRT%% with availability anylocation' % f)
            fparents = filter_parents(parents)
            if len(fparents) > 0:
                mdp = samweb.getMetadata(fparents.pop())
                if 'fcl.name' in mdp:
                    fclname = mdp['fcl.name']
                if 'fcl.version' in mdp:
                    fclversion = mdp['fcl.version']
        else:
            if 'fcl.version' in md:
                fclversion = md['fcl.version']

    # Done.

    return fclname, fclversion


# Recursively extract top panel CRT parent, and immediate parent of CRT file.

def get_crt_parent(f):

    crt = ''

    while True:

        # Look for top panel CRT parent.

        crts = samweb.listFiles('isparentof:( file_name %s ) and file_name CRTHits%%-crt01.1%%' % f)
        if len(crts) > 0:
            crt = crts[0]
            break

        # This file doesn't have CRT parents.  Find non-CRT parent

        parents = samweb.listFiles('isparentof:( file_name %s )' % f)
        if len(parents) == 0:
            break
        f = parents[0]

    # Done.

    return crt, f


# Check CRT status of a single file.
# Return False if remerge recommended.

def check_file(filename):

    # Check file.

    print('\nChecking file %s' % filename)

    # Get metadata of this file.

    md = samweb.getMetadata(filename)

    # Extract run number.

    run = -1
    if 'runs' in md:
        runs = md['runs']
        if len(runs) > 0:
            run = runs[0][0]

    if run >= 0:
        print('Run number %d' % run)
    else:
        print('Unable to determine run number.')
        return False

    # Determine epoch (2b-5).

    epoch=''
    if run <= 25769:
        epoch = '5'
    if run <= 24319:
        epoch = '4d'
    if run <= 22269:
        epoch = '4c'
    if run <= 21285:
        epoch = '4b'
    if run <= 19752:
        epoch = '4a'
    if run <= 18960:
        epoch = '3b'
    if run <= 14116:
        epoch = '3a'
    if run <= 13696:
        epoch = '2b'
    if run <= 11048:
        epoch = ''

    if epoch != '':
        print('Epoch run %s' % epoch)
    else:
        print('Unable to determine epoch.')
        return False

    # Extract top panel CRT parent

    crtfile, pfile = get_crt_parent(filename)

    # Check swizzler version of the CRT file.

    crtsamok = False
    crtupsok = False
    if crtfile != '':
        print('Found top panel CRT parent %s' % crtfile)
        mdcrt = samweb.getMetadata(crtfile)
        samv = ''
        upsv = ''
        if 'ub_project.version' in mdcrt:
            samv = mdcrt['ub_project.version']
        if 'fcl.version' in mdcrt:
            upsv = mdcrt['fcl.version']
        if samv == '':
            print('Unable to determine CRT SAM version.')
        else:
            print('CRT swizzler SAM version %s' % samv)
        if upsv == '':
            print('Unable to determine CRT UPS version.')
        else:
            print('CRT swizzler UPS version %s' % upsv)

        # Check UPS version.

        if epoch <= '3a':
            if upsv >= 'v06_26_01_26':
                crtupsok = True
        else:
            if (upsv >= 'v06_26_01_13' and upsv < 'v06_26_01_25') or upsv >= 'v06_26_01_33':
                crtupsok = True

        # Check SAM version.

        if epoch == '2b' or epoch == '3a':
            if samv == 'prod_v06_26_01_26':
                crtsamok = True
        elif epoch == '3b' or epoch == '4a':
            if samv == 'prod_v06_26_01_13':
                crtsamok = True
        elif epoch == '4b' or epoch == '4c' or epoch == '4d' or epoch == '5':
            if samv == 'prod_v06_26_01_33' or samv == 'prod_v06_26_01_13':
                crtsamok = True
    else:
        print('Unable to determine top panel CRT parent.')

    # Also check CRT merging fcl.

    fclok = False
    fclvok = False
    print('Checking CRT (re)merge fcl.')
    fclname, fclversion = get_crt_merge_fcl(pfile)

    if fclname != '':
        print('CRT merge fcl name %s' % fclname)
        print('CRT merge fcl version %s' % fclversion)
        if fclname.find('merge_extra') >= 0:
            fclok = True
        if fclversion.startswith('v06') and fclversion >= 'v06_26_01_30':
            fclvok = True
        if fclversion.startswith('v08') and fclversion >= 'v08_00_00_08':
            fclvok = True
        if fclversion.startswith('v10'):    # Update in Mar. 2025 to support MCC9.10
            fclvok = True
    else:
        print('Unable to determine CRT (re)merge fcl.')
    

    if crtsamok:
        print('Top panel CRT swizzler SAM version OK.')
    else:
        print('Top panel CRT swizzler SAM version bad.')

    if crtupsok:
        print('Top panel CRT swizzler UPS version OK.')
    else:
        print('Top panel CRT swizzler UPS version bad.')

    if fclok:
        print('CRT merge FCL name OK.')
    else:
        print('CRT merge FCL name bad.')

    if fclvok:
        print('CRT merge FCL version OK.')
    else:
        print('CRT merge FCL version bad.')

    if not crtupsok or not fclok or not fclvok:
        print('##### CRT remerge recommended #####')
        return False

    # Done (success).

    return True



# Main function.

def main(argv):

    # Statistics.

    nfile = 0
    nfileok = 0

    # Parse arguments.

    defname = ''
    filename = ''
    ncheck = 10

    args = argv[1:]
    while len(args) > 0:
        if args[0] == '-h' or args[0] == '--help' :
            help()
            return 0
        elif (args[0] == '-d' or args[0] == '--def') and len(args) > 1:
            defname = args[1]
            del args[0:2]
        elif (args[0] == '-f' or args[0] == '--file') and len(args) > 1:
            filename = args[1]
            del args[0:2]
        elif (args[0] == '-n') and len(args) > 1:
            ncheck = int(args[1])
            del args[0:2]
        else:
            print('Unknown option %s' % args[0])
            sys.exit(1)

    # Make sure at least one of defname or filename was specified.

    if defname == '' and filename == '':
        print('No dataset or file name specified.')
        sys.exit(1)

    # Make sure defname and filename were not both specified.

    if defname != '' and filename != '':
        print('Only specify one of dataset or file name.')
        sys.exit(1)

    # Make a set of filenames to check.

    files_to_check = set()

    # If we have a filename, add it to the set.

    if filename != '':
        files_to_check.add(filename)

    # If we have a dataset at this point, query files.

    if defname != '':

        files = []
        print('Checking dataset %s' % defname)
        try:
            files = samweb.listFiles('defname: %s' % defname)
        except:
            print('Dataset %s does not exist.' % defname)
            sys.exit(1)
        print('Dataset contains %d files.' % len(files))
        if len(files) == 0:
            print('Dataset is empty.')
            sys.exit(1)

        # Choose files

        random.shuffle(files)
        if ncheck > len(files):
            ncheck = len(files)
        for i in range(ncheck):
            print('Adding %s' % files[i])
            files_to_check.add(files[i])

    # Loop over files.

    for filename in files_to_check:

        # Check this file.

        nfile += 1
        ok = check_file(filename)
        if ok:
              nfileok += 1

    # Print statistics.

    print('\n%d files checked.' % nfile)
    print('%d files OK.' % nfileok)


    # Done.

    return 0


# Invoke main program.

if __name__ == "__main__":
    sys.exit(main(sys.argv))



