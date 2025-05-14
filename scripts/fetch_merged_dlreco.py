#! /usr/bin/env python
######################################################################
#
# Name: fetch_merged_dlreco.py
#
# Purpose: Fetch or make file merged_dlreco.root that matches a specified
#          reco2 (artroot) file.
#
# Created: 13-May-2025  H. Greenlee
#
# Usage:
#
# fetch_merged_dlreco.py [-h|--help] [<reco2-file>]
#
# Options:
#
# -h|--help        - Print help message.
# -f               - Overwrite existing output file.
# -o <output-file> - Specify name of output file (default "merged_dlreco.root").
#
# Arguments.
#
# reco2-file - Specify reco2 file name or path.
#
# Usage Notes.
#
# 1.  If the specified output file exists in the current directory,
#     this script will exit immediately, unless option "-f" is
#     specified.
#
# 2.  This script may be invoked without specifying any reco2 file on
#     the command line.  In that case, the script will hunt for a
#     single artroot file in the current directory.  If there is
#     exactly one artroot file in the current directory, the script
#     will use that as the input file.
#
# 3.  The input reco2 file may be specified as a full path or a simple
#     file name.  In the latter case, the absolute locaiton of the
#     reco2 file will be determined using samweb, and the contents of
#     the reco2 file will be read using xrootd.
#
# 4.  This script will use sam parentage information to find matching
#     dlreco files from sam, then copy matching entries into a new
#     dlreco output file.  Contents of dlreco files are read using
#     xrootd.
#
######################################################################

from __future__ import print_function
import sys, os

# Import samweb

import samweb_cli
samweb = samweb_cli.SAMWebClient(experiment='uboone')

# Import ROOT module.
# Globally turn off root warning and error messages.
# Don't let root see our command line options.

myargv = sys.argv
sys.argv = myargv[0:1]
if 'TERM' in os.environ:
    del os.environ['TERM']
import ROOT
ROOT.gErrorIgnoreLevel = ROOT.kFatal
sys.argv = myargv

# Print help.

def dohelp():
    print('Usage:\nfetch_merged_dlreco.py [-h|--help] <reco2-file>')


# Return a list of artroot files in the current directory.

def find_artroot_files():

    result = []

    files = os.listdir()
    for f in files:
        if f.endswith('.root'):

            # Open this file.

            tf = None
            try:
                tf = ROOT.TFile.Open(f, 'read')
            except:
                tf = None
            if tf and tf.IsOpen() and not tf.IsZombie():

                # To qualify as an artroot file, this file must contain the following objects:
                # 1.  A TTree called 'Events'
                # 2.  A TKey called 'RootFileDB'

                has_events = False
                has_db = False
                keys = tf.GetListOfKeys()
                for key in keys:
                    objname = key.GetName()
                    obj = tf.Get(objname)
                    if objname == 'Events' and obj.InheritsFrom('TTree'):
                        has_events = True
                    if objname == 'RootFileDB' and obj.InheritsFrom('TKey'):
                        has_db = True

                if has_events and has_db:
                    result.append(f)

                # Close file.

                tf.Close()
                
    # Done.

    return result


# Main program.

