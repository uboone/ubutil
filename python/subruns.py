#!/usr/bin/env python
######################################################################
#
# Name: subruns.py
#
# Purpose: Extract (run, subrun) pairs from an artroot file or certain
#          root tuple files.  Output one (run, subrun) pair per line 
#          of output.
#
# Created: 13-Oct-2015  H. Greenlee
#
# Command line usage:
#
# subruns.py <artroot file>
#
######################################################################

# Import stuff.

import sys, os, project_utilities
import extractor_dict
import ifdh
import json

Ifdh = ifdh.ifdh()

# Import ROOT (hide command line arguments).

myargv = sys.argv
sys.argv = myargv[0:1]
sys.argv.append('-n')
# Prevent root from printing garbage on initialization.
if os.environ.has_key('TERM'):
    del os.environ['TERM']
import ROOT
ROOT.gErrorIgnoreLevel = ROOT.kError
sys.argv = myargv

# Filter warnings.

import warnings
warnings.filterwarnings('ignore', category = RuntimeWarning, message = 'creating converter.*')

# This function returns a list of (run, subrun) pairs for a given filename
# by accessing sam metadata in the sam database.

def get_file_subruns(filename):

    result = []

    md = Ifdh.getMetadata(filename)

    state=0
    for line in md.splitlines():
        words = line.split()
        if state == 0 and len(words) >= 2 and words[0] == 'Runs:':
            state = 1
            run_subrun = words[1].split('.')
            if len(run_subrun) >= 2:
                subrun_id = (int(run_subrun[0]), int(run_subrun[1]))
                if subrun_id not in result:
                    result.append(subrun_id)
        elif state == 1 and len(words) >= 1:
            if words[0].find(':') < 0:
                run_subrun = words[0].split('.')
                if len(run_subrun) >= 2:
                    subrun_id = (int(run_subrun[0]), int(run_subrun[1]))
                    if subrun_id not in result:
                        result.append(subrun_id)
            else:
                state = 2

    return result


# This function opens an artroot file and extracts the list of runs and subruns
# from the SubRuns TTree.
# A list of (run, subrun) pairs is returned as a list of 2-tuples.

def get_subruns(inputfile):

    # Initialize return value to empty list.

    result = []

    # Check whether this file exists.
    if not os.path.exists(inputfile):
        return result

    # Root checks.

    file = project_utilities.SafeTFile(inputfile)
    if file and file.IsOpen() and not file.IsZombie():

        # Root file opened successfully.
        # Check whether this file has an sqlite database, and therefore
        # may have internal sam metadata.

        db = file.Get('RootFileDB')
        if db and db.InheritsFrom('TKey'):

            # Extract internal sam metadata.

            md = extractor_dict.getmetadata(inputfile)
            if type(md) == type({}) and md.has_key('parents'):

                # Extract run and subrun information from parent files.

                for parent in md['parents']:
                    parent_name = parent['file_name']
                    subruns = get_file_subruns(str(parent_name))
                    for subrun in subruns:
                        if subrun not in result:
                            result.append(subrun)

        else:

            # This file is not an artroot file.
            # Try to extract information from corresponding json file.

            json_filename = inputfile + '.json'
            if os.path.exists(json_filename):
                json_file = open(json_filename)
                if json_file:
                    md = json.load(json_file)
                    if type(md) == type({}) and md.has_key('parents'):

                        # Extract run and subrun information from parent files.

                        for parent in md['parents']:
                            parent_name = parent['file_name']
                            subruns = get_file_subruns(str(parent_name))
                            for subrun in subruns:
                                if subrun not in result:
                                    result.append(subrun)

    else:

        # Root file could not be opened.

        result = []

    # Sort in order of increasing run, then increasing subrun.

    result.sort()

    # Done.

    return result

if __name__ == "__main__":
    run_subruns = get_subruns(str(sys.argv[1]))
    for run_subrun in run_subruns:
        print run_subrun[0], run_subrun[1]
    sys.exit(0)	
