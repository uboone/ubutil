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
# This script is designed as a drop in replacement for the art executable
# (art or lar) in the sense that it supports many of the same command line
# options as the standard art executable.
#
# This script also resembles the art executable in that it requires a fcl
# configuration file, and its actions are controlled by this fcl file.  The
# expected format of the file file is given below.
#
# This script opens a sequence root ntuples and imports and calls a sequence
# of analysis modules.  It is designed specfically to work with analysis
# tree ntuples, but should work with similarly structured root ntuples.
#
# This script performs the following functions:
#
# 1.  Opening and closing input root files (file loop).
# 2.  Opening and closing one single output root file.
# 3.  Reading the input TTree.
# 4.  Setting input TTree branch statuses (load selected branches).
# 5.  Looping over and loading entries of input ntuples (event loop).
# 6.  Calling analysis module functions.
# 7.  Generating sam metadata for the output file.
#
# Reading input from sam.
#
# The sam project and consumer process should be started externally to this script.
# The project url and process id should be specified as command line arguments.
#
# Fcl file format:
#
# input_tree : "anatree"   # Name of input TTree.
# modules : { module1 : config1,
#             module2 : config2 }
#
#
#
# The configuration object can any valid fcl object (e.g. a fcl table).  A pythonized
# version of the configuration will be passed to the module factory function.
#
# Analysis modules should define the following module function.
#
# 1.  make(config) - Factory function to create an instance of an analysis class.  The
#                    single argument is the pythonized configuration object from the
#                    fcl file.
#
# The analysis class object returned by function make() can be any class, but
# normally would be an instance of a class defined by the analysis module.
#
# There is no base class that the analysis class must inherit from.  The 
# analysis class should define the following functions, which will be called 
# at appropriate times.
#
# 1.  branches(tree) - Argument is a TTree.  Return a list or tuple of branch
#                      names that the analysis class wants loaded from this tree.
#                      Wildcards are allowed.  Return ['*'] to load all branches.
#                      Called each time an input tree is opened.
# 2.  output(tfile)  - Argument is an open TFile object.  Called once per job 
#                      initialization.  Each analysis object can add arbitrary
#                      content to the output file.  Analysis objects can also
#                      keep a copy of the tfile object (really a reference) and
#                      add content at later times (e.g. per run).
# 3.  analyze(tree)  - Argument is a loaded TTree object.  Called for each
#                      tree entry.
#
#
###############################################################################
import sys, os, imp, fcl

# Prevent root from printing garbage on initialization.
if os.environ.has_key('TERM'):
    del os.environ['TERM']

# Hide command line arguments from ROOT module.
myargv = sys.argv
sys.argv = myargv[0:1]

import ROOT
#ROOT.gErrorIgnoreLevel = ROOT.kError
sys.argv = myargv

# Help function.

def help():

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
                print line[2:],
            else:
                print


# Global ifdh object.

Ifdh = None

# SAM iterator.

def sam_iter(prjurl, pid):
    # Arguments:
    #
    # prjurl - Project url.
    # pid    - Process id.

    # Initialize ifdh object, if not already done.

    global Ifdh
    if Ifdh == None:
        import ifdh
        Ifdh = ifdh.ifdh()

    # File loop.

    current_file = None
    while True:

        # Release most recent file, if any.

        if current_file:
            Ifdh.updateFileStatus(prjurl, pid, os.path.basename(current_file), 'consumed')

        # Get next file.

        current_file = Ifdh.getNextFile(prjurl, pid)
        if current_file:

            # Fetch the input file.

            current_file = Ifdh.fetchInput(current_file)
            Ifdh.updateFileStatus(prjurl, pid, os.path.basename(current_file), 'transferred')

            # Return the next file.

            yield current_file

        else:

            # Stop iteration.

            return


# Framework class

