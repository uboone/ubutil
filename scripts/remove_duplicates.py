#! /usr/bin/env python
######################################################################
#
# Name: remove_duplicates.py
#
# Purpose: Remove duplicate files in a definition, in the sense of
#          multiple files having the same immediate parent.
#
# Created: 2-Apr-2018  Herbert Greenlee
#
# Usage:
#
# remove_duplicates.py <options>
#
# Options:
#
# --def <dataset-definition> - Specify dataset definition.
# -n|--dryrun                - Just print duplicates, but do not remove them.
# -q|--quiet                 - Be somewhat quiet.
# --virtual                  - Check virtual parents of dataset definition
#                              (relevant for merged datasets).
#
######################################################################

import sys, os
import project_utilities

# Global variables.

samweb = project_utilities.samweb()

# Options.

defname = ''
dryrun = False
quiet = False
virtual = False
ignore_crt = False

# Statistics.

nchild = 0
nparent = 0
ndup = 0
norphan = 0
nremove = 0

# Parents.

all_parents = {}

# Print help.

def help():

    filename = sys.argv[0]
    file = open(filename, 'r')

    doprint=0
    
    for line in file.readlines():
        if line[2:22] == 'remove_duplicates.py':
            doprint = 1
        elif line[0:6] == '######' and doprint:
            doprint = 0
        if doprint:
            if len(line) > 2:
                print line[2:],
            else:
                print


# Recursively declare file and any descendants as bad.

def declare_bad(filename):

    global samweb

    print 'Declare bad: %s' % filename

    # Find descendants of filename and declare them bad as well.

    children = samweb.listFiles(
        dimensions='ischildof: (file_name \'%s\' and availability: anylocation) and availability: anylocation' % filename)

    for child in children:
        declare_bad(child)

    # Now declare the original file as bad.

    samweb.modifyFileMetadata(filename, md={"content_status": "bad"})

    # Done

    return

# Given two potential duplicate files, check run and subrun information
# Return true of files are not really duplicate-processed (i.e. if run/subruns
# are disjoint between the two files.

def check_runs(f1, f2):

    result = False

    md1 = samweb.getMetadata(f1)
    runs1 = set()
    for run in md1['runs']:
        rs = 1000000 * run[0] + run[1]
        runs1.add(rs)

    md2 = samweb.getMetadata(f2)
    runs2 = set()
    for run in md2['runs']:
        rs = 1000000 * run[0] + run[1]
        runs2.add(rs)

    # Find intersection of runs/subruns between the two files.

    runs3 = runs1 & runs2

    if len(runs3) == 0:
        result = True

    # Done.

    return result


# Given two files with duplicate parents, decide which file is good,
# and which file is bad.
# Return 2-tuple (good_file, bad_file)

def decide(f1, f2):

    locs1 = samweb.locateFile(f1)
    locs2 = samweb.locateFile(f2)

    # If one file is virtual and one is physical, keep the physical file.

    if len(locs1) > 0 and len(locs2) == 0:
        return f1, f2

    elif len(locs1) == 0 and len(locs2) > 0:
        return f2, f1

    # Below handle cases where both files are either physical or virtual.

    elif len(locs1) > 0 and len(locs2) > 0:

        # Both files are physical.
        # Find physical parents of both files.

        parents1 = []
        parents2 = []

        for f in (f1, f2):
            dim = 'isparentof:( file_name \'%s\')' % f
            parents = samweb.listFiles(dim)
            if f == f1:
                parents1.extend(parents)
            else:
                parents2.extend(parents)

        # Keep the file with more physical parents.

        if len(parents1) > len(parents2):
            return f1, f2
        else:
            return f2, f1

    else:

        # Both files are virtual.
        # Find physical siblings of both files.

        sibs1 = []
        sibs2 = []

        for f in (f1, f2):
            dim = 'ischildof:( file_name \'%s\')' % f
            children = samweb.listFiles(dim)
            for child in children:
                dim = 'isparentof:( file_name \'%s\')' % child
                sibs = samweb.listFiles(dim)
                if f == f1:
                    sibs1.extend(sibs)
                else:
                    sibs2.extend(sibs)

        # Keep the file with more physical siblings.
        # In particular, a virtual file with zero physical siblings can not be good.

        if len(sibs1) > len(sibs2):
            return f1, f2
        else:
            return f2, f1


