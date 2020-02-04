#! /usr/bin/env python
###############################################################################
#
# Name: cint_analyze.py
# 
# Purpose: Analysis module that acts as a front end to a cint macro.
#
# Created: 13-Apr-2017, H. Greenlee
#
###############################################################################
from __future__ import absolute_import
from __future__ import print_function
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
    # Returns: Instance of class EventInfo.
    #
    #----------------------------------------------------------------------

    obj = CintAnalyze(config)
    return obj

# Cint macro interface class.

class CintAnalyze(RootAnalyze):

    def __init__(self, pset):
        #----------------------------------------------------------------------
        #
        # Purpose: Constructor.
        #
        # Arguments: pset - FCL parameter set.
        #
        # The following fcl parameters are recognized.
        #
        # CintMacro    - The name of a cint (.C) macro.
        #                Use ".C" for interpreted cint.
        #                Use ".C+" for compiled cint.
        #
        # AnalyzeTree  - Name of c++ function in the cint macro that should be
        #                called to analyze an entire TTree or TChain.  This
        #                function should take a single argument of type TTree*.
        #                This function can do rooty things like setting branch
        #                addresses and statuses, and looping over tree entries.
        #
        # AnalyzeEntry - Name of c++ function in the cint macro that should be
        #                called to analyze one entry from a TTree or TChain.
        #
        # HistDir      - Make the specified diretory in the output file.
        #
        # LoadAllBranches - Activate all branches if true.  Otherwise don't
        #                   activate any branches (cint macro can still activate).
        #
        #----------------------------------------------------------------------

        mypset = pset['modules']['cint_analyze']
        self.cint_macro = mypset['CintMacro']

        self.analyze_tree_function = None
        if mypset.has_key('AnalyzeTree'):
            self.analyze_tree_function = mypset['AnalyzeTree']

        self.analyze_entry_function = None
        if mypset.has_key('AnalyzeEntry'):
            self.analyze_entry_function = mypset['AnalyzeEntry']

        self.hist_dir = None
        if mypset.has_key('HistDir'):
            self.hist_dir = mypset['HistDir']

        self.load_all_branches = False
        if mypset.has_key('LoadAllBranches'):
            self.load_all_branches = mypset['LoadAllBranches']

        # Load the macro.
        # If successful, the top level symbols in the cint macro will be added
        # to the ROOT module namespace.

        ok = ROOT.gROOT.LoadMacro(self.cint_macro)
        if ok == 0:
            print('Loaded cint macro %s' % self.cint_macro)
        else:
            print('Failed to load cint macro %s' % self.cint_macro)
            sys.exit(1)

        return


    def branches(self):
        #----------------------------------------------------------------------
        #
        # Purpose: Specify which branches should be loaded from this TTree.
        #          Called once by the framework at initialization.
        #
        # Returns: List or tuple of branch names that should be loaded.
        #
        # The returned list of branch names can include wildcards.  This 
        # base class provides a default implementation that returns ['*']
        # to load all branches.
        #
        #----------------------------------------------------------------------

        result = []
        if self.load_all_branches:
            result = ['*']
        return result


    def open_output(self, tfile):
        #----------------------------------------------------------------------
        #
        # Purpose: Called once by the framework at job initialization.
        #
        # Arguments: tfile - An open TFile object.
        #
        # Returns: None
        #
        #----------------------------------------------------------------------

        # Remember the top level output file TDirectory.

        if self.hist_dir == None:
            self.topdir = tfile
        else:
            self.topdir = tfile.mkdir(self.hist_dir)


    def analyze_tree(self, tree):
        #----------------------------------------------------------------------
        #
        # Purpose: Called by the framework each time a new TTree is read.  This
        #          function is provided for modules that do their own loop over
        #          tree entries.
        #
        # Arguments: tree - A TTree object.
        #
        # Returns: None
        #
        #----------------------------------------------------------------------

        if self.analyze_tree_function:

            # Find the tree function in the ROOT namespace.

            try:
                func = getattr(ROOT, self.analyze_tree_function)
            except:
                print('No callable function %s in module ROOT' % self.analyze_tree_function)
                sys.exit(1)

            self.topdir.cd()
            func(tree)


    def analyze_entry(self, tree):
        #----------------------------------------------------------------------
        #
        # Purpose: Called by the framework each time an entry is loaded in a 
        #          TTree.
        #
        # Arguments: tree - A loaded TTree object.
        #
        # Returns: None
        #
        #----------------------------------------------------------------------

        if self.analyze_entry_function:

            # Find the tree function in the ROOT namespace.

            try:
                func = getattr(ROOT, self.analyze_entry_function)
            except:
                print('No callable function %s in module ROOT' % self.analyze_entry_function)
                sys.exit(1)

            self.topdir.cd()
            func(tree)
