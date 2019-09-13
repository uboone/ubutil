#! /usr/bin/env python
######################################################################
#
# Name: filter_duplicates.py
#
# Purpose: End-of-batch-job script with purpose to filter out files 
#          that are already available in sam.
#
# Created: 12-Sep-2019  Herbert Greenlee
#
# Usage:
#
# $ filter_duplicates.py
#
#
######################################################################

import sys, os, subprocess, json, datetime
import project_utilities
import extractor_dict

samweb = project_utilities.samweb()

# Extract sam metadata for each artroot file in the local directory.

mddict = {}             # metadata = mddict[filename]

stream_files = {}
for f in os.listdir('.'):
    if f.endswith('.root'):
        print 'Checking file %s' % f

        # Extract sam metadata for this root file as python dictionary.

        md = {}
        try:
            m = extractor_dict.expMetaData(project_utilities.get_experiment(), f)
            md = m.getmetadata()
        except:
            md = {}

        if len(md) > 0:

            # Check whether this file is a duplicate.

            if md.has_key('parents'):
                for parent in md['parents']:
                    pname = parent['file_name']
                    if not pname.startswith('CRT'):
                        print 'Checking parent %s' % pname
                        dim = 'ischildof: ( file_name %s with availability physical )' % pname
                        dim += ' and file_type %s' % md['file_type']
                        dim += ' and file_format %s' % md['file_format']
                        dim += ' and data_tier %s' % md ['data_tier']
                        dim += ' and data_stream %s' % md['data_stream']
                        dim += ' and ub_project.name %s' % md['ub_Project.Name']
                        dim += ' and ub_project.stage %s%%' % md['ub_Project.Stage']
                        dim += ' and ub_project.version %s' % md['ub_Project.Version']
                        s = samweb.listFilesSummary(dimensions=dim)
                        nf = s['file_count']
                        if nf != 0:

                            # This file is a duplicate.  Remove it.

                            print 'Deleting duplicate file %s.' % f
                            os.remove(f)
                            break         # Break out of loop over parents.