# Check metadata of a single file.

def check_metadata(md):

    global quiet
    global ignore_crt

    global nchild
    global nparent
    global ndup
    global norphan
    global nremove

    global all_parents

    nchild += 1
    f = md['file_name']
    if not quiet:
        print 'Checking file %s' % f

    # Ignore mergable files.

    orphan = True
    if 'parents' in md:
        for parent in md['parents']:
            parent_name = parent['file_name']

            # Ignore CRT parents.

            if not ignore_crt or not parent_name.startswith('CRT'):
                orphan = False
                if not quiet:
                    print 'Found parent %s' % parent_name
                if parent_name in all_parents.keys():
                    f2 = all_parents[parent_name]
                    ok = check_runs(f, f2)
                    if not ok:
                        print 'Duplicate parent %s.' % parent_name
                        print '  Child: %s' % f
                        print '  Previous child: %s' % f2
                        good_file, bad_file = decide(f, f2)
                        print 'Good file: %s' % good_file
                        print 'Bad file: %s' % bad_file
                        ndup += 1
                        if not dryrun:
                            declare_bad(bad_file)
                            all_parents[parent_name] = good_file
                        nremove += 1

                        # If we declared this file bad, break out of loop over parents.
                        # Otherwise (if we declared the other file bad), keep checking the
                        # rest of the parents.

                        if f == bad_file:
                            break
                else:
                    if not quiet:
                        print 'OK.'
                    all_parents[parent_name] = f
                    nparent += 1

    if orphan:
        print 'Orphan: %s' % f
        norphan += 1
        if not dryrun:
            declare_bad(f)
        nremove += 1

    # Done.

    return

# Check metadata of file list.

def check_file_list(files):

    mds = samweb.getMultipleMetadata(files)
    for md in mds:
        check_metadata(md)

    # Done.

    return

# Main program starts here.
# Parse arguments.

args = sys.argv[1:]

if len(args) == 0:
    help()
    sys.exit(0)

while len(args) > 0:
    if args[0] == '-h' or args[0] == '--help':
        help()
        sys.exit(0)
    elif args[0] == '-n' or args[0] == '--dryrun':
        dryrun = True
        del args[0]
    elif args[0] == '-q' or args[0] == '--quiet':
        quiet = True
        del args[0]
    elif args[0] == '--virtual':
        virtual = True
        del args[0]
    elif args[0] == '--def' and len(args) > 1:
        defname = args[1]
        del args[0:2]
    else:
        print 'Unknown option %s' % args[0]
        sys.exit(1)

if defname == '':
    print 'No dataset definition supplied.'
    help()
    sys.exit(1)

print 'Checking definition %s' % defname

# Decide if we should ignore CRT parents.

ignore_crt = not defname.startswith('crt')
if ignore_crt:
    print 'Ignoring duplicate CRT parents.'

# Query all files in this dataset definition.

if virtual:
    dim = 'isparentof:( defname: %s minus merge.merge 1 with availability physical ) with availability virtual' % defname
    files = samweb.listFiles(dimensions=dim)
else:
    dim = 'defname: %s minus (merge.merge 1 and merge.merged 0)' % defname
    files = samweb.listFiles(dimensions=dim)

file_queue = []

for f in files:
    file_queue.append(f)
    if len(file_queue) > 100:
        check_file_list(file_queue)
        file_queue = []

if len(file_queue) > 0:
    check_file_list(file_queue)
        

# Print summary.

print '%d files in dataset definition.' % nchild
print '%d parent files.' % nparent
print '%d duplicates.' % ndup
print '%d orphans.' % norphan
print '%d files removed.' % nremove
        
