#!/usr/bin/env python
#----------------------------------------------------------------------
#
# Name: experiment_utilities.py
#
# Purpose: A python module containing various experiment-specific
#          python utility functions.
#
# Created: 28-Oct-2013  H. Greenlee
#
#----------------------------------------------------------------------

from __future__ import absolute_import
from __future__ import print_function
import os
import larbatch_posix

# Don't fail (on import) if samweb is not available.

try:
    import samweb_cli
except ImportError:
    pass

def get_dropbox(filename):

    # Get metadata.

    md = {}
    exp = 'uboone'
    if 'SAM_EXPERIMENT' in os.environ:
        exp = os.environ['SAM_EXPERIMENT']
    samweb = samweb_cli.SAMWebClient(experiment=exp)
    try:
        md = samweb.getMetadata(filenameorid=filename)
    except:
        pass

    # Extract the metadata fields that we need.
    
    file_format = ''
    file_type = ''
    group = ''
    data_tier = ''
    size = 0
    run = 0
    subrun = 0
    merge = 0

    if 'file_format' in md:
        file_format = md['file_format']
    if 'file_type' in md:
        file_type = md['file_type']
    if 'group' in md:
        group = md['group']
    if 'data_tier' in md:
        data_tier = md['data_tier']
    if 'file_size' in md:
        size = md['file_size']
    if 'runs' in md:
        runs = md['runs']
        if len(runs) > 0:
            runid = runs[0]
            if len(runid) > 1:
                run = runid[0]
                subrun = runid[1]
    if 'merge.merge' in md:
        merge = md['merge.merge']

    if not file_type or not group or not data_tier:
        raise RuntimeError('Missing or invalid metadata for file %s.' % filename)

    # Construct dropbox path.

    #path = '/uboone/data/uboonepro/dropbox/%s/%s/%s' % (file_type, group, data_tier)
    if 'FTS_DROPBOX' in os.environ:
        dropbox_root = os.environ['FTS_DROPBOX']
    else:
        dropbox_root = '/pnfs/uboone/scratch/uboonepro/dropbox'
    if merge and size < 1000000000 and (file_format == 'artroot' or file_format == 'root'):
        dropbox_root = '%s/merge' % dropbox_root
    path = '%s/%s/%s/%s' % (dropbox_root, file_type, group, data_tier)

    # Make sure path exists.

    if not larbatch_posix.exists(path):
        larbatch_posix.makedirs(path)
        larbatch_posix.chmod(path, 0o775)

    # Add run number to path.

    if type(run) == type(0):
        path = '%s/%d' % (path, run % 100)
        if not larbatch_posix.exists(path):
            larbatch_posix.mkdir(path)
            larbatch_posix.chmod(path, 0o775)

    # Add subrun number to path.

    if type(subrun) == type(0):
        path = '%s/%d' % (path, subrun % 100)
        if not larbatch_posix.exists(path):
            larbatch_posix.mkdir(path)
            larbatch_posix.chmod(path, 0o775)

    return path

# Return fcl configuration for experiment-specific sam metadata.

def get_sam_metadata(project, stage):
    result = 'services.FileCatalogMetadataMicroBooNE: {\n'
    if type(stage.fclname) == type(b'') or type(stage.fclname) == type(u''):
        result = result + '  FCLName: "%s"\n' % os.path.basename(stage.fclname)
    else:
        result = result + '  FCLName: "'
        for fcl in stage.fclname:
            result = result + '%s/' % os.path.basename(fcl)
        result = result[:-1]
        result = result + '"\n' 
    result = result + '  FCLVersion: "%s"\n' % project.release_tag
    result = result + '  ProjectName: "%s"\n' % project.name
    result = result + '  ProjectStage: "%s"\n' % stage.name
    result = result + '  ProjectVersion: "%s"\n' % project.version
    if stage.merge == '1':
        result = result + '  Merge: 1\n'
    if hasattr(stage, 'mixparents'):
        n=0
        for mixparent in stage.mixparents:
            if n == 0:
                result = result + '  Parameters: [ '
            else:
                result = result + ',\n                '
            result = result + '"mixparent%d", "%s"' % (n, mixparent)
            n += 1
        result = result + ' ]\n'
    result = result + '}\n'
    result = result + 'services.TFileMetadataMicroBooNE: @local::microboone_tfile_metadata\n'
    if hasattr(stage,'anamerge') and stage.anamerge == '1':
        result = result + 'services.TFileMetadataMicroBooNE.Merge:  @local::microboone_tfile_metadata.GenerateTFileMetadata\n'

    return result

# Function to return path to the setup_uboone.sh script

