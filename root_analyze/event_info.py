#! /usr/bin/env python
###############################################################################
#
# Name: event_info.py
# 
# Purpose: Extract (run, subrun, event) information for analysis trees.
#
# Created: 11-Apr-2017, H. Greenlee
#
###############################################################################
import sys, os
from root_analyze import RootAnalyze

def make(config):
    #----------------------------------------------------------------------
    #
    # Purpose: Factory function.
    #
    # Arguments: config - FCL configuration.
    #
    # Returns: Instance of class EventInfo.
    #
    #----------------------------------------------------------------------

    obj = EventInfo()
    return obj

# Event information class.

class EventInfo(RootAnalyze):

    def __init__(self):
        #----------------------------------------------------------------------
        #
        # Purpose: Constructor.
        #
        #----------------------------------------------------------------------

        return


    def branches(self, tree):
        #----------------------------------------------------------------------
        #
        # Purpose: Return list of branches we want read for this tree, namely,
        #          run, subrun, event.
        #
        # Arguments: tree - TTree object (ignored).
        #
        # Returns: List of branches.
        #
        #----------------------------------------------------------------------

        return ['run', 'subrun', 'event']


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

        run = None
        br = tree.GetBranch('run')
        leaves = br.GetListOfLeaves()
        if len(leaves) > 0:
            run = int(leaves[0].GetValue(0))

        # Subrun number.

        subrun = None
        br = tree.GetBranch('subrun')
        leaves = br.GetListOfLeaves()
        if len(leaves) > 0:
            subrun = int(leaves[0].GetValue(0))

        # Event number.

        event = None
        br = tree.GetBranch('event')
        leaves = br.GetListOfLeaves()
        if len(leaves) > 0:
            event = int(leaves[0].GetValue(0))

        # Done.

        return run, subrun, event
