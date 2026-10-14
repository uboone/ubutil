#!/bin/bash
#------------------------------------------------------------------
#
# Purpose: This script runs merge_dlreco_fnal_data_lantern.sh. 
#          but only if the grid was unable to fetch the dlreco file.
#
# Created: Ben Bogart (benbogart777@gmail.com@fnal.gov), 15-Nov-2025 
#
#------------------------------------------------------------------

# Function for checking if anything exited wrong
check_exit () {
  if [ $? -ne 0 ]; then
    echo "Command failed. Exiting."
    exit 1
  fi
}

# Read the config

reco1def=''

while [ $# -gt 0 ]; do
  case "$1" in

  -d|--def )
    if [ $# -gt 1 ]; then
      echo "Parent reco 1 definition is $2"
      reco1def=$2
      shift
    else
      echo "Bad $1 argument"
      exit 1
    fi
    ;;

  -* )
    echo "Unknown option $1"
    dohelp
    exit 1
    ;;

  * )
    echo "Bad argument $1"
    dohelp
    exit 1
    ;;

  esac
  shift
done

# Check options.

if [ x$reco1def = x ]; then
  echo "No reco1 parent def specified."
  exit 1
fi

# First try to retrive the merged_dlreco file

fetch_merged_dlreco.py
exit_code=$?
echo $exit_code > fetch_merge_dlreco_status.txt

# Get the name of the reco2

inputreco2=`ls -t1 *.root | egrep -v 'celltree|hist|larlite|larcv|Supplemental|TGraphs' | artroot_filter.py | head -n1`
echo inputreco2 $inputreco2
run_number=`lar -c eventdump.fcl $inputreco2 -n 1 | grep "Begin processing the 1st record" | awk '{match($0, /run: ([0-9]+)/, arr); print arr[1]}'`
echo $run_number
# Make sure we got an int
if [[ "$run_number" =~ ^-?[0-9]+$ ]]; then
  # Make sure the run number is sensible
  if [ "$run_number" -le "3419" ]; then
    echo "run number too small, rechecking"
    run_number=`echo $inputreco2 | cut -d '-' -f3`
  elif [ "$run_number" -ge "0025769" ]; then
    echo "run number too big, rechecking"
    run_number=`echo $inputreco2 | cut -d '-' -f3`
  fi
else
  echo "run number is not an integer, rechecking"
  run_number=`echo $inputreco2 | cut -d '-' -f3`
fi
echo $run_number

# Now run Lantern if we need to

fetch_merge_dlreco_status=$(head -n 1 fetch_merge_dlreco_status.txt)
echo fetch_merge_dlreco_status $fetch_merge_dlreco_status
if [ $fetch_merge_dlreco_status -eq 0 ]; then
	echo "Was able to fetch dlreco, will not run Lantern"
else
    rm merged_dlreco.root # Get rid of the old dlreco file that is empty
    # First retrive all parent reco1 files
    reco1filelist=`samweb list-files "isparentof:(file_name=${inputreco2}) and defname:$reco1def"`
    echo reco1filelist $reco1filelist
    # Now get the filepath for each, use dchache if its avalible
    while IFS= read -r filename; do
        echo filename $filename
        file2path=`samweb locate-file $filename`
        echo file2path $file2path
        # Strip off the dache file location if it exists 
        if [[ "$file2path" == *"dcache:"* ]]; then
          file2path00=${file2path#*dcache:}
          echo file2path00 $file2path00
          file2path0=${file2path00%%enstore:*}
          echo file2path0 $file2path0
          file2path1=$(echo "$file2path0" | sed -E 's/([0-9])[^0-9]*$/\1/')
          echo file2path1 $file2path1
        # No dcache location, make sure we have just the file path
        else
          file2path00=${file2path#*:}
          echo file2path00 $file2path00
          file2path0=${file2path00#*:}
          echo file2path0 $file2path0
          file2path1=${file2path0%(*)}
          echo file2path1 $file2path1
        fi
        INFILE=$file2path1/$filename
        echo INFILE $INFILE
        ifdh cp $INFILE reco1input_$filename
        echo ""
    done <<< "$reco1filelist"

    # Rerun the relevant light simulation

    lar -c wirecell_reg4_LightPropTime_LY.fcl -s reco1input_* -o reco1input0.root -n-1
    check_exit
    rm reco1input_*
    lar -c wirecell_detsim_optical_overlay_uboone.fcl -s reco1input0.root -o reco1input1.root -n-1
    check_exit
    rm reco1input0.root
    if [ "$run_number" -ge "0003420"  ] && [  "0011048" -ge "$run_number"  ];    # in the run1 and run 2a run number interval; before full CRT
    then
        lar -c standard_overlay_optical_uboone.fcl -s reco1input1.root -o reco1input2.root -n-1
        check_exit
    elif [ "$run_number" -ge "0011049"  ] && [  "0025769" -ge "$run_number"  ];   # run 2b and later; after full CRT
    then
        lar -c standard_overlay_notpc_uboone.fcl -s reco1input1.root -o reco1input2.root -n-1
        check_exit
    else
        echo "WARNING, too big run number detected"
        echo "Defaulting to standard_overlay_notpc_uboone.fcl"
        lar -c standard_overlay_notpc_uboone.fcl -s reco1input1.root -o reco1input2.root -n-1
        check_exit
    fi
    rm reco1input1.root

    # Re-run WC to get the needed Lantern input

    mv reco1input2.root reco1input2_temp.root
    lar -c run_celltreeub_overlay_port_prod.fcl -s reco1input2_temp.root -n-1
    check_exit
    metadata=$(samweb get-metadata $inputreco2)
    evc=$(echo $metadata | grep -oP 'Event Count: \K\d+')
    cat <<EOF > celltreeOVERLAY.root.json
{
  "event_count": ${evc},
}
EOF
    bash fully_unified_reco2_wirecell.sh
    check_exit
    touch updated_run_slimmed_port_overlay_sp.fcl
    cat <<EOF > updated_run_slimmed_port_overlay_sp.fcl
#include "run_slimmed_port_overlay_sp.fcl"
physics.producers.nuselMetrics.PortInput:                 "./WCPwork/merge.root"
physics.producers.portedFlash.PortInput:                  "./WCPwork/merge.root"
physics.producers.portedSpacePointsThreshold.PortInput:   "./WCPwork/merge.root"
physics.producers.portedThresholdhit.PortInput:           "./WCPwork/merge.root"
EOF
    lar -c updated_run_slimmed_port_overlay_sp.fcl -s reco1input2_temp.root -o reco1input2.root -n-1
    check_exit
    rm reco1input2_temp.root

    # Rerun Lantern

    lar -c mcc10_dlreco_w_wirecell_driver_overlay_lantern_set1.fcl -s reco1input2.root -n-1
    check_exit
    lar -c mcc10_dlreco_w_wirecell_driver_overlay_lantern_set2.fcl -s reco1input2.root -n-1
    check_exit
    lar -c mcc10_dlreco_w_wirecell_driver_overlay_lantern_set3.fcl -s reco1input2.root -n-1
    check_exit
    lar -c mcc10_dlreco_w_wirecell_driver_overlay_lantern_set4.fcl -s reco1input2.root -n-1
    check_exit
    lar -c mcc10_dlreco_w_wirecell_driver_overlay_lantern_set5.fcl -s reco1input2.root -n-1
    check_exit
    rm reco1input*
    bash merge_dlreco_fnal_overlay_and_mc_lantern_multiStage.sh
    check_exit

fi





