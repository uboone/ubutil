#!/bin/bash
#------------------------------------------------------------------
#
# Purpose: This script runs the standalone CRT reconstruction. 
#          but only if the previouse attempt on the file failed.
#
# Created: Ben Bogart (benbogart777@gmail.com@fnal.gov), 15-Nov-2025 
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


TEMPLATE_FHILE=$(head -n 1 $FCL)
TEMPLATE_FHILE="${TEMPLATE_FHILE%%.*}"
TEMPLATE_FHILE="${TEMPLATE_FHILE#*\"}"
PICKED_FHICL=$TEMPLATE_FHILE

crt_status=$(head -n 1 crt_status.txt)
if [ $crt_status -eq 0 ]; then
	echo "Previouse CRT re-merging was good, will not run the standalone reconstruction."
        PICKED_FHICL="copy"
fi

echo $TEMPLATE_FHILE
echo $PICKED_FHICL

mv wrapper.fcl backup_wrapper_crt_reco.fcl
cat backup_wrapper_crt_reco.fcl | sed "s/${TEMPLATE_FHILE}/${PICKED_FHICL}/g" > wrapper.fcl
for fhicl_stage in Stage*fcl;
do
        mv $fhicl_stage backup_crt_reco_${fhicl_stage}.fcl
        cat backup_crt_reco_${fhicl_stage}.fcl  | sed "s/${TEMPLATE_FHILE}/${PICKED_FHICL}/g" > $fhicl_stage
done
