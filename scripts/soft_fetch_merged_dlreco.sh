#!/bin/bash
#------------------------------------------------------------------
#
# Purpose: This script is intended to try to retrive the dlreco file.
#          If this fails, Lantern will be re-run.
#
# Created: Ben Bogart (benbogart777@gmail.com), 15-Nov-2025 
#
#------------------------------------------------------------------

# Make sure batch environment variables needed by this script are defined.

echo $FCL

if [ x$FCL = x ]; then
  echo "Variable FCL not defined."
  exit 1
fi

# Make sure fcl file $FCL exists.
if [ ! -f $FCL ]; then
  echo "Fcl file $FCL does not exist."
  exit 1
fi

# First try to retrive the merged_dlreco file

fetch_merge_dlreco.py
exit_code=$?
echo $exit_code > fetch_merge_dlreco_status.txt

# If it failed, then we need to re-run Lantern
TEMPLATE_FHILE=$(head -n 1 $FCL)
TEMPLATE_FHILE="${TEMPLATE_FHILE%%.*}"
TEMPLATE_FHILE="${TEMPLATE_FHILE#*\"}"
PICKED_FHICL=$TEMPLATE_FHILE
if [ $exit_code -eq 0 ]; then
        echo "The dlreco file was fetched successfully."
        PICKED_FHICL="copy"
fi

echo $TEMPLATE_FHILE
echo $PICKED_FHICL

mv wrapper.fcl backup_wrapper.fcl
cat backup_wrapper.fcl | sed "s/${TEMPLATE_FHILE}/${PICKED_FHICL}/g" > wrapper.fcl
for fhicl_stage in Stage*fcl;
do
        mv $fhicl_stage backup_${fhicl_stage}.fcl
        cat backup_${fhicl_stage}.fcl  | sed "s/${TEMPLATE_FHILE}/${PICKED_FHICL}/g" > $fhicl_stage
done
