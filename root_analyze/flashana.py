#! /usr/bin/env python
###############################################################################
#
# Name: flash.py
# 
# Purpose: Book and fill flash analysis tree histograms.
#
# Created: 2-Jun-2017, H. Greenlee
#
###############################################################################
from __future__ import absolute_import
from __future__ import print_function
import sys, os
from root_analyze import RootAnalyze

# Prevent root from printing garbage on initialization.
if 'TERM' in os.environ:
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
    # Returns: Instance of class AnalyzeFlashes.
    #
    #----------------------------------------------------------------------

    obj = AnalyzeFlashes(config)
    return obj

# Analyze flash class

class AnalyzeFlashes(RootAnalyze):

    def __init__(self, pset):
        #----------------------------------------------------------------------
        #
        # Purpose: Constructor.
        #
        #----------------------------------------------------------------------

        mypset = pset['modules']['flashana']
        self.algonames = mypset['algorithn_names']

        return


    def branches(self):
        #----------------------------------------------------------------------
        #
        # Purpose: Return list of branches we want read for this tree.
        #
        # Returns: List of flash-related branches.
        #
        #----------------------------------------------------------------------

        return ['nfls_*', 'fls*']


    def open_output(self, output_file):
        #----------------------------------------------------------------------
        #
        # Purpose: Add content to output file.  Add flash-related histograms.
        #          Called by framework.
        #
        # Arguments: output_file - Open TFile.
        #
        #----------------------------------------------------------------------

        # Make output directory.

        dir = output_file.mkdir('flash')
        dir.cd()
        self.hnfls = {}
        self.hflsTime = {}
        self.hflsTimeBeam = {}
        self.hflsPe = {}
        self.hflsYcenter = {}
        self.hflsZcenter = {}
        self.hflsYwidth = {}
        self.hflsZwidth = {}
        for algoname in self.algonames:
            subdir = dir.mkdir(algoname)
            subdir.cd()

            # Book histograms.

            self.hnfls[algoname] = ROOT.TH1F('hnfls_%s' % algoname,
                                             'Number of flashes for %s' % algoname,
                                             100, 0., 100.)
            self.hflsTime[algoname] = ROOT.TH1F('hflsTime_%s' % algoname,
                                                'Flash time for %s' % algoname,
                                                100, -3000., 5000.)
            self.hflsTimeBeam[algoname] = ROOT.TH1F('hflsTimeBeam_%s' % algoname,
                                                    'Flash time for %s' % algoname,
                                                    50, 0., 20.)

        # Done.

        return


    def getLeaf(self, tree, branch_name):
        #----------------------------------------------------------------------
        #
        # Purpose: Utility function to return leaf information for a particular
        #          branch.
        #
        # Arguments: branch name.
        #
        # Returns: Leaf (TLeaf).
        #
        # This function assumes one leaf/branch (true in case of analysis tree).
        # The returned value is an instance of class TLeaf.  To get numeric 
        # values, call TLeaf function GetValue(i), where i=array index or 0 for 
        # scalar leaf.
        #
        #----------------------------------------------------------------------

        result = None
        br = tree.GetBranch(branch_name)
        leaves = br.GetListOfLeaves()
        if len(leaves) > 0:
            result = leaves[0]
        return result


    def analyze_entry(self, tree):
        #----------------------------------------------------------------------
        #
        # Purpose: Analyze loaded tree (fill histograms).  Called by framework.
        #
        # Arguments: tree - Loaded tree.
        #
        #----------------------------------------------------------------------

        for algoname in self.algonames:

            # Get leaves.

            nfls = self.getLeaf(tree, 'nfls_%s' % algoname)
            flsTime = self.getLeaf(tree, 'flsTime_%s' % algoname)

            # Fill histograms.

            self.hnfls[algoname].Fill(nfls.GetValue())
            self.hflsTime[algoname].Fill(flsTime.GetValue())
            self.hflsTimeBeam[algoname].Fill(flsTime.GetValue())
