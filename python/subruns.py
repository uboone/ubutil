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
        # Get runs and subruns fro SubRuns tree.

        subrun_tree = file.Get('SubRuns')
        if subrun_tree and subrun_tree.InheritsFrom('TTree'):
            nsubruns = subrun_tree.GetEntriesFast()
            tfr = ROOT.TTreeFormula('runs',
                                    'SubRunAuxiliary.id_.run_.run_',
                                    subrun_tree)
            tfs = ROOT.TTreeFormula('subruns',
                                    'SubRunAuxiliary.id_.subRun_',
                                    subrun_tree)
            for entry in range(nsubruns):
                subrun_tree.GetEntry(entry)
                run = tfr.EvalInstance64()
                subrun = tfs.EvalInstance64()
                run_subrun = (run, subrun)
                result.append(run_subrun)

        # If previous section didn't find anything, try extracting 
        # from beam data trees.

        if len(result) == 0:
            tdir = file.Get('beamdata')
            if tdir and tdir.InheritsFrom('TDirectory'):

                # Look for bnb tree.

                bnb_tree = tdir.Get('bnb')
                if bnb_tree and bnb_tree.InheritsFrom('TTree'):
                    nsubruns = bnb_tree.GetEntriesFast()
                    tfr = ROOT.TTreeFormula('runs', 'run', bnb_tree)
                    tfs = ROOT.TTreeFormula('subruns', 'subrun', bnb_tree)
                    for entry in range(nsubruns):
                        bnb_tree.GetEntry(entry)
                        run = tfr.EvalInstance64()
                        subrun = tfs.EvalInstance64()
                        run_subrun = (run, subrun)
                        if run_subrun not in result:
                            result.append(run_subrun)

                # Look for numi tree.

                numi_tree = tdir.Get('numi')
                if numi_tree and numi_tree.InheritsFrom('TTree'):
                    nsubruns = numi_tree.GetEntriesFast()
                    tfr = ROOT.TTreeFormula('runs', 'run', numi_tree)
                    tfs = ROOT.TTreeFormula('subruns', 'subrun', numi_tree)
                    for entry in range(nsubruns):
                        numi_tree.GetEntry(entry)
                        run = tfr.EvalInstance64()
                        subrun = tfs.EvalInstance64()
                        run_subrun = (run, subrun)
                        if run_subrun not in result:
                            result.append(run_subrun)

        # If previous section didn't find anything, try extracting 
        # from specalib trees.

        if len(result) == 0:
            tdir = file.Get('specalib')
            if tdir and tdir.InheritsFrom('TDirectory'):

                # Look for eventtree.

                event_tree = tdir.Get('eventtree')
                if event_tree and event_tree.InheritsFrom('TTree'):
                    nsubruns = event_tree.GetEntriesFast()
                    tfr = ROOT.TTreeFormula('runs', 'run', event_tree)
                    tfs = ROOT.TTreeFormula('subruns', 'subrun', event_tree)
                    for entry in range(nsubruns):
                        event_tree.GetEntry(entry)
                        run = tfr.EvalInstance64()
                        subrun = tfs.EvalInstance64()
                        run_subrun = (run, subrun)
                        if run_subrun not in result:
                            result.append(run_subrun)

        # If previous section didn't find anything, try extracting 
        # from analysis tree trees.

        if len(result) == 0:
            tdir = file.Get('analysistree')
            if tdir and tdir.InheritsFrom('TDirectory'):

                # Look for eventtree.

                event_tree = tdir.Get('anatree')
                if event_tree and event_tree.InheritsFrom('TTree'):
                    nsubruns = event_tree.GetEntriesFast()
                    tfr = ROOT.TTreeFormula('runs', 'run', event_tree)
                    tfs = ROOT.TTreeFormula('subruns', 'subrun', event_tree)
                    for entry in range(nsubruns):
                        event_tree.GetEntry(entry)
                        run = tfr.EvalInstance64()
                        subrun = tfs.EvalInstance64()
                        run_subrun = (run, subrun)
                        if run_subrun not in result:
                            result.append(run_subrun)

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
