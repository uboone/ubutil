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

# Grab the fhicl name and change it to the right run
TEMPLATE_FHILE=$(head -n 1 $FCL)
TEMPLATE_FHILE="${TEMPLATE_FHILE%%.*}"
TEMPLATE_FHILE="${TEMPLATE_FHILE#*\"}"
PICKED_FHICL=$TEMPLATE_FHILE
if [ "$run_number" -ge "3420"  ] && [  "8316" -ge "$run_number"  ];    # in the run1 run number interval
then
        echo "Using run1 wiremod fhicl"
	PICKED_FHICL=$(echo "$TEMPLATE_FHILE" | sed -E "s/run([0-9]+)/run1/g")
elif [ "$run_number" -ge "8317"  ] && [  "11048" -ge "$run_number"  ];   # beyond run1, so use the run3 fhicl
then
        echo "Using run3 wiremod fhicl"
        PICKED_FHICL=$(echo "$TEMPLATE_FHILE" | sed -E "s/run([0-9]+)/run3/g")
fi


mv wrapper.fcl backup_wrapper.fcl
cat backup_wrapper.fcl | sed "s/${TEMPLATE_FHILE}/${PICKED_FHICL}/g" > wrapper.fcl

for fhicl_stage in Stage*fcl;
do
        mv $fhicl_stage backup_${fhicl_stage}.fcl
        cat backup_${fhicl_stage}.fcl  | sed "s/${TEMPLATE_FHILE}/${PICKED_FHICL}/g" > $fhicl_stage
done

