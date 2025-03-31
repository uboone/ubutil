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
#run_number=`lar -c eventdump.fcl $next_stage_input -n 1 | grep "Begin processing the 1st record" | awk '{match($0, /run: ([0-9]+)/, arr); print arr[1]}'`
run_number=`echo $next_stage_input | cut -d '-' -f3`
echo $run_number


TEMPLATE_FHILE="crt_merge_extra_v06_26_01_13"
PICKED_FHICL=""

while read -r crt_status; do
if [ "$crt_status" -eq "0" ]; then
    echo "CRT is OK $crt_status, skip fhicl copy.fcl"
    PICKED_FHICL="copy"
elif [ "$run_number" -ge "3420"  ] && [  "8316" -ge "$run_number"  ];    # in the run1 run number interval
then
        echo "run run1 fhicl copy.fcl"
        PICKED_FHICL="copy"
elif [ "$run_number" -ge "8317"  ] && [  "11048" -ge "$run_number"  ];   # in the run2a run number interval
then
        echo "run run2a fhicl copy.fcl"
        PICKED_FHICL="copy"
elif [ "$run_number" -ge "11049"  ] && [  "13696" -ge "$run_number"  ];   # in the run2b run number interval
then
        echo "run run2b fhicl crt_merge_extra_v06_26_01_26.fcl"
        PICKED_FHICL="crt_merge_extra_v06_26_01_26"
elif [ "$run_number" -ge "13697"  ] && [  "14116" -ge "$run_number"  ];    # in the run3 run number interval
then
        echo "run run3a fhicl crt_merge_extra_v06_26_01_26.fcl"
        PICKED_FHICL="crt_merge_extra_v06_26_01_26"
elif [ "$run_number" -ge "14117"  ] && [  "18960" -ge "$run_number"  ];    # in the run3b run number interval
then
        echo "run run3b fhicl crt_merge_extra_v06_26_01_13.fcl"
        PICKED_FHICL="crt_merge_extra_v06_26_01_13"
elif [ "$run_number" -ge "0018961"  ] && [  "0019752" -ge "$run_number"  ];  # in the run4 run number interval, run4a has four epochs, we may need to split it
then
        echo "run run4a fhicl crt_merge_extra_v06_26_01_13.fcl"
        PICKED_FHICL="crt_merge_extra_v06_26_01_13"
elif [ "$run_number" -ge "0019753"  ] && [  "0021285" -ge "$run_number"  ];  # in the run4 run number interval, run4b has four epochs, we may need to split it
then
        echo "run run4b fhicl crt_merge_extra_v06_26_01_13_33.fcl"
        PICKED_FHICL="crt_merge_extra_v06_26_01_13_33"
elif [ "$run_number" -ge "0021286"  ] && [  "0022269" -ge "$run_number"  ];  # in the run4 run number interval, run4c has four epochs, we may need to split it
then
        echo "run run4c fhicl crt_merge_extra_v06_26_01_13_33.fcl"
        PICKED_FHICL="crt_merge_extra_v06_26_01_13_33"
elif [ "$run_number" -ge "0022270"  ] && [  "0024319" -ge "$run_number"  ];  # in the run4 run number interval, run4d has four epochs, we may need to split it
then
        echo "run run4d fhicl skip copy.fcl"
        PICKED_FHICL="copy"
elif [ "$run_number" -ge "0024320"  ] && [  "0025768" -ge "$run_number"  ];  # in the run5 run number interval
then
        echo "run run5 fhicl skip copy.fcl"
        PICKED_FHICL="copy"
fi
done < crt_status.txt

#cat wrapper.fcl
mv wrapper.fcl backup_wrapper.fcl
cat backup_wrapper.fcl | sed "s/${TEMPLATE_FHILE}/${PICKED_FHICL}/g" > wrapper.fcl
#cat wrapper.fcl

#cat $FCL
#mv $FCL backup_${FCL}.fcl
#cat backup_${FCL}.fcl  | sed "s/${TEMPLATE_FHILE}/${PICKED_FHICL}/g" > $FCL
#cat $FCL

# change the fhicls in all Stage.fcl

echo "List all the Stage.fcl"
ls Stage*fcl

for fhicl_stage in Stage*fcl;
do
#        cat $fhicl_stage
        mv $fhicl_stage backup_${fhicl_stage}.fcl
        cat backup_${fhicl_stage}.fcl  | sed "s/${TEMPLATE_FHILE}/${PICKED_FHICL}/g" > $fhicl_stage
#        cat $fhicl_stage
done

