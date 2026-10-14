#! /bin/bash
#==========================================================================
#
# Name: merge_hist.sh
#
# Purpose: This is a script for merging stage 1 and stage 2 dqm
#          histogram files in batch jobs.  It is intended to be run as
#          an end of job script.  It does not accept any arguments.
#
#          Histogram files to be merged are identified by having names
#          matching wildcard reco_stage_[12]_hist.root.  The merged
#          histogram file is named reco_stage_12_hist.root, and the
#          stage 1 json file, if any, is renamed to match the merged
#          root file.
#
#          Original unmerged histogram and json files are deleted.
#
# Created: 20-Nov-2017  H. Greenlee
# 
#==========================================================================

if [ -f reco_stage_1_hist.root -a -f reco_stage_2_hist.root ]; then

  # Merge histogram root files.

  hadd reco_stage_12_hist.root reco_stage_1_hist.root reco_stage_2_hist.root

  # Rename stage 1 json file.

  if [ -f reco_stage_1_hist.root.json ]; then
    mv reco_stage_1_hist.root.json reco_stage_12_hist.root.json
  fi

  # Delete original histogram and json files.

  rm -f reco_stage_1_hist.root
  rm -f reco_stage_2_hist.root
  rm -f reco_stage_2_hist.root.json
fi
