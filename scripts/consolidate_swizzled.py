#! /usr/bin/env python
######################################################################
#
# Name: consolidate_swizzled.py
#
# Purpose: End-of-batch-job script with purpose to merge swizzled files
#          by stream, and filter out swizzled files that are already
#          available in sam.
#
# Created: 10-Feb-2019  Herbert Greenlee
#
# Usage:
#
# $ consolidate_swizzled.py
#
#
######################################################################

from __future__ import absolute_import
from __future__ import print_function
import sys, os, subprocess, json, datetime
import project_utilities
import extractor_dict
import root_metadata

samweb = project_utilities.samweb()

# Extract sam metadata for each artroot file in the local directory.

mddict = {}             # metadata = mddict[filename]

stream_files = {}
for f in os.listdir('.'):
    if f.endswith('.root'):
        print('Checking file %s' % f)

        # Extract sam metadata for this root file as python dictionary.

        md = {}
        try:
            m = extractor_dict.expMetaData(project_utilities.get_experiment(), f)
            md = m.getmetadata()
        except:
            md = {}

        if len(md) > 0:

            # Check whether this file is a duplicate.

            duplicate = False
            if 'parents' in md:
                for parent in md['parents']:
                    pname = parent['file_name']
                    if not pname.startswith('CRT'):
                        print('Checking parent %s' % pname)
                        dim = 'ischildof: ( file_name %s with availability physical )' % pname
                        dim += ' and file_type data and file_format artroot and data_tier raw'
                        dim += ' and ub_project.name %s' % md['ub_Project.Name']
                        dim += ' and ub_project.version %s' % md['ub_Project.Version']
                        dim += ' and data_stream %s' % md['data_stream']
                        s = samweb.listFilesSummary(dimensions=dim)
                        nf = s['file_count']
                        if nf != 0:

                            # This file is a duplicate.  Remove it.

                            print('Deleting duplicate file %s.' % f)
                            os.remove(f)
                            duplicate = True
                            break

            if not duplicate:
                mddict[f] = md

# Organize files by stream and run with a maximum merged size.

stream_size = {}        # bytes = stream_size[stream][run][n]
stream_files = {}       # file_list = stream_files[stream][run][n]
max_size = 2000000000   # 2 GBytes

# Job-specific metadata

stream_prjname = {}     # Project name = stream_prjname[stream][run]
stream_prjstage = {}    # Project stage = stream_prjstage[stream][run]
stream_prjversion = {}  # Project version = stream_version[stream][run]
stream_fcl = {}         # fcl name = stream_fcl[stream][run]

for f in list(mddict.keys()):
    md = mddict[f]
    stream = md['data_stream']
    run = md['runs'][0][0]
    if stream not in stream_size:
        stream_size[stream] = {}
    if run not in stream_size[stream]:
        stream_size[stream][run] = []

    if stream not in stream_files:
        stream_files[stream] = {}
    if run not in stream_files[stream]:
        stream_files[stream][run] = []

    if stream not in stream_prjname:
        stream_prjname[stream] = {}
    if run not in stream_prjname[stream]:
        stream_prjname[stream][run] = md['ub_Project.Name']

    if stream not in stream_prjstage:
        stream_prjstage[stream] = {}
    if run not in stream_prjstage[stream]:
        stream_prjstage[stream][run] = md['ub_Project.Stage']

    if stream not in stream_prjversion:
        stream_prjversion[stream] = {}
    if run not in stream_prjversion[stream]:
        stream_prjversion[stream][run] = md['ub_Project.Version']

    if stream not in stream_fcl:
        stream_fcl[stream] = {}
    if run not in stream_fcl[stream]:
        stream_fcl[stream][run] = md['fcl.name']

    # Get this file size.

    size = os.stat(f).st_size
    print('File %s, size = %d' % (f, size))

    # Decide if we should start a new list.

    if len(stream_size[stream][run]) == 0 or stream_size[stream][run][-1] + size > max_size:
        stream_size[stream][run].append(0)
        stream_files[stream][run].append([])

    # Add this file to the current stream list.

    stream_size[stream][run][-1] += size
    stream_files[stream][run][-1].append(f)
    

# Make merging fcl files for each stream and run.
# Generate these fcl files such that the internal metadata is as correct as possible,
# meaning as close as possible to the internal metadata of the files being merged.

