#!/bin/bash
#------------------------------------------------------------------
#
# Purpose: This script switches Lantern weights based on the run number
#
# Created: Ben Bogart (benbogart777@gmail.com), 11-Dec-2025 
#
#------------------------------------------------------------------

# get the file that will be used as input for next stage
next_stage_input=`ls -t1 *.root | egrep -v 'celltree|hist|larlite|larcv|Supplemental|TGraphs' | artroot_filter.py | head -n1`
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

if [ "$run_number" -ge "13697"  ] && [  "18960" -ge "$run_number"  ];   # run 3
then
        echo "Using alternate Lantern weights."
        launch_lantern_container_data_unified_altLArPIDWeights.sh
        if [ $? -ne 0 ]; then
        echo "Lantern container failed. Exiting."
        exit 1
        fi
else 
        echo "Using standard Lantern weights."
        launch_lantern_container_data_unified.sh
        if [ $? -ne 0 ]; then
        echo "Lantern container failed. Exiting."
        exit 1
        fi
fi
