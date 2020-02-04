#! /usr/bin/env python
###############################################################################
#
# Name: lar.py
# 
# Purpose: Ntuple reading framework script.
#
# Created: 16-Mar-2017
#
# Usage:
#
# lar.py [options]
#
# Options:
#
# -h|--help               - Print help message.
# -c|--config <fcl>       - Configuration.
# -s|--source <input>     - Input (single file).
# -S|--source-list <list> - Input (file list).
# --sam-web-uri <uri>     - SAM project uri (input project).
# --sam-process-id <pid>  - SAM process ID (input project).
# -o|--output <output>    - Specify output.
# -T|--TFileName <output> - Specify output (synonymous with --output).
# -n|--nevts <nev>        - Number of events to process.
# --nskip                 - Number of events to skip.
# --rethrow-default       - Ignored (for compatibility).
#
# Usage:
#
# This script is designed as a drop-in replacement for the art executable
# (art or lar) in the sense that it supports many of the same command line
# options as the standard art executable.
#
# This script also resembles the art executable in that it requires a fcl
# configuration file, and its actions are in part controlled by this fcl file.
# The expected format of the file file is given below.
#
# This script opens a sequence root files and imports and calls a sequence
# of analysis modules.  It is designed specfically to work with analysis
# tree ntuples, but should work with other kinds of root ntuples or TTrees.
#
# This script performs the following functions:
#
# 1.  Opening and closing input root files (file loop), possibly from sam.
# 2.  Opening and closing one single output root file.
# 3.  Reading the input TTree.
# 4.  Setting input TTree branch statuses (load only selected branches).
# 5.  Looping over and loading entries of input ntuples (event loop).
# 6.  Calling analysis module function hooks at appropriate times.
# 7.  Generating sam metadata for the output file.
#
# Reading input from sam
#-----------------------
#
# The sam project and consumer process should be started externally to this script.
# The project url and process id should be specified as command line arguments using
# options --sam-web-uri and --sam-process-id.
#
# Analysis modules
#-----------------
#
# Each analysis module should define a factory function:
#
# make(config)
#
# The factory function should return an instance of an analysis class defined
# in the module.  The single argument of the factory function is a pythonized
# version of the fcl configuration object (i.e. a python dictionary).
#
# Analysis classes
#-----------------
#
# The analysis class should inherit from base class RootAnalyze.  Refer to the 
# source file (root_analyze.py) for a detailed description of class functions that
# analysis classes can overload.  Analysis classes are not required to overload
# any base class functions.  Most analysis classes will want to overload 
# function "analyze," which is called for each ntuple entry (event).
#
# Fcl file format
#----------------
#
# process_name : "myprocess"         # Required by work flow.
# input_tree : "anatree"             # Name of input TTree (name or path).
# modules : { module1 : config1
#             module2 : config2 }
#
###############################################################################
from __future__ import absolute_import
from __future__ import print_function
import sys, os, imp, fcl, json, datetime

# Prevent root from printing garbage on initialization.
if 'TERM' in os.environ:
    del os.environ['TERM']

# Hide command line arguments from ROOT module.
myargv = sys.argv
sys.argv = myargv[0:1]

import ROOT
#ROOT.gErrorIgnoreLevel = ROOT.kError
sys.argv = myargv

# Global ifdh object.

Ifdh = None

# Transferred files.

transferred_files = set()


def help():
    #----------------------------------------------------------------------
    #
    # Purpose: Print help.
    #
    #----------------------------------------------------------------------
    filename = sys.argv[0]
    file = open(filename, 'r')

    doprint=0
    
    for line in file.readlines():
        if line[2:8] == 'lar.py':
            doprint = 1
        elif line[0:6] == '######' and doprint:
            doprint = 0
        if doprint:
            if len(line) > 2:
                print(line[2:], end=' ')
            else:
                print()


