#!/usr/bin/env python

# Import stuff.

import sys, os

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

# This function opens an artroot file and loops over the RawDigit branch 
# of the Events TTree.  It counts the number of non-empty RawDigit entries
# and returns that number as its result.

def count_tpc_events(inputfile):

    # Initialize return value to empty list.

    result = 0

    # Check whether this file exists.
    if not os.path.exists(inputfile):
        return result
            
    # Root checks.

    file = ROOT.TFile.Open(inputfile)
    if file and file.IsOpen() and not file.IsZombie():

        # Root file opened successfully.

        events_tree = file.Get('Events')
        if events_tree and events_tree.InheritsFrom('TTree'):
            nevents = events_tree.GetEntriesFast()
            tfev = ROOT.TTreeFormula('events',
                                    'raw::RawDigits_digitcopy__Swizzler.present',
                                    events_tree)
            for entry in range(nevents):
                events_tree.GetEntry(entry)
                present = tfev.EvalInstance64()
                if present != 0:
                    result += 1

    else:

        # Root file could not be opened.

        result = 0

    return result

if __name__ == "__main__":
    tpc_events = count_tpc_events(str(sys.argv[1]))
    print tpc_events
    sys.exit(0)	
