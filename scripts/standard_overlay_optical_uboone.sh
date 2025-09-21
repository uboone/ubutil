#!/bin/bash
#------------------------------------------------------------------
#
# Purpose: This script is intended to update the configuration
#          of the fhicl according to run number.
#
# Created: Liang Liu (liangliu@fnal.gov), 25-Nov-2024 
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

# get the file that will be used as input for next stage
next_stage_input=`ls -t1 *.root | egrep -v 'celltree|hist|larlite|larcv|Supplemental|TGraphs' | head -n1`
echo $next_stage_input
run_number=`lar -c eventdump.fcl $next_stage_input -n 1 | grep "Begin processing the 1st record" | awk '{match($0, /run: ([0-9]+)/, arr); print arr[1]}'`
echo $run_number
# Make sure we got an int
if [[ "$run_number" =~ ^-?[0-9]+$ ]]; then
  # Make sure the run number is sensible
  if [ "$run_number" -le "3419" ]; then
    echo "run number too small, rechecking"
    run_number=`echo $next_stage_input | cut -d '-' -f3`
  elif [ "$run_number" -ge "0025769" ]; then
    echo "run number too big, rechecking"
    run_number=`echo $next_stage_input | cut -d '-' -f3`
  fi
else
  echo "run number is not an integer, rechecking"
  run_number=`echo $next_stage_input | cut -d '-' -f3`
fi
echo $run_number

if [ "$run_number" -ge "0003420"  ] && [  "0011048" -ge "$run_number"  ];    # in the run1 and run 2a run number interval; before full CRT
then
        echo "run run1 fhicl"
        cat $FCL
        mv $FCL backup_${FCL}.fcl
        cat backup_${FCL}.fcl  | sed "s/standard_overlay_optical_uboone/standard_overlay_optical_uboone/g" > $FCL
        cat $FCL
        cat wrapper.fcl
        mv wrapper.fcl backup_wrapper.fcl
        cat backup_wrapper.fcl | sed "s/standard_overlay_optical_uboone/standard_overlay_optical_uboone/g" > wrapper.fcl
        cat wrapper.fcl
elif [ "$run_number" -ge "0011049"  ] && [  "0025769" -ge "$run_number"  ];   # run 2b and later; after full CRT
then
        echo "run run2 fhicl"
        cat $FCL
        mv $FCL backup_${FCL}.fcl
        cat backup_${FCL}.fcl  | sed "s/standard_overlay_optical_uboone/standard_overlay_notpc_uboone/g" > $FCL
        cat $FCL
        cat wrapper.fcl
        mv wrapper.fcl backup_wrapper.fcl
        cat backup_wrapper.fcl | sed "s/standard_overlay_optical_uboone/standard_overlay_notpc_uboone/g" > wrapper.fcl
        cat wrapper.fcl
fi