def main(argv):

    # Parse arguments.

    reco2_file_or_path = ''
    do_overwrite = False
    output_file = 'merged_dlreco.root'
    args = argv[1:]

    while len(args) > 0:

        if args[0] == '-h' or args[0] == '--help':
            dohelp()
            sys.exit(0)

        elif args[0] == '-f':
            do_overwrite = True
            del args[0]

        elif len(args) > 1 and args[0] == '-o':
            output_file = args[1]
            del args[0:2]

        elif args[0].startswith('-'):
            print('Unknown option %s' % args[0])
            dohelp()
            sys.exit(1)

        elif reco2_file_or_path == '':
            reco2_file_or_path = args[0]
            del args[0]

        else:
            print('Too many arguments.')
            dohelp()
            sys.exit(1)

    if not do_overwrite and os.path.exists(output_file):
        print('Quitting because %s already exists.' % output_file)
        sys.exit(0)

    # Check arguments.

    if reco2_file_or_path == '':
        artroot_files = find_artroot_files()
        if len(artroot_files) == 1:
            reco2_file_or_path = artroot_files[0]
        elif len(artroot_files) == 0:
            print('Quitting because no input file was specified and')
            print('there are no artroot files in the current directory.')
            sys.exit(1)
        else:
            print('Quitting because no input file was specified and')
            print('there is more than one artroot files in the current directory.')
            sys.exit(1)

    print('Fetching dlreco data for reco2 file %s' % reco2_file_or_path)

    # Open reco2 file for reading.
    # If reco2 file exists locally, open file directly.
    # Otherwise, open xrootd url.

    # Get file base name.

    reco2_file_name = os.path.basename(reco2_file_or_path)

    # Open reco2 file for reading.

    root = None
    if os.path.exists(reco2_file_or_path):

        # Open file.

        print('Opening root file locally.')
        root = ROOT.TFile.Open(reco2_file_or_path, 'read')

    else:

        # File is not directly accessible.  Use xrootd.

        url = samweb.getFileAccessUrls(reco2_file_name, 'root')
        if len(url) > 0:
            print('Opening file using xrootd.')
            root = ROOT.TFile.Open(url[0], 'read')

    if root and root.IsOpen() and not root.IsZombie():
        print('Open successful.')
    else:
        print('Could not open root file.')
        sys.exit(1)

    # Scan the reco2 file to extract its event ids (run, subrun, event).

    event_ids = []
    events_tree = root.Get('Events')
    nevents = events_tree.GetEntriesFast()
    print('%d events.' % nevents)

    tfr = ROOT.TTreeFormula('run', 'EventAuxiliary.id_.subRun_.run_.run_', events_tree)
    tfs = ROOT.TTreeFormula('subrun', 'EventAuxiliary.id_.subRun_.subRun_', events_tree)
    tfe = ROOT.TTreeFormula('event', 'EventAuxiliary.id_.event_', events_tree)
    for entry in range(nevents):
        events_tree.GetEntry(entry)
        run = tfr.EvalInstance64()
        subrun = tfs.EvalInstance64()
        event = tfe.EvalInstance64()
        event_id = (run, subrun, event)
        event_ids.append(event_id)

    # Get metadata of reco2 file.

    md = samweb.getMetadata(reco2_file_name)
    pname = md['ub_project.name']
    pstage = md['ub_project.stage']
    pversion = md['ub_project.version']

    # Loop over parent files of reco2 and identify matching dlreco files.

    dlreco_files = set()   # Dlreco file names.
    dlreco_tfiles = {}     # dlreco name -> open dlreco tfile
    dlreco_event_map = {}  # Event id -> dlreco file, entry #.
    output_trees = {}      # Tree name -> output TTree object.

    parents = samweb.listFiles('isparentof:( file_name %s )' % reco2_file_name)
    for parent in parents:
        print('Found parent file %s' % parent)

        # Query dlreco files corresponding to this parent.

        dim = 'ischildof:( file_name %s ) and data_tier merged_dlreco' % parent
        dim += ' and ub_project.name %s' % pname
        dim += ' and ub_project.stage %s' % pstage
        dim += ' and ub_project.version %s' % pversion
        dls = samweb.listFiles(dim)

        # Don't know what to do if there is not exactly one sibling dlreco file.

        if len(dls) == 0:
            print('Failed to find any dlreco file for parent file %s' % parent)
            sys.exit(1)
        if len(dls) > 1:
            print('Found more than one sibling dlreco file for parent file %s' % parent)
            sys.exit(1)
        dl = dls[0]
        print('Found matching dlreco file %s.' % dl)
        if not dl in dlreco_files:
            dlreco_files.add(dl)

    print('Found %d matching dlreco files.' % len(dlreco_files))
    print()
    if len(dlreco_files) == 0:
        print('Quitting because we did not find any matching dlreco files.')
        sys.exit(1)

    # Open output file.

    print('\nOpening output file %s' % output_file)
    out = ROOT.TFile.Open(output_file, 'recreate')
    if out and out.IsOpen() and not out.IsZombie():
        print('Open successful.')
    else:
        print('Unable to open output file.')
        sys.exit(1)

    # If reco2 file didn't have any events, just close the output file and quit.
    # This is what LANTERN does.  This is not an error.

    if nevents == 0:
        print('Closing output file.')
        out.Close()
        sys.exit(0)

    # Loop over dlreco files.

    for dl in dlreco_files:

        # Open this dlreco file using xrootd.

        print('Opening dlreco file %s' % dl)
        url = samweb.getFileAccessUrls(dl, 'root')
        if len(url) > 0:
            dlroot = ROOT.TFile.Open(url[0], 'read')
            if dlroot and dlroot.IsOpen() and not dlroot.IsZombie():
                print('Open successful.')
                dlreco_tfiles[dl] = dlroot
                keys = dlroot.GetListOfKeys()

                # Clone empty output trees.

                for key in keys:
                    tree_name = key.GetName()
                    if tree_name not in output_trees:
                        print('Cloning tree: %s' % tree_name)
                        input_tree = dlroot.Get(tree_name)
                        output_trees[tree_name] = input_tree.CloneTree(0)  # Clone empty tree.
                        out.cd()
                        output_trees[tree_name].Write()

                # Scan this dlreco file to extract event ids.

                dl_ids_tree = dlroot.Get('larlite_id_tree')
                dl_nevents = dl_ids_tree.GetEntriesFast()
                print('%d events.' % dl_nevents)

                dlr = ROOT.TTreeFormula('dlrun', '_run_id', dl_ids_tree)
                dls = ROOT.TTreeFormula('dlsubrun', '_subrun_id', dl_ids_tree)
                dle = ROOT.TTreeFormula('dlevent', '_event_id', dl_ids_tree)
                for entry in range(dl_nevents):
                    dl_ids_tree.GetEntry(entry)
                    run = dlr.EvalInstance64()
                    subrun = dls.EvalInstance64()
                    event = dle.EvalInstance64()
                    dl_event_id = (run, subrun, event)
                    dlreco_event_map[dl_event_id] = (dl, entry)

            else:
                print('Open failed.')
                sys.exit(1)

    # Loop over output trees.

    for tree_name in output_trees:

        print('Copying tree %s' % tree_name)

        # Loop over event ids from reco2 file.

        for event_id in event_ids:

            # Search for matching dlreco event.

            if event_id in dlreco_event_map:
                dl_entry = dlreco_event_map[event_id]
                dl = dl_entry[0]
                entry = dl_entry[1]
                dlroot = dlreco_tfiles[dl]
                input_tree = dlroot.Get(tree_name)
                input_tree.GetEntry(entry)
                output_trees[tree_name].Fill()
            else:
                print('No matching dlreco event.')
                sys.exit(1)

        # Write output tree to output file.

        out.cd()
        output_trees[tree_name].Write()

    # Close output file.

    print('\nClosing output file.')
    out.Purge()
    out.Close()

    # Done.

    return 0

# Invoke main program.

if __name__ == "__main__":
    sys.exit(main(sys.argv))
