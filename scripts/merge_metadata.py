#!/usr/bin/env python
#---------------------------------------------------------------------------
#
# Name: merge_metadata.py
#
# Purpose: Calculate merged metadata for a file merged from several files.
#          Result is printed as json object to standard output.
#
# Created: 3-Apr-2015  H. Greenlee
#
# Command line usage:
#
# merge_metadata.py <file-list> [<process id>]
#
# Usage notes.
#
# 1.  Some metadata are ignored, including file_name, file_size, checksum.
#
# 2.  Blinding metadata are ignored, which is to say that all merged files
#     are born not blind (they may be subsequently blinded by blinding cron
#     jobs).
#
# 3.  The following metadata are aggregated:
#
#     a) first_event
#     b) last_event
#     c) event_count
#     d) mc.pot
#     e) runs
#
# 4.  By default, parents are generated to match the list of files.
#     Parent metadata of input files are ignored.
#
# 5.  Start time and end time are set to the current time (local time).
#
#---------------------------------------------------------------------------

# Import stuff.

from __future__ import print_function
import sys, json, project_utilities, datetime

# Function to calculate merged metadata from a file list.
# Merged metadata python dictionary returned by function.

def merge_metadata(filelist, cpid):

    samweb = project_utilities.samweb()

    # Merged metadata dictionary.

    merged_md = {}

    # Aggregated metadata.

    first_event = None
    last_event = None
    event_count = None
    mcpot = None
    parents = []
    runs = []
    now = datetime.datetime.now()
    nowstr = datetime.datetime.strftime(now, '%Y-%m-%dT%H:%M:%S+00:00')
    merged_md['start_time'] = nowstr
    merged_md['end_time'] = nowstr
    if cpid != None:
        merged_md['process_id'] = cpid

    # Loop over files.

    files = open(filelist)
    for line in files.readlines():
        filename = line.strip()
        #print('Merging %s' % filename)

        parents.append({'file_name': filename})

        # Get metadata for thie file.

        md = samweb.getMetadata(filename)

        # Loop over metadata keys.

        for key in md.keys():

            # Some keys are ignored or need aggregation.

            if key == 'file_name':
                continue

            if key == 'file_id':
                continue

            if key == 'file_size':
                continue

            if key == 'checksum':
                continue

            if key == 'create_date':
                continue

            if key == 'update_date':
                continue

            if key == 'update_user':
                continue

            if key == 'parents':
                continue

            if key == 'start_time':
                continue

            if key == 'end_time':
                continue

            if key == 'ub_blinding.blind':
                continue

            if key == 'ub_blinding.processed':
                continue

            if key == 'merge.merge' or key == 'merge.merged':
                continue

            if key == 'first_event':
                md_first_event = md[key]
                if first_event == None or md_first_event < first_event:
                    first_event = md_first_event
                continue

            if key == 'last_event':
                md_last_event = md[key]
                if last_event == None or md_last_event > last_event:
                    last_event = md_last_event
                continue

            if key == 'event_count':
                md_event_count = md[key]
                if event_count == None:
                    event_count = md_event_count
                else:
                    event_count += md_event_count
                continue

            if key == 'runs':
                for runid in md[key]:
                    if not runid in runs:
                        runs.append(runid)
                continue

            if key == 'mc.pot':
                if mcpot == None:
                    mcpot = md[key]
                else:
                    mcpot += md[key]
                continue
            
            # Handle nonaggregated metadata keys.

            if not key in merged_md:

                # If this key is not present in merged metadata, just add it.

                #print('Adding key %s.' % key)
                merged_md[key] = md[key]

            elif merged_md[key] == md[key]:

                # Already present matching nonaggregated metadata, do nothing.

                #print('Matching key %s.' % key)
                pass

            else:

                # Nonmatching nonaggregated keys handled here.
                # Some nonmatching keys are allowed.
                # In these cases, accept the first key and ignore the later nonmatching key.

                if key == 'user':
                    continue

                # Don't know what to do with this nonmatching key.

                raise RuntimeError('Duplicate nonmatching key %s.' % key)


    # Add aggregated metadata

    if first_event != None:
        merged_md['first_event'] = first_event
    if last_event != None:
        merged_md['last_event'] = last_event
    if event_count != None:
        merged_md['event_count'] = event_count
    if mcpot != None:
        merged_md['mc.pot'] = mcpot
    if len(runs) > 0:
        merged_md['runs'] = runs
    if len(parents) > 0:
        merged_md['parents'] = parents

    # Done.

    return merged_md

if __name__ == "__main__":

    # Parse arguments.

    if len(sys.argv) < 2:
        print('No file list specified.')
        sys.exit(1)
    filelist = sys.argv[1]
    cpid = None
    if len(sys.argv) > 2:
        cpid = int(sys.argv[2])
    if len(sys.argv) > 3:
        print('Too many arguments.')
        sys.exit(1)
    md = merge_metadata(filelist, cpid)

    # Print metadata as json string.

    print(json.dumps(md, indent=2, sort_keys=True))

    sys.exit(0)	
