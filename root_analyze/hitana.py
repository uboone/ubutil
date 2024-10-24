#! /usr/bin/env python
###############################################################################
#
# Name: hitana.py
# 
# Purpose: Book and fill hit analysis tree histograms.
#
# Created: 28-Mar-2017, H. Greenlee
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
    # Returns: Instance of class AnalyzeHits.
    #
    #----------------------------------------------------------------------

    obj = AnalyzeHits()
    return obj

# Analyze hit class

class AnalyzeHits(RootAnalyze):

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
        # Purpose: Return list of branches we want read for this tree.
        #
        # Returns: List of hit-related branches.
        #
        #----------------------------------------------------------------------

        return ['no_hits', 'hit_*']


    def open_output(self, output_file):
        #----------------------------------------------------------------------
        #
        # Purpose: Add content to output file.  Add hit-related histograms.
        #          Called by framework.
        #
        # Arguments: output_file - Open TFile.
        #
        #----------------------------------------------------------------------

        # Make output directory.

        dir = output_file.mkdir('hit')
        dir.cd()

        # Book histograms.

        self.hno_hits = ROOT.TH1F('hno_hits', 'Number of hits', 100, 0., 50000.)
        self.hhit_plane = ROOT.TH1F('hhit_plane', 'Plane number', 3, -0.5, 2.5)
        self.hhit_wire = ROOT.TH1F('hhit_wire', 'Wire number', 100, 0., 6000.)
        self.hhit_channel = ROOT.TH1F('hhit_channel', 'Channel number', 100, 0., 10000.)
        self.hhit_peakT = ROOT.TH1F('hhit_peakT', 'Hit peak time (tick)', 100, 0., 10000.)

        self.hhit_charge = []
        self.hhit_ph = []
        self.hhit_nelec = []
        self.hhit_charge_nelec = []
        self.hhit_ph_nelec = []
        self.hchargeperelec = []
        self.hphperelec = []
        for p in range(3):
            self.hhit_charge.append(ROOT.TH1F('hhit_charge%d' % p, 
                                              'Plane %d, Hit area (ADC)' % p,
                                              100, 0., 1500.))
            self.hhit_ph.append(ROOT.TH1F('hhit_ph%d' % p,
                                          'Plane %d, Hit pulse height (ADC)' % p,
                                          100, 0., 200.))
            self.hhit_nelec.append(ROOT.TH1F('hhit_nelec%d' % p,
                                             'Plane %d, Hit number of electrons',
                                             100, 0., 1.e5))
            self.hhit_charge_nelec.append(ROOT.TH2F('hhit_charge_nelec%d' % p,
                                                    'Plane %d, Hit area (ADC) vs. Number of electrons' % p,
                                                    1000, 0., 1.e5, 1000, 0., 1000.))
            self.hhit_ph_nelec.append(ROOT.TH2F('hhit_ph_nelec%d' % p,
                                                'Plane %d, Hit pulseheight (ADC) vs. Number of electrons' % p,
                                                1000, 0., 1.e5, 1000, 0., 100.))
            self.hchargeperelec.append(ROOT.TH1F('hchargeperelec%d' % p,
                                                 'Plane %d, ADC (area) per electron' % p,
                                                 1000, 0., 0.02))
            self.hphperelec.append(ROOT.TH1F('hphperelec%d' % p,
                                             'Plane %d, ADC (pulse height) per electron' % p,
                                             1000, 0., 0.003))

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

        # Get leaves.

        no_hits = self.getLeaf(tree, 'no_hits')
        hit_plane = self.getLeaf(tree, 'hit_plane')
        hit_wire = self.getLeaf(tree, 'hit_wire')
        hit_channel = self.getLeaf(tree, 'hit_channel')
        hit_peakT = self.getLeaf(tree, 'hit_peakT')
        hit_charge = self.getLeaf(tree, 'hit_charge')
        hit_ph = self.getLeaf(tree, 'hit_ph')
        hit_nelec = self.getLeaf(tree, 'hit_nelec')

        # Fill histograms.

        self.hno_hits.Fill(no_hits.GetValue())

        for i in range(hit_plane.GetLen()):

            plane = int(hit_plane.GetValue(i))
            wire = hit_wire.GetValue(i)
            channel = hit_channel.GetValue(i)
            peakT = hit_peakT.GetValue(i)
            charge = hit_charge.GetValue(i)
            ph = hit_ph.GetValue(i)
            nelec = hit_nelec.GetValue(i)

            self.hhit_plane.Fill(plane)
            self.hhit_wire.Fill(wire)
            self.hhit_channel.Fill(channel)
            self.hhit_peakT.Fill(peakT)
            self.hhit_charge[plane].Fill(charge)
            self.hhit_ph[plane].Fill(ph)
            self.hhit_nelec[plane].Fill(nelec)
            self.hhit_charge_nelec[plane].Fill(nelec, charge)
            self.hhit_ph_nelec[plane].Fill(nelec, ph)
            if nelec > 0:
                self.hphperelec[plane].Fill(ph/nelec)
