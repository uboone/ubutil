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
# source file (RootAnalyze.py) for a detailed description of class functions that
# analysis classes can overload.  Analysis classes are not required to overload
# any base class functions.  Most analysis classes will want to overload 
# function "analyze," which is called for each ntuple entry (event).
#
# Fcl file format
#----------------
#
# process_name : "myprocess"         # Required by work flow.
# input_tree : "anatree"             # Name of input TTree.
# modules : { module1 : config1
#             module2 : config2 }
#
###############################################################################
import sys, os, imp, fcl, json, datetime

# Prevent root from printing garbage on initialization.
if os.environ.has_key('TERM'):
    del os.environ['TERM']

# Hide command line arguments from ROOT module.
myargv = sys.argv
sys.argv = myargv[0:1]

import ROOT
#ROOT.gErrorIgnoreLevel = ROOT.kError
sys.argv = myargv

# Global ifdh object.

Ifdh = None


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
                print line[2:],
            else:
                print


def sam_iter(prjurl, pid):
    #----------------------------------------------------------------------
    #
    # Purpose: A sam generator.
    #
    # Arguments: prjurl - Project url.
    #            pid    - Process id.
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

        url = Ifdh.getNextFile(prjurl, pid)
        if url:

            # Fetch the input file.

            current_file = Ifdh.fetchInput(url)
            Ifdh.updateFileStatus(prjurl, pid, os.path.basename(current_file), 'transferred')

            # Return the next file.

            yield current_file

        else:

            # Stop iteration.

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

        # Other class data members.

        self.tree_name = pset['input_tree']   # Input tree name.
        self.output_file = None               # Output TFile object.
        self.input_file = None                # Currently open input TFile object.
        self.tree = None                      # Current input TTree.
        self.analyzers = []                   # Analyzer objects.
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

        print 'Opening output file %s' % output_file_name
        self.output_file = ROOT.TFile.Open(output_file_name, 'RECREATE')
        if not self.output_file or not self.output_file.IsOpen():
            print 'Unable to open output file.'
            sys.exit(1)
        print 'Open successful.'

        # Import analysis modules and make analyzer objects.

        for module_name in self.pset['modules']:
            print 'Importing module %s' % module_name
            fp, pathname, description = imp.find_module(module_name)
            module = imp.load_module(module_name, fp, pathname, description)
            print 'Making analyzer object.'
            analyzer = module.make(self.pset)
            self.analyzers.append(analyzer)

        # Call the open output function of each analyzer.

        for analyzer in self.analyzers:
            analyzer.open_output(self.output_file)

        # Update metadata.

        self.metadata['start_time'] = datetime.datetime.utcnow().replace(microsecond=0).isoformat()

        # Extract experiment-independent metadata from FileCatalogMetadata configuration.

        app = {}

        if self.pset.has_key('process_name'):
            app['name'] = self.pset['process_name']

        if self.pset.has_key('services'):
            services = self.pset['services']
            if services.has_key('FileCatalogMetadata'):
                fcm = services['FileCatalogMetadata']
                if fcm.has_key('applicationFamily'):
                    app['family'] = fcm['applicationFamily']
                if fcm.has_key('applicationFamily'):
                    app['version'] = fcm['applicationVersion']
                if fcm.has_key('group'):
                    self.metadata['group'] = fcm['group']
                if fcm.has_key('fileType'):
                    self.metadata['file_type'] = fcm['fileType']
                if fcm.has_key('runType'):
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

        print 'Begin run %d' % run

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

        print 'End run %d' % run

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

        print 'Begin subrun (%d, %d)' % (run, subrun)

        # Call analyzer begin subrun hooks.

        for analyzer in self.analyzers:
            analyzer.begin_subrun(run, subrun)

        # Add this subrun to metadata.

        if not self.metadata.has_key('runs'):
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

        print 'End subrun (%d, %d)' % (run, subrun)

        # Call analyzer end subrun hooks.

        for analyzer in self.analyzers:
            analyzer.end_subrun(run, subrun)


    def read(self):
        #----------------------------------------------------------------------
        # 
        # Purpose: Load and process all entries in the current tree (the event 
        #          loop).  This function calls "analyze" functions provided by
        #          analysis modules, as well as begin/end run and begin/end subrun.
        #
        #----------------------------------------------------------------------

        entries = self.tree.GetEntriesFast()

        for jentry in xrange(entries):

            # Skip events.

            if self.nskip > 0:
                self.nskip -= 1
                continue

            # Keep user from getting bored.

            if jentry%10 == 0:
                print jentry,"/",entries

            # Make sure tree is loaded.

            ientry = self.tree.LoadTree( jentry )
            if ientry < 0:
                break
    
            # Load next entry into memory.

            nb = self.tree.GetEntry( jentry )
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
                info = analyzer.event_info(self.tree)
                if newrun == None and info != None and len(info) >= 1 and info[0] != None:
                    newrun = info[0]
                if newsubrun == None and info != None and len(info) >= 2 and info[1] != None:
                    newsubrun = info[1]
                if newevent == None and info != None and len(info) >= 3 and info[2] != None:
                    newevent = info[2]

                # Stop checking after we get results.

                if newrun != None and newsubrun != None and newevent != None:
                    break

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
                analyzer.analyze(self.tree)            

            # Decrement event count.

            if self.nev > 0:
                self.nev -= 1
                if self.nev == 0:
                    self.done = True
                    break

        # Done.

        return


    def find_tree(self, dir):
        #----------------------------------------------------------------------
        # 
        # Purpose: Find the input tree, as specified by class variable
        #          self.tree_name, in the specified directory.  Also search
        #          subdirectories.
        #
        # Arguments: dir - Root directory (TDirectory).
        #
        # Returns: Tree object (TTree) or None.
        #
        #----------------------------------------------------------------------

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


    def open_input(self, input_file_name):
        #----------------------------------------------------------------------
        # 
        # Purpose: Open an input file.  Find the input tree and set branch
        #          statuses.
        #
        # Arguments: input_file_name - Input file.
        #
        #----------------------------------------------------------------------

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

        else:
            self.tree.SetBranchStatus("*",0);
            for analyzer in self.analyzers:
                branch_names = analyzer.branches(self.tree)
                for branch_name in branch_names:
                    print 'Read branch %s' % branch_name
                    self.tree.SetBranchStatus(branch_name, 1);

        # Update metadata.

        filename = os.path.basename(input_file_name)
        if not filename in self.parents:
            self.parents.append({'file_name' : filename})

        # Done.

        return


    def close_input(self):
        #----------------------------------------------------------------------
        # 
        # Purpose: Close the currently open input file.
        #
        #----------------------------------------------------------------------

        if self.input_file is not None and self.input_file.IsOpen():
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

        for input_file_name in self.input_file_names:

            # Open input file.

            self.open_input(input_file_name.strip())

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
            print 'Unknown option %s' % args[0]
            return 1

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
        input_iter = sam_iter(prjurl, pid)

    if n == 0:
        print 'No input specified.'
        return 1
    if n > 1:
        print 'More than one input specified.'
        return 1

    # Parse configuration.

    pset = fcl.make_pset(config)

    # Create framework object.

    fwk = Framework(pset, input_iter, outfile, nev, nskip)

    # Run.

    fwk.run()


if __name__ == '__main__':
    rc = main(sys.argv)
    sys.exit(rc)