def get_setup_script_path():

    CVMFS_DIR="/cvmfs/uboone.opensciencegrid.org/products/"
    UBUTIL_DIR=''
    if 'UBUTIL_DIR' in os.environ:
        UBUTIL_DIR=os.environ['UBUTIL_DIR'] + '/bin/'

    if os.path.isfile(CVMFS_DIR+"setup_uboone.sh"):
        setup_script = CVMFS_DIR+"setup_uboone.sh"
    elif UBUTIL_DIR != '' and os.path.isfile(UBUTIL_DIR+"setup_uboone.sh"):
        setup_script = UBUTIL_DIR+"setup_uboone.sh"
    else:
        raise RuntimeError("Could not find setup script at "+CVMFS_DIR)

    return setup_script

# Construct dimension string for project, stage.

def dimensions(project, stage, ana=False):

    data_tier = ''
    if ana:
        data_tier = stage.ana_data_tier
    else:
        data_tier = stage.data_tier
    dim = 'file_type %s' % project.file_type
    dim = dim + ' and data_tier %s' % data_tier
    dim = dim + ' and ub_project.name %s' % project.name
    dim = dim + ' and ub_project.stage %s%%' % stage.name
    dim = dim + ' and ub_project.version %s' % project.version
    if stage.pubs_output:
        first_subrun = True
        for subrun in stage.output_subruns:
            if first_subrun:
                dim = dim + ' and run_number %d.%d' % (stage.output_run, subrun)
                first_subrun = False

                # Kluge to pick up mc files with wrong run number.

                if stage.output_run > 1 and stage.output_run < 100:
                    dim = dim + ',1.%d' % subrun
            else:
                dim = dim + ',%d.%d' % (stage.output_run, subrun)
    elif project.run_number != 0:
        dim = dim + ' and run_number %d' % project.run_number
    dim = dim + ' and availability: anylocation'


    return dim


# Function to strip enclosing single- or double-quote characters from a string.

def unquote(s):
    result = s
    if len(s) >= 2 and \
       ((s.startswith('\'') and s.endswith('\'')) or \
        (s.startswith('"') and s.endswith('"'))):
        result = s[1:-1]

    # Done.

    return result


# Function to perform validation check before submitting batch jobs.
# Return True if good, False if bad.

def validate_stage(project, stage):

    result = True

    # Check recursive dataset, if any, definition here.
    # These checks are intended to detect common mistakes.

    if stage.recur and stage.inputdef != '' and stage.basedef != '' and \
       (stage.recurtype == 'child' or stage.recurtype == 'anachild'):
        print('Checking recursive definition %s' % stage.inputdef)

        # Extract description

        exp = 'uboone'
        if 'SAM_EXPERIMENT' in os.environ:
            exp = os.environ['SAM_EXPERIMENT']
        samweb = samweb_cli.SAMWebClient(experiment=exp)
        desc = samweb.descDefinition(defname=stage.inputdef)
        n = desc.find('Dimensions:')
        if n > 0:
            words = desc[n+12:].split()

            # Extract the first "minus isparentof:" clause, if any

            first = -1
            last = -1
            for i in range(len(words)):
                if words[i] == 'minus' and words[i+1].startswith('isparentof:'):
                    first = i+2
                if words[i] == ')' and last < 0:
                    last = i

            if first >= 0 and last > first:

                # Extract project (name, stage, version).

                clause = words[first:last]
                pname = ''
                pstage = ''
                pversion = ''
                for i in range(len(clause)-1):
                    if clause[i] == 'ub_project.name':
                        pname = unquote(clause[i+1])
                    if clause[i] == 'ub_project.stage':
                        pstage = unquote(clause[i+1])
                    if clause[i] == 'ub_project.version':
                        pversion = unquote(clause[i+1])

                # Check whether project (name, stage, version) are compatible.

                if pname != '' and project.name != '' and pname != project.name:
                    print('Project name is incompatible with recursive dataset.')
                    print('This project name = %s' % project.name)
                    print('Recursive dataset project name = %s' % pname)
                    result = False

                if pstage != '' and stage.name != '' and \
                   pstage != stage.name and pstage != '%s%%' % stage.name:
                    print('Stage name is incompatible with recursive dataset.')
                    print('This stage name = %s' % stage.name)
                    print('Recursive dataset stage name = %s' % pstage)
                    result = False

                if pversion != '' and project.version != '' and pversion != project.version:
                    print('Project version is incompatible with recursive dataset.')
                    print('This project version = %s' % project.version)
                    print('Recursive dataset project version = %s' % pversion)
                    result = False

    # Done.

    return result


class MetaDataKey:

   def __init__(self):
     self.expname = "ub"

   def metadataList(self):
     result = [self.expname + elt for elt in ('ProjectName', 'ProjectStage', 'ProjectVersion')]
     result.extend(['merge', 'merged'])
     return result


   def translateKey(self, key):
     if key.startswith('merge'):
       return 'merge.%s' % key
     else:
       prefix = key[:2]
       stem = key[2:]
       projNoun = stem.split("Project")
       return prefix + "_Project." + projNoun[1]
