#! /usr/bin/env python
###############################################################################
#
# Name: sam_metadata.py
# 
# Purpose: Extract per-job experiment-specific sam metadata from services
#          configuration.  Use the configuration of the following services.
#
#          1.  FileCatalogMetadataMicroBooNE.
#          2.  TFileMetadataMicroBooNE
#
# Created: 12-Apr-2017, H. Greenlee
#
###############################################################################
import sys, os
from root_analyze import RootAnalyze

def make(config):
    #----------------------------------------------------------------------
    #
    # Purpose: Factory function.
    #
    # Arguments: config - FCL configuration.
    #
    # Returns: Instance of class SamMetadata.
    #
    #----------------------------------------------------------------------

    obj = SamMetadata(config)
    return obj

# Sam metadata class

class SamMetadata(RootAnalyze):

    def __init__(self, pset):
        #----------------------------------------------------------------------
        #
        # Purpose: Constructor.
        #
        # Arguments: pset - FCL configuration.
        #
        # In the constructor, we extract per-job experiment-specific sam metadata
        # from the fcl configuration of the following art services.
        #
        # 1.  FileCatalogMetadataMicroBooNE.
        # 2.  TFileMetadataMicroBooNE.
        #
        # The extracted metadata is stashed away as a class data member, and
        # returned to the framework via function end_job.
        #
        #----------------------------------------------------------------------

        # Metadata object data member (dictionary).

        self.metadata = {}

        # Extract information from services configuration and update metadata.

        if pset.has_key('services'):
            services = pset['services']

            # Extract parameters from FileCatalogMetadataMicroBooNE.

            if services.has_key('FileCatalogMetadataMicroBooNE'):
                fcm_uboone = services['FileCatalogMetadataMicroBooNE']
                if fcm_uboone.has_key('FCLName'):
                    self.metadata['fcl.name'] = fcm_uboone['FCLName']
                if fcm_uboone.has_key('FCLVersion'):
                    self.metadata['fcl.version'] = fcm_uboone['FCLVersion']
                if fcm_uboone.has_key('ProjectName'):
                    self.metadata['ub_project.name'] = fcm_uboone['ProjectName']
                if fcm_uboone.has_key('ProjectStage'):
                    self.metadata['ub_project.stage'] = fcm_uboone['ProjectStage']
                if fcm_uboone.has_key('ProjectVersion'):
                    self.metadata['ub_project.version'] = fcm_uboone['ProjectVersion']

            # Extract parameters from TFileMetadataMicroBooNE.

            if services.has_key('TFileMetadataMicroBooNE'):
                tfm_uboone = services['TFileMetadataMicroBooNE']
                if tfm_uboone.has_key('dataTier'):
                    self.metadata['data_tier'] = tfm_uboone['dataTier']
                if tfm_uboone.has_key('fileFormat'):
                    self.metadata['file_format'] = tfm_uboone['fileFormat']        

        # Done.

        return


    def branches(self, tree):
        #----------------------------------------------------------------------
        #
        # Purpose: Return list of branches we want read for this tree, namely, none.
        #
        # Arguments: tree - TTree object (ignored).
        #
        # Returns: Empty list.
        #
        #----------------------------------------------------------------------

        return []


    def end_job(self):
        #----------------------------------------------------------------------
        #
        # Purpose: End job.  Return saved metadata.
        #
        # Returns: Metadata.
        #
        #----------------------------------------------------------------------

        return self.metadata