version=os.environ['UBOONECODE_VERSION']
for stream in list(stream_size.keys()):

    for run in list(stream_size[stream].keys()):

        stream_fcl_name = 'copy_raw_%s_%d.fcl' % (stream, run)
        fcl = open(stream_fcl_name, 'w')
        fcl.write('''#include "services_microboone.fcl"

process_name: Copy

services:
{
  scheduler:    { defaultExceptions: false }    # Make all uncaught exceptions fatal.
  message:      @local::standard_warning
  FileCatalogMetadata:  @local::art_file_catalog_data
}

''')
        fcl.write('services.FileCatalogMetadata.applicationVersion: "%s"\n' % version)
        fcl.write('''services.FileCatalogMetadata.fileType: "data"
services.FileCatalogMetadata.runType: "physics"
services.FileCatalogMetadataMicroBooNE: {
''')
        fcl.write('  FCLName: "%s"\n' % stream_fcl[stream][run])
        fcl.write('  FCLVersion: "%s"\n' % version)
        fcl.write('  ProjectName: "%s"\n' % stream_prjname[stream][run])
        fcl.write('  ProjectStage: "%s"\n' % stream_prjstage[stream][run])
        fcl.write('  ProjectVersion: "%s"\n' % stream_prjversion[stream][run])
        fcl.write('''}

source:
{
  module_type: RootInput
  maxEvents:  1000000        # Number of events to create
}

physics:
{

 #define the output stream, there could be more than one if using filters
''')
        fcl.write(' stream1:  [ %s ]\n' % stream)
        fcl.write(''' #end_paths is a keyword and contains the paths that do not modify the art::Event, 
 #ie analyzers and output streams.  these all run simultaneously
 end_paths:     [ stream1 ]  
}

outputs:
{
''')
        fcl.write(' %s:\n' % stream)
        fcl.write(''' {
   module_type: RootOutput
   fileName:    "%ifb_%tc_merged.root"
   dataTier:    "raw"
''')
        fcl.write('   streamName:  "%s"\n' % stream)
        fcl.write('''   compressionLevel: 3
 }
}
''')
        fcl.close()

# Merge files in each list.

for stream in list(stream_files.keys()):

    n = 0
    for run in list(stream_files[stream].keys()):

        for stream_list in stream_files[stream][run]:

            print('Merging stream %s[%d][%d]' % (stream, run, n))
            parents = set()
            outname = ''

            # Loop over files in this stream.
            # Make file list and merged metadata.

            stream_list_name = 'files_%s_%d_%d.list' % (stream, run, n)
            fl = open(stream_list_name, 'w')
            for f in stream_list:
                print('  Merging file %s' % f)
                fl.write('%s\n' % f)
                md = mddict[f]
                if 'parents' in md:
                    for p in md['parents']:
                        parent = p['file_name']
                        if parent not in parents:
                            parents.add(parent)

                if outname == '':
                    t = datetime.datetime.now()
                    ts = datetime.datetime.strftime(t, '%Y%m%d%H%M%S')
                    outname = '%s_%s_merged.root' % (os.path.basename(f)[:-5], ts)
            fl.close()

            # Merge files.

            stream_out_name = 'copy_raw_%s_%d_%d.out' % (stream, run, n)
            out = open(stream_out_name, 'w')

            stream_err_name = 'copy_raw_%s_%d_%d.err' % (stream, run, n)
            err = open(stream_err_name, 'w')

            stream_fcl_name = 'copy_raw_%s_%d.fcl' % (stream, run)
            cmd = ['lar', '-c', './%s' % stream_fcl_name, '-S', stream_list_name, '-o', outname]
            job = subprocess.Popen(cmd, stdout=out, stderr=err)
            rc = job.wait()
            out.close()
            err.close()
            print('Exit status %d'% rc)

            if rc == 0:

                # Save parents.

                pfile = open('%s.parents' % outname, 'w')
                plist = list(parents)
                plist.sort()
                for p in plist:
                    print('Parent file: %s' % p)
                    pfile.write('%s\n' % p)
                pfile.close()

                # Extract metadata as python dictionary and update parentage.

                m = extractor_dict.expMetaData(project_utilities.get_experiment(), outname)
                md = m.getmetadata()
                md['parents'] = []
                for p in plist:
                    md['parents'].append({'file_name': p})

                # Save metadata as json file.

                #mdfilename = '%s.json' % outname
                #mdfile = open(mdfilename, 'w')
                #json.dump(md, mdfile, indent=2, sort_keys = True)
                #mdfile.close()

                # Declare file to sam.

                print('Declaring %s.' % outname)
                samweb.declareFile(md=md)

            # Delete all input files, whether or not merge job succeeded.

            for f in stream_list:
                print('  Deleting file %s' % f)        
                os.remove(f)

            # Done with this list.

            n += 1

# Generate external metadata for each newly generated artroot file.

#for f in os.listdir('.'):
#    if f.endswith('_merged.root'):
#        print 'Generating external metadata for %s' % f
#        md = root_metadata.get_external_metadata(f)
#        jsonfilename = '%s.json' % f
#        jsonfile = open(jsonfilename, 'w')
#        json.dump(md, jsonfile, indent=2, sort_keys = True)
#        jsonfile.close()