def sam_iter(prjurl, pid, cleanup=True):
    #----------------------------------------------------------------------
    #
    # Purpose: A sam generator.
    #
    # Arguments: prjurl  - Project url.
    #            pid     - Process id.
    #            cleanup - If true, delete local copies each time a file 
    #                      is marked "consumed."
    #
    # Returns: A sam iterator.
    #
    # This function is a python generator (meaning it contains "yield" 
    # statements).  When called, it returns an iterator that acts like a
    # list of files for files obtained from sam.
    #
    # Example:
    #
    # files = sam_iter(prjurl, pid)
    # for file in files:
    # ...
    #
    #----------------------------------------------------------------------

    global Ifdh, transferred_files

    # Initialize ifdh object, if not already done.

    if Ifdh == None:
        import ifdh
        Ifdh = ifdh.ifdh()

    # File loop.

    current_file = None
    while True:

        # Release most recent file, if any.

        if current_file:
            sam_clean(prjurl, pid, cleanup=cleanup)

        # Get next file.

        url = Ifdh.getNextFile(prjurl, pid)
        if url:

            print('Delivered file = %s' % url)

            # Fetch the input file.

            ok = False
            try:
                current_file = Ifdh.fetchInput(url)
                ok = True
            except:
                ok = False

            # If transfer failed.  Update file status to "skipped."

            if not ok:
                print('Skipped file = %s' % url)
                Ifdh.updateFileStatus(prjurl, pid, os.path.basename(url), 'skipped')
                continue

            # Transfer succeeded.  Update file status to "transferred."

            print('Transferred file = %s' % current_file)
            Ifdh.updateFileStatus(prjurl, pid, os.path.basename(current_file), 'transferred')
            transferred_files.add(os.path.basename(current_file))

            # Return the next file.

            yield current_file

        else:

            # Stop iteration.

            return


def sam_clean(prjurl, pid, cleanup=True):
    #----------------------------------------------------------------------
    #
    # Purpose: Clean up transferred files.  Update status of transferred
    #          files to "consumed", and call "ifdh cleanup" to delete local
    #          copies of transferred files.
    #
    # Arguments: prjurl  - Project url.
    #            pid     - Process id.
    #            cleanup - Delete temp files by calling "ifdh cleanup."
    #
    #----------------------------------------------------------------------

    global Ifdh, transferred_files

    # Update file statuses of transferred files to consumed.

    while len(transferred_files) > 0:
        transferred_file = transferred_files.pop()
        print('Consumed file = %s' % transferred_file)
        Ifdh.updateFileStatus(prjurl, pid, transferred_file, 'consumed')

    # Delete local copies.

    if cleanup:
        print('Clean up local copies of transferred files.')
        Ifdh.cleanup()

    # Done.

    return  


# Framework class

