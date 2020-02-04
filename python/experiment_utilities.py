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
    if os.environ.has_key('SAM_EXPERIMENT'):
        exp = os.environ['SAM_EXPERIMENT']
    samweb = samweb_cli.SAMWebClient(experiment=exp)
    try:
        md = samweb.getMetadata(filenameorid=filename)
    except:
        pass

    # Extract the metadata fields that we need.
    
    file_type = ''
    group = ''
    data_tier = ''
    run=0
    subrun=0

    if md.has_key('file_type'):
        file_type = md['file_type']
    if md.has_key('group'):
        group = md['group']
    if md.has_key('data_tier'):
        data_tier = md['data_tier']
    if md.has_key('runs'):
        runs = md['runs']
        if len(runs) > 0:
            runid = runs[0]
            if len(runid) > 1:
                run = runid[0]
                subrun = runid[1]

    if not file_type or not group or not data_tier:
        raise RuntimeError('Missing or invalid metadata for file %s.' % filename)

    # Construct dropbox path.

    #path = '/uboone/data/uboonepro/dropbox/%s/%s/%s' % (file_type, group, data_tier)
    if os.environ.has_key('FTS_DROPBOX'):
        dropbox_root = os.environ['FTS_DROPBOX']
    else:
        dropbox_root = '/pnfs/uboone/scratch/uboonepro/dropbox'
    path = '%s/%s/%s/%s' % (dropbox_root, file_type, group, data_tier)

    # Make sure path exists.

    if not larbatch_posix.exists(path):
        larbatch_posix.makedirs(path)
        larbatch_posix.chmod(path, 0775)

    # Add run number to path.

    if type(run) == type(0):
        path = '%s/%d' % (path, run % 1000)
        if not larbatch_posix.exists(path):
            larbatch_posix.mkdir(path)
            larbatch_posix.chmod(path, 0775)

    # Add subrun number to path.

    if type(subrun) == type(0):
        path = '%s/%d' % (path, subrun % 1000)
        if not larbatch_posix.exists(path):
            larbatch_posix.mkdir(path)
            larbatch_posix.chmod(path, 0775)

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
    result = result + '}\n'
    result = result + 'services.TFileMetadataMicroBooNE: @local::microboone_tfile_metadata\n'

    return result

# Function to return path to the setup_uboone.sh script

def get_setup_script_path():

    CVMFS_DIR="/cvmfs/uboone.opensciencegrid.org/products/"
    UBUTIL_DIR=''
    if os.environ.has_key('UBUTIL_DIR'):
        UBUTIL_DIR=os.environ['UBUTIL_DIR'] + '/bin/'

    if os.path.isfile(CVMFS_DIR+"setup_uboone.sh"):
        setup_script = CVMFS_DIR+"setup_uboone.sh"
    elif os.path.isfile(FERMIAPP_DIR+"setup_uboone.sh"):
        setup_script = FERMIAPP_DIR+"setup_uboone.sh"
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
    dim = dim + ' and ub_project.stage %s' % stage.name
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


class MetaDataKey:

   def __init__(self):
     self.expname = "ub"

   def metadataList(self):
     return [self.expname + elt for elt in ('ProjectName', 'ProjectStage', 'ProjectVersion')]


   def translateKey(self, key):
     prefix = key[:2]
     stem = key[2:]
     projNoun = stem.split("Project")
     return prefix + "_Project." + projNoun[1]
