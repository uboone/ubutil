#! /usr/bin/env python
###############################################################################
#
# Name: art_event_info.py
# 
# Purpose: Extract (run, subrun, event) information for artroot Events tree.
#
# Created: 11-Apr-2017, H. Greenlee
#
###############################################################################
import sys, os
from root_analyze import RootAnalyze

# Prevent root from printing garbage on initialization.
if os.environ.has_key('TERM'):
    del os.environ['TERM']

# Hide command line arguments from ROOT module.
myargv = sys.argv
sys.argv = myargv[0:1]

import ROOT
#ROOT.gErrorIgnoreLevel = ROOT.kError
sys.argv = myargv

def make(config):
    #----------------------------------------------------------------------
    #
    # Purpose: Factory function.
    #
    # Arguments: config - FCL configuration.
    #
    # Returns: Instance of class ArtEventInfo.
    #
    #----------------------------------------------------------------------

    obj = ArtEventInfo()
    return obj

# Event information class.

class ArtEventInfo(RootAnalyze):

    def __init__(self):
        #----------------------------------------------------------------------
        #
        # Purpose: Constructor.
        #
        #----------------------------------------------------------------------

        return


    def branches(self):
        #----------------------------------------------------------------------
        #
        # Purpose: Return list of branches we want read for this tree, namely,
        #          run, subrun, event.
        #
        # Returns: List of branches.
        #
        #----------------------------------------------------------------------

        return ['EventAuxiliary']


    def event_info(self, tree):
        #----------------------------------------------------------------------
        #
        # Purpose: Extract run, subrun, event from loaded tree entry.
        #          Called by framework.
        #
        # Arguments: tree - Loaded TTree object.
        #
        # Returns: 3-tuple (run, subrun, event).
        #
        #----------------------------------------------------------------------

        # Run number.

        tfr =  ROOT.TTreeFormula('runs', 'EventAuxiliary.id_.subRun_.run_.run_', tree)
        run = tfr.EvalInstance64()

        # Subrun number.

        tfs =  ROOT.TTreeFormula('subruns', 'EventAuxiliary.id_.subRun_.subRun_', tree)
        subrun = tfs.EvalInstance64()

        # Event number.

        tfe =  ROOT.TTreeFormula('events', 'EventAuxiliary.id_.event_', tree)
        event = tfe.EvalInstance64()

        # Done.

        return run, subrun, event