class Framework:

    def __init__(self,
                 pset,
                 input_file_names,
                 output_file_name,
                 nev,
                 nskip) :
        #----------------------------------------------------------------------
        #
        # Purpose: Constructor.
        #
        # Arguments: pset             - Pythonized fcl configuration (dictionary).
        #            input_file_names - Input file name iterator.
        #            output_file_name - Output file.
        #            nev              - Maximum number of events to process.
        #            nskip            - Number of events to stip.
        #
        # The input_file_names argument can be any of the following.
        #
        # 1.  A python list of file names.
        # 2.  An open file object for a file list.
        # 3.  A a sam iterator (as returned by generator "sam_iter").
        #
        #----------------------------------------------------------------------

        # Remember arguments.

        self.pset = pset
        self.input_file_names = input_file_names
        self.output_file_name = output_file_name
        self.nev = nev
        self.nskip = nskip

        # FCL parameters.

        self.tree_names = []
        if 'input_tree' in pset:
            tree_name = pset['input_tree']              # Input tree name(s).
            if type(tree_name) == type([]):
                self.tree_names = tree_name
            else:
                self.tree_names.append(tree_name)
        self.loop_over_entries = pset['loop_over_entries']   # Entry loop flag.
        self.module_names = pset['modules']                  # Analysis modules.
        self.chain = pset['chain']                           # Combine TTrees into one TChain?
        self.dump_every = pset['dump_every']                 # Generate output every N entries.

        # Other class data members.

        self.output_file = None               # Output TFile object.
        self.analyzers = []                   # Analyzer objects.
        self.branch_names = []                # Branch names to load.
        self.input_file = None                # Currently open input TFile object.
        self.trees = []                       # Current input TTrees.
        self.runnum = None                    # Current run number.
        self.subrunnum = None                 # Current subrun number.
        self.evnum = None                     # Current event number.
        self.done = False                     # Finished flag.

        # Statistics and metadata.

        self.metadata = {}           # Sam metadata dictionary.
        self.first_event = None      # First event number.
        self.last_event = None       # Last event number.
        self.event_count = 0         # Number of events.
        self.run_type = 'unknown'    # Run type.
        self.parents = []            # Parents.

        # Open output file.

        print('Opening output file %s' % output_file_name)
        self.output_file = ROOT.TFile.Open(output_file_name, 'RECREATE')
        if not self.output_file or not self.output_file.IsOpen():
            print('Unable to open output file.')
            sys.exit(1)
        print('Open successful.')

        # Import analysis modules and make analyzer objects.

        for module_name in self.module_names:
            print('Importing module %s' % module_name)
            sys.path.append('.')          # Make sure local directory is on import path.
            fp, pathname, description = imp.find_module(module_name)
            module = imp.load_module(module_name, fp, pathname, description)
            print('Making analyzer object.')
            analyzer = module.make(self.pset)
            self.analyzers.append(analyzer)

        # Call the open output function of each analyzer.
        # Save list of branches to load.

        for analyzer in self.analyzers:
            analyzer.open_output(self.output_file)
            for branch_name in analyzer.branches():
                print('Read branch %s' % branch_name)
                self.branch_names.append(branch_name)


        # Update metadata.

        self.metadata['start_time'] = datetime.datetime.utcnow().replace(microsecond=0).isoformat()

        # Extract experiment-independent metadata from FileCatalogMetadata configuration.

        app = {}

        if 'process_name' in self.pset:
            app['name'] = self.pset['process_name']

        if 'services' in self.pset:
            services = self.pset['services']
            if 'FileCatalogMetadata' in services:
                fcm = services['FileCatalogMetadata']
                if 'applicationFamily' in fcm:
                    app['family'] = fcm['applicationFamily']
                if 'applicationFamily' in fcm:
                    app['version'] = fcm['applicationVersion']
                if 'group' in fcm:
                    self.metadata['group'] = fcm['group']
                if 'fileType' in fcm:
                    self.metadata['file_type'] = fcm['fileType']
                if 'runType' in fcm:
                    self.run_type = fcm['runType']

        if len(app) > 0:
            self.metadata['application'] = app

        # Done.

        return


    def __del__(self):
        #----------------------------------------------------------------------
        # 
        # Purpose: Destroctor.
        #
        #----------------------------------------------------------------------

        self.close()


    def begin_run(self, run):
        #----------------------------------------------------------------------
        # 
        # Purpose: Called at begin run time.  This function calls the begin run
        #          functions provided by analysis modules.
        #
        # Arguments: run - Run number.
        #
        #----------------------------------------------------------------------

        print('Begin run %d' % run)

        # Call analyzer begin run hooks.

        for analyzer in self.analyzers:
            analyzer.begin_run(run)


    def end_run(self, run):
        #----------------------------------------------------------------------
        # 
        # Purpose: Called at end run time.  This function calls the end run
        #          functions provided by analysis modules.
        #
        # Arguments: run - Run number.
        #
        #----------------------------------------------------------------------

        print('End run %d' % run)

        # Call analyzer end run hooks.

        for analyzer in self.analyzers:
            analyzer.end_run(run)


    def begin_subrun(self, run, subrun):
        #----------------------------------------------------------------------
        # 
        # Purpose: Called at begin subrun time.  This function calls the begin
        #          subrun functions provided by analysis modules.
        #
        # Arguments: run - Run number.
        #
        #----------------------------------------------------------------------

        print('Begin subrun (%d, %d)' % (run, subrun))

        # Call analyzer begin subrun hooks.

        for analyzer in self.analyzers:
            analyzer.begin_subrun(run, subrun)

        # Add this subrun to metadata.

        if 'runs' not in self.metadata:
            self.metadata['runs'] = []
        self.metadata['runs'].append((run, subrun, self.run_type))


    def end_subrun(self, run, subrun):
        #----------------------------------------------------------------------
        # 
        # Purpose: Called at end subrun time.  This function calls the end
        #          subrun functions provided by analysis modules.
        #
        # Arguments: run - Run number.
        #
        #----------------------------------------------------------------------

        print('End subrun (%d, %d)' % (run, subrun))

        # Call analyzer end subrun hooks.

        for analyzer in self.analyzers:
            analyzer.end_subrun(run, subrun)


    def read(self, tree):
        #----------------------------------------------------------------------
        # 
        # Purpose: Load and process all entries in the input tree (the event 
        #          loop).  This function calls "analyze" functions provided by
        #          analysis modules, as well as begin/end run and begin/end subrun.
        #
        # Arguments: tree - TTree object.
        #
        #----------------------------------------------------------------------

        entries = 0
        if tree.InheritsFrom('TChain'):
            entries = tree.GetEntries()
        else:
            entries = tree.GetEntriesFast()

        for jentry in xrange(entries):

            # Skip events.

            if self.nskip > 0:
                self.nskip -= 1
                continue

            # Make sure tree is loaded (only relevant for TChains).

            ientry = tree.LoadTree( jentry )
            if ientry < 0:
                break
    
            # Load next entry into memory.

            nb = tree.GetEntry( jentry )
            if nb <= 0:
                continue

            # Extract the current (run, subrun, event).
            # Since this script doesn't know where run, subrun, and event are
            # stored in the input tree (if they are), it relies on analysis
            # module function "event_info" to obtain this information.  It can
            # happen the run, subrun, event information is not available.

            oldrun = self.runnum
            oldsubrun = self.subrunnum

            newrun = None
            newsubrun = None
            newevent = None

            for analyzer in self.analyzers:
                info = analyzer.event_info(tree)
                if newrun == None and info != None and len(info) >= 1 and info[0] != None:
                    newrun = info[0]
                if newsubrun == None and info != None and len(info) >= 2 and info[1] != None:
                    newsubrun = info[1]
                if newevent == None and info != None and len(info) >= 3 and info[2] != None:
                    newevent = info[2]

                # Stop checking after we get results.

                if newrun != None and newsubrun != None and newevent != None:
                    break

            # Keep user from getting bored.

            if jentry % self.dump_every == 0:
                print('Entry = %d/ %d' % (jentry, entries), end=' ')
                if newrun != None:
                    print(', run=%d' % newrun, end=' ')
                if newsubrun != None:
                    print(', subrun=%d' % newsubrun, end=' ')
                if newevent != None:
                    print(', event=%d' % newevent, end=' ')
                print()

            # Check for new run.

            if newrun != None and newrun != oldrun:
                if oldrun != None:
                    self.end_run(oldrun)
                self.runnum = newrun
                self.begin_run(newrun)

            # Check for new subrun.

            if newrun != None and newsubrun != None and (newrun, newsubrun) != (oldrun, oldsubrun):
                if oldrun != None and oldsubrun != None:
                    self.end_subrun(oldrun, oldsubrun)
                self.subrunnum = newsubrun
                self.begin_subrun(newrun, newsubrun)

            # Update event number.

            self.eventnum = newevent

            # Update metadata.

            if self.eventnum != None:
                if self.first_event == None:
                    self.first_event = self.eventnum
                self.last_event = self.eventnum
            self.event_count += 1

            # Call analyze function for each analyzer.

            for analyzer in self.analyzers:
                analyzer.analyze_entry(tree)

            # Decrement event count.

            if self.nev > 0:
                self.nev -= 1
                if self.nev == 0:
                    self.done = True
                    break

        # Done.

        return


    def find_tree(self, tree_name, dir):
        #----------------------------------------------------------------------
        # 
        # Purpose: Find input tree in the specified directory.  Also search
        #          subdirectories.
        #
        # Arguments: tree_name - Tree name (name or path).
        #            dir       - Root directory (TDirectory).
        #
        # Returns: Tree object (TTree) or None.
        #
        #----------------------------------------------------------------------

        if tree_name == None:
            return None

        # First try a plain "Get".

        obj = dir.Get(tree_name)
        if obj and obj.InheritsFrom('TTree'):
            return obj

        # Plain Get didn't work.  Recursively descend into subdirectories.

        keys = dir.GetListOfKeys()
        for key in keys:
            cl = ROOT.TClass(key.GetClassName())

            # Is this a subdirectory?

            if cl.InheritsFrom('TDirectory'):
                subdir = dir.Get(key.GetName())
                obj = self.find_tree(tree_name, subdir)
                if obj and obj.InheritsFrom('TTree'):
                    return obj

        # If we fall out of loop, search failed.

        return None


    def set_branch_statuses(self, tree):
        #----------------------------------------------------------------------
        # 
        # Purpose: Set branch statuses for tree or chain.
        #
        # Arguments: tree - TTree object.
        #
        #----------------------------------------------------------------------
        
        tree.SetBranchStatus("*",0);
        for branch_name in self.branch_names:
            tree.SetBranchStatus(branch_name, 1);

        # Print list of activated branches for this tree.

        print('List of activated branches:')
        for branch in tree.GetListOfBranches():
            if tree.GetBranchStatus(branch.GetName()):
                print('  %s' % branch.GetName())

        # Done

        return


    def open_input(self, input_file_name):
        #----------------------------------------------------------------------
        # 
        # Purpose: Open an input file.  Find the input tree and set branch
        #          statuses.
        #
        # Arguments: input_file_name - Input file.
        #
        #----------------------------------------------------------------------

        print('Opening input file %s' % input_file_name)
        self.input_file = ROOT.TFile.Open(input_file_name)
        if not self.input_file.IsOpen():
            print('Unable to open input file %s.' % input_file_name)
            sys.exit(1)
        print('Open successful.')

        # Call open_input hook for each analyzer.

        for analyzer in self.analyzers:
            analyzer.open_input(self.input_file)

        # Get input trees.

        self.trees = []
        for tree_name in self.tree_names:
            tree = self.find_tree(tree_name, self.input_file)
            if tree != None:

                # Tree successfully located.

                self.trees.append(tree)
                self.set_branch_statuses(tree)

            else:

                # Failed to locate tree.

                print('Unable to find tree %s.' % tree_name)

        # Done.

        return


    def close_input(self):
        #----------------------------------------------------------------------
        # 
        # Purpose: Close the currently open input file.
        #
        #----------------------------------------------------------------------

        if self.input_file is not None and self.input_file.IsOpen():

            # Call close_input hook for each analyzer.

            for analyzer in self.analyzers:
                analyzer.close_input(self.input_file)

            self.input_file.Close()
            self.input_file = None

        # Done.

        return


    def close(self):
        #----------------------------------------------------------------------
        # 
        # Purpose: Close the output file.  Also generate metadata json file.
        #
        #----------------------------------------------------------------------

        if self.output_file is not None and self.output_file.IsOpen():
            self.output_file.Write()
            self.output_file.Close()
            self.output_file = None

            # Generate sam metadata json file.

            end_time = datetime.datetime.utcnow().replace(microsecond=0).isoformat()
            self.metadata['end_time'] = end_time
            self.metadata['first_event'] = self.first_event
            self.metadata['last_event'] = self.last_event
            self.metadata['event_count'] = self.event_count
            self.metadata['parents'] = self.parents
            json_name = self.output_file_name + '.json'
            mf = open(json_name, 'w')
            json.dump(self.metadata, mf, indent=2, sort_keys=True)
            mf.write('\n')
            mf.close()

        # Done.

        return


    def run(self):
        #----------------------------------------------------------------------
        # 
        # Purpose: Run the framework.  This function controls the main file loop.
        #
        #----------------------------------------------------------------------

        # Call begin job analysis module functions.

        for analyzer in self.analyzers:
            analyzer.begin_job()

        # Loop over input files.
        # In this loop we either
        # a) Load and process trees individually, or
        # b) Prepare a TChain to be processed after the loop is finished.

        tchains = []
        if self.chain:
            for tree_name in self.tree_names:
                tchains.append(ROOT.TChain(tree_name))

        for line in self.input_file_names:
            input_file_name = line.strip()

            # Update metadata.

            filename = os.path.basename(input_file_name)
            if not filename in self.parents:
                self.parents.append({'file_name' : filename})

            # Open input file, or add to TChain.

            if self.chain:

                print('Add file to TChain: %s' % input_file_name)
                for tchain in tchains:
                    tchain.AddFile(input_file_name)

            else:
                self.open_input(input_file_name)

                for tree in self.trees:

                    # Call analyzer hooks to analyze the whole tree.

                    for analyzer in self.analyzers:
                        analyzer.analyze_tree(tree)

                    # Read entries.

                    if self.loop_over_entries:
                        self.read(tree)

                # Close input file.

                self.close_input()
                if self.done:
                    break

        # Do additional chain processing here.

        for tchain in tchains:

            # Call analyzer hooks to analyze the whole tree.

            for analyzer in self.analyzers:
                analyzer.analyze_tree(tchain)

            # Read entries.

            if self.loop_over_entries:
                self.read(tchain)

        # End the current run and subrun.

        if self.runnum != None:
            self.end_run(self.runnum)
            if self.subrunnum != None:
                self.end_subrun(self.runnum, self.subrunnum)

        # Call end job analysis module functions.
        # Analysis modules can contribute metadata at this point.

        for analyzer in self.analyzers:
            md = analyzer.end_job()
            if md != None:
                for key in md:
                    self.metadata[key] = md[key]

        # Close output file.

        self.close()

        # Done.

        return