class Framework:

    # Constructor.

    def __init__(self,
                 input_file_names,
                 output_file_name,
                 analysis_module_names,
                 tree_name,
                 nev,
                 nskip) :

        # Remember arguments.

        self.input_file_names = input_file_names            # Input file names (iterator).
        self.output_file_name = output_file_name            # Output file name.
        self.analysis_module_names = analysis_module_names  # Analysis modules.
        self.tree_name = tree_name                          # Input tree path.
        self.nev = nev                                      # Number of events to process.
        self.nskip = nskip                                  # Number of events to skip.
        self.done = False                                   # Finish flag.

        # Other class data members.

        self.output_file = None      # Output TFile object.
        self.input_file = None       # Currently open input TFile object.
        self.tree = None             # Current input TTree.
        self.analyzers = []          # Analyzer objects.

        # Open output file.

        print 'Opening output file %s' % output_file_name
        self.output_file = ROOT.TFile.Open(output_file_name, 'RECREATE')
        if not self.output_file or not self.output_file.IsOpen():
            print 'Unable to open output file.'
            sys.exit(1)
        print 'Open successful.'

        # Import analysis modules and make analyzer objects.

        for module_name in self.analysis_module_names:
            config = self.analysis_module_names[module_name]
            print 'Importing module %s' % module_name
            fp, pathname, description = imp.find_module(module_name)
            module = imp.load_module(module_name, fp, pathname, description)
            print 'Making analyzer object.'
            analyzer = module.make(config)
            self.analyzers.append(analyzer)

        # Call the output function of each analyzer.

        for analyzer in self.analyzers:
            analyzer.output(self.output_file)

        # Done.

        return


    # Destructor.

    def __del__(self):
        self.close()


    # Read and process all entries for current tree.

    def read(self):
        entries = self.tree.GetEntriesFast()

        for jentry in xrange(entries):

            # Skip events.

            if self.nskip > 0:
                self.nskip -= 1
                continue

            if jentry%1 == 0:
                print jentry,"/",entries

            # Make sure tree is loaded.

            ientry = self.tree.LoadTree( jentry )
            if ientry < 0:
                break
    
            # Load next entry into memory and verify

            nb = self.tree.GetEntry( jentry )
            if nb <= 0:
                continue

            # Call analyze function for each analyzer.

            for analyzer in self.analyzers:
                analyzer.analyze(self.tree)            

            # Decrement event count.

            if self.nev > 0:
                self.nev -= 1
                if self.nev == 0:
                    self.done = True
                    break

        # Done.

        return


    # Find input tree in input file in the specified TDirectory.
    # If successful, return TTree object, otherwise None.

    def find_tree(self, dir):

        result = None

        # Loop over keys from this directory.
        # Look for
        # a) TTrees with the correct name.
        # b) Subdirectories.

        keys = dir.GetListOfKeys()
        subdirs = []
        for key in keys:
            cl = ROOT.TClass(key.GetClassName())

            # Is this the correct tree?

            if cl.InheritsFrom('TTree') and key.GetName() == self.tree_name:
                result = dir.Get(key.GetName())
                break

            # Is this a subdirectory?

            if cl.InheritsFrom('TDirectory'):
                subdirs.append(key.GetName())

        # If we didn't find the right tree in this directory, search subdirectories.

        if result == None:
            for subdir in subdirs:
                result = self.find_tree(dir.Get(subdir))
                if result != None:
                    break

        # Done

        return result


    # Open input file.

    def open_input(self, input_file_name):
        print 'Opening input file %s' % input_file_name
        self.input_file = ROOT.TFile.Open(input_file_name)
        if not self.input_file.IsOpen():
            print 'Unable to open input file %s.' % input_file_name
            sys.exit(1)
        print 'Open successful.'

        # Get input tree.

        self.tree = self.find_tree(self.input_file)
        if self.tree == None:
            print 'Unable to find tree %s.' % self.tree_name

        # Set branch statuses.

        if self.tree != None:
            self.tree.SetBranchStatus("*",0);
            for analyzer in self.analyzers:
                branch_names = analyzer.branches(self.tree)
                for branch_name in branch_names:
                    print 'Read branch %s' % branch_name
                    self.tree.SetBranchStatus(branch_name, 1);

        # Done.

        return


    # Close input file.

    def close_input(self):
        if self.input_file is not None and self.input_file.IsOpen():
            self.input_file.Close()
            self.input_file = None

        # Done.

        return


    # Close output file.

    def close(self):

        if self.output_file is not None and self.output_file.IsOpen():
            self.output_file.Write()
            self.output_file.Close()
            self.output_file = None

        # Done.

        return


    # Run framework (file and event loop).

    def run(self):

        # Loop over input files.

        for input_file_name in self.input_file_names:

            # Open input file.

            self.open_input(input_file_name)

            # Read entries.

            if self.tree != None:
                self.read()

            # Close input file.

            self.close_input()
            if self.done:

                # In case of premature break, invoke the file iterator one 
                # more time to change sam status to consumed.

                try:
                    self.input_file_names.next()
                except:
                    pass
                break

        # Done.

        return

def main(argv):

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
            print 'Unknown option %s' % args[0]
            return 1

    # Validate arguments.

    # Exactly one of infile, inlist, or prjurl must be specified.
    # Depending on which one was specified, construct the input iterable.

    n = 0
    input_iter = None
    if infile != '':
        n = n + 1
        input_iter = [infile]
    if inlist != '':
        n = n + 1
        input_iter = inlist
    if prjurl != '':
        n = n + 1
        input_iter = sam_iter(prjurl, pid)
    if n == 0:
        print 'No input specified.'
        return 1
    if n > 1:
        print 'More than one input specified.'
        return 1

    # Parse configuration.

    pset = fcl.make_pset(config)
    tree_name = pset['input_tree']
    modules = pset['modules']

    # Create framework object.

    fwk = Framework(input_iter, outfile, modules, tree_name, nev, nskip)

    # Run.

    fwk.run()

    # Close output file.

    fwk.close()


if __name__ == '__main__':
    rc = main(sys.argv)
    sys.exit(rc)
