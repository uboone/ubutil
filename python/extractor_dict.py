#!/usr/bin/env python
import sys, getopt
import os
import subprocess
from subprocess import Popen, PIPE
import threading
import Queue
import time
import ast
import root_metadata
import json

# Function to wait for a subprocess to finish and fetch return code,
# standard output, and standard error.
# Call this function like this:
#
# q = Queue.Queue()
# jobinfo = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
# wait_for_subprocess(jobinfo, q)
# rc = q.get()      # Return code.
# jobout = q.get()  # Standard output
# joberr = q.get()  # Standard error


def wait_for_subprocess(jobinfo, q):
    jobout, joberr = jobinfo.communicate()
    rc = jobinfo.poll()
    q.put(rc)
    q.put(jobout)
    q.put(joberr)
    return

# Get metadata from input file and return as python dictionary.

def getmetadata(inputfile, md0={}):

    # Extract metadata into a pipe.
    proc = subprocess.Popen(["sam_metadata_dumper", inputfile],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    q = Queue.Queue()
    thread = threading.Thread(target=wait_for_subprocess, args=[proc, q])
    thread.start()
    thread.join(timeout=60)
    if thread.is_alive():
        print 'Terminating subprocess because of timeout.'
        proc.terminate()
        thread.join()
    rc = q.get()
    jobout = q.get()
    joberr = q.get()
    if rc != 0:
        raise RuntimeError, 'sam_metadata_dumper returned nonzero exit status %d.' % rc
	
    # Decode output from sam_metadata_dumper as json text.
    # Add some fixes and workarounds here.
    # Extract mix parents before conversion to json.

    mdtext=''
    mixparents = []
    for line in jobout.split('\n'):
        fields = line.split(':')
        if fields[0].find('mixparent') >= 0 and len(fields) >= 2:
            mixparents.append(fields[1].strip(' ,"'))
        else:
            if line[-3:-1] != ' ,':
                mdtext = mdtext + line.replace(", ,",",")
    mdtop = json.JSONDecoder().decode(mdtext)
    if len(mdtop.keys()) == 0:
        print 'No top-level key in extracted metadata.'
        sys.exit(1)
    file_name = mdtop.keys()[0]
    mdart = mdtop[file_name]

    # define an empty python dictionary which will hold sam metadata.
    # Some fields can be copied directly from art metadata to sam metadata.
    # Other fields require conversion.
    md = {}

    # Loop over art metadata.
    for mdkey in mdart.keys():
        mdval = mdart[mdkey]

        # Skip some art-specific fields.

        if mdkey == 'file_format_version':
            pass
        elif mdkey == 'file_format_era':
            pass

        # Ignore primary run_type field (if any).
        # Instead, get run_type from runs field.

        elif mdkey == 'run_type':
            pass

        # Ignore data_stream if it begins with "out".
        # These kinds of stream names are probably junk module labels.

        elif mdkey == 'data_stream' and mdval[:3] == 'out' and \
                mdval[3] >= '0' and mdval[3] <= '9':
            pass

        # Application family/name/version.

        elif mdkey == 'applicationFamily':
            if not md.has_key('application'):
                md['application'] = {}
            md['application']['family'] = mdval
        elif mdkey == 'process_name':
            if not md.has_key('application'):
                md['application'] = {}
            md['application']['name'] = mdval
        elif mdkey == 'applicationVersion':
            if not md.has_key('application'):
                md['application'] = {}
            md['application']['version'] = mdval

        # Parents.

        elif mdkey == 'parents':
            mdparents = []
            for parent in mdval:
                parent_dict = {'file_name': parent}
                mdparents.append(parent_dict)
            md['parents'] = mdparents

        # Other fields where the key or value requires minor conversion.

        elif mdkey == 'first_event':
            md[mdkey] = mdval[2]
        elif mdkey == 'last_event':
            md[mdkey] = mdval[2]
        elif mdkey == 'ubProjectName':
            md['ub_project.name'] = mdval
        elif mdkey == 'ubProjectStage':
            md['ub_project.stage'] = mdval
        elif mdkey == 'ubProjectVersion':
            md['ub_project.version'] = mdval
        elif mdkey == 'fclName':
            md['fcl.name'] = mdval
        elif mdkey == 'fclVersion':
            md['fcl.version']  = mdval

        # For all other keys, copy art metadata directly to sam metadata.
        # This works for run-tuple (run, subrun, runtype) and time stamps.

        else:
            md[mdkey] = mdart[mdkey]

    # Merge mix parents into normal parents.

    for mixparent in mixparents:
        mixparent_dict = {'file_name': mixparent}
        md['parents'].append(mixparent_dict)

    # Get the other meta data field parameters
    md['file_name'] =  inputfile.split("/")[-1]
    if md0.has_key('file_size'):
        md['file_size'] = md0['file_size']
    else:
        md['file_size'] =  os.path.getsize(inputfile)
    if md0.has_key('crc'):
        md['crc'] = md0['crc']
    else:
        md['crc'] = root_metadata.fileEnstoreChecksum(inputfile)
    return md

if __name__ == "__main__":
    md = getmetadata(str(sys.argv[1]))
    #print md	
    mdtext = json.dumps(md, indent=2, sort_keys=True)
    print mdtext
    sys.exit(0)	