def main(argv):
    #----------------------------------------------------------------------
    # 
    # Purpose: Main program.
    #
    # Arguments: argv - Command line arguments (sys.argv).
    #
    #----------------------------------------------------------------------

    # Parse command line.

    config = ''
    infile = ''
    inlist = ''
    prjurl = ''
    pid = 0
    outfile = 'hist.root'
    nev = 0
    nskip = 0
    args = argv[1:]
    while len(args) > 0:
        if args[0] == '-h' or args[0] == '--help':
            help()
            return 0
        elif (args[0] == '-c' or args[0] == '--config') and len(args) > 1:
            config = args[1]
            del args[0:2]
        elif (args[0] == '-s' or args[0] == '--source') and len(args) > 1:
            infile = args[1]
            del args[0:2]
        elif (args[0] == '-S' or args[0] == '--source-list') and len(args) > 1:
            inlist = args[1]
            del args[0:2]
        elif args[0] == '--sam-web-uri' and len(args) > 1:
            prjurl = args[1]
            del args[0:2]
        elif args[0] == '--sam-process-id' and len(args) > 1:
            pid = args[1]
            del args[0:2]
        elif (args[0] == '-o' or args[0] == '--output' or \
                  args[0] == '-T' or args[0] == '--TFileName') and len(args) > 1:
            outfile = args[1]
            del args[0:2]
        elif (args[0] == '-n' or args[0] == '--nevts') and len(args) > 1:
            nev = int(args[1])
            del args[0:2]
        elif args[0] == '--nskip' and len(args) > 1:
            nskip = int(args[1])
            del args[0:2]
        elif args[0] == '--rethrow-default':
            del args[0]
        else:
            print('Unknown option %s' % args[0])
            return 1

    # Parse configuration.

    pset = fcl.make_pset(config)

    # Add default parameters.

    if 'loop_over_entries' not in pset:
        pset['loop_over_entries'] = True
    if 'chain' not in pset:
        pset['chain'] = False
    if 'dump_every' not in pset:
        pset['dump_every'] = 10

    # Validate arguments.

    # Exactly one of infile, inlist, or prjurl must be specified.
    # Depending on which one was specified, construct the input iterable.

    n = 0
    input_iter = None

    if infile != '':

        # Input from single file.

        n = n + 1
        input_iter = [infile]

    if inlist != '':

        # Input from file list.

        n = n + 1
        input_iter = open(inlist)

    if prjurl != '':

        # Input from sam.

        n = n + 1
        input_iter = sam_iter(prjurl, pid, cleanup=not pset['chain'])

    if n == 0:
        print('No input specified.')
        return 1
    if n > 1:
        print('More than one input specified.')
        return 1

    # Create framework object.

    fwk = Framework(pset, input_iter, outfile, nev, nskip)

    # Run.

    fwk.run()

    # Sam final cleanup.

    if prjurl != '':
        sam_clean(prjurl, pid, cleanup=True)

    # Done

    return 0


if __name__ == '__main__':
    rc = main(sys.argv)
    sys.exit(rc)
