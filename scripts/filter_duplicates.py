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
from __future__ import print_function

samweb = project_utilities.samweb()

# If file cpid.txt exists, use process id to identify consumed files as parents.

parents = []
cpid=''
if os.path.exists('cpid.txt'):
    lines = open('cpid.txt').readlines()
    if len(lines) > 0:
        cpid = lines[0].strip()
    
if cpid != '':
    dim = 'consumer_process_id %s and consumed_status consumed' % cpid
    parents = samweb.listFiles(dimensions=dim)
print('%d parents based on sam process id %s' % (len(parents), cpid))

# Extract sam metadata for each artroot file in the local directory.

for f in os.listdir('.'):
    if f.endswith('.root') or f.endswith('.pndr'):
        print('Checking file %s' % f)
        this_file_parents = []
        for parent in parents:
            if parent not in this_file_parents:
                this_file_parents.append(parent)

        # Extract precalculated sam metadata for this file.

        md0 = {}
        json_file = f + '.json'
        if project_utilities.safeexist(json_file):
            mdlines = project_utilities.saferead(json_file)
            mdtext = ''
            for line in mdlines:
                mdtext = mdtext + line
            try:
                md0 = json.loads(mdtext)
            except:
                md0 = {}
                pass

        # Extract internal sam metadata for this root file as python dictionary.

        md = {}
        try:
            m = extractor_dict.expMetaData(project_utilities.get_experiment(), f)
            md = m.getmetadata(md0)
        except:
            md = md0

        # Extract metadata parents.

        if len(md) > 0:
            if 'parents' in md:
                for parent in md['parents']:
                    pname = parent['file_name']
                    if pname not in this_file_parents:
                        this_file_parents.append(pname)

        # Loop over parents.

        for pname in this_file_parents:

            # Check whether this file is a duplicate.

            if not pname.startswith('CRT'):
                print('Checking parent %s' % pname)
                dim = 'ischildof: ( file_name %s with availability physical )' % pname
                if 'file_type' in md:
                    dim += ' and file_type %s' % md['file_type']
                if 'file_format' in md:
                    dim += ' and file_format %s' % md['file_format']
                if 'data_tier' in md:
                    dim += ' and data_tier %s' % md ['data_tier']
                if 'data_stream' in md:
                    dim += ' and data_stream %s' % md['data_stream']
                if 'ub_Project.Name' in md:
                    dim += ' and ub_project.name %s' % md['ub_Project.Name']
                if 'ub_Project.Stage' in md:
                    dim += ' and ub_project.stage %s%%' % md['ub_Project.Stage']
                if 'ub_Project.Version' in md:
                    dim += ' and ub_project.version %s' % md['ub_Project.Version']
                if 'ub_project.name' in md:
                    dim += ' and ub_project.name %s' % md['ub_project.name']
                if 'ub_project.stage' in md:
                    dim += ' and ub_project.stage %s%%' % md['ub_project.stage']
                if 'ub_project.version' in md:
                    dim += ' and ub_project.version %s' % md['ub_project.version']
                s = samweb.listFilesSummary(dimensions=dim)
                nf = s['file_count']
                if nf != 0:

                    # This file is a duplicate.  Remove it.

                    print('Deleting duplicate file %s.' % f)
                    os.remove(f)
                    break         # Break out of loop over parents.

