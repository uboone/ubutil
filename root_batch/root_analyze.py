#! /usr/bin/env python
###############################################################################
#
# Name: RootAnalyze.py
# 
# Purpose: Base class for root analysis modules.
#
# Created: 11-Apr-2017
#
# Analysis modules should inherit from this base class and may override base
# class functions.  This class provides a default implementation for any function
# that the framework might call.  There is no function that analysis functions
# must override.
#
###############################################################################

from __future__ import absolute_import
from __future__ import print_function

class RootAnalyze:

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

        return ['*']

    def open_output(self, tfile):
        #----------------------------------------------------------------------
        #
        # Purpose: Called once by the framework at job initialization.
        #
        # Arguments: tfile - An open TFile object.
        #
        # Returns: None
        #
        # Analysis classes can add arbitrary content to the output file,
        # immediately or later.  It is legitimate for analysis classes to retain
        # a copy of the output file object so that content can be added later.
        #
        #----------------------------------------------------------------------

        return

    def event_info(self, tree):
        #----------------------------------------------------------------------
        #
        # Purpose: Called by the framework for each TTree entry.
        #
        # Arguments: tree - A loaded TTree object.
        #
        # Returns: A 3-tuple of integers (run, subrun, event).
        #
        # In case of missing or incomplete information, it is acceptable to return
        # a single None object, a tuple with fewer than 3 entries, or a tuple
        # containing None objects.
        #
        #----------------------------------------------------------------------

        return

    def analyze_tree(self, tree):
        #----------------------------------------------------------------------
        #
        # Purpose: Called by the framework each time a new TTree is read.  This
        #          function is provided for modules that do their own loop over
        #          tree entries.
        #
        # Arguments: tree - A loaded TTree object.
        #
        # Returns: None
        #
        #----------------------------------------------------------------------

        return

    def analyze_entry(self, tree):
        #----------------------------------------------------------------------
        #
        # Purpose: Called by the framework for each TTree entry.
        #
        # Arguments: tree - A loaded TTree object.
        #
        # Returns: None
        #
        #----------------------------------------------------------------------

        return

    def begin_job(self):
        #----------------------------------------------------------------------
        #
        # Purpose: Called by the framework at begin job time.
        #
        #----------------------------------------------------------------------

        return

    def end_job(self):
        #----------------------------------------------------------------------
        #
        # Purpose: Called by the framework at end job time.  In addition to 
        #          performing normal end-of-job tasks, this function gives modules
        #          the opportunity to contribute metadata to the output file.
        #
        # Returns: Sam metadata (python dictionary) or None.
        #
        #----------------------------------------------------------------------

        return

    def open_input(self, input_file):
        #----------------------------------------------------------------------
        #
        # Purpose: Called by the framework each time a new input file is opened.
        #
        # Arguments: input_file - An open TFile.
        #
        #----------------------------------------------------------------------

        return

    def close_input(self, input_file):
        #----------------------------------------------------------------------
        #
        # Purpose: Called by the framework just before an input file is closed.
        #
        # Arguments: input_file - An open TFile.
        #
        #----------------------------------------------------------------------

        return

    def begin_run(self, run):
        #----------------------------------------------------------------------
        #
        # Purpose: Called by the framework for each new run.
        #
        # Arguments: run - Run number.
        #
        #----------------------------------------------------------------------

        return

    def end_run(self, run):
        #----------------------------------------------------------------------
        #
        # Purpose: Called by the framework for ended run.
        #
        # Arguments: run - Run number.
        #
        #----------------------------------------------------------------------

        return

    def begin_subrun(self, run, subrun):
        #----------------------------------------------------------------------
        #
        # Purpose: Called by the framework for each new subrun.
        #
        # Arguments: run    - Run number.
        #            subrun - Subrun number.
        #
        #----------------------------------------------------------------------

        return

    def end_subrun(self, run, subrun):
        #----------------------------------------------------------------------
        #
        # Purpose: Called by the framework for ended subrun.
        #
        # Arguments: run    - Run number.
        #            subrun - Subrun number.
        #
        #----------------------------------------------------------------------

        return
