#!/bin/bash
#------------------------------------------------------------------
#
# Purpose: Following the copy.fcl to check the crt status
#          
#
# Created: Liang Liu (liangliu@fnal.gov), 25-Nov-2024 
#
#------------------------------------------------------------------


# Make sure batch environment variables needed by this script are defined.

# get the file that will be used as input for next stage
next_stage_input=`ls -t1 *.root | egrep -v 'celltree|hist|larlite|larcv|Supplemental|TGraphs' | head -n1`
echo $next_stage_input
run_number=`lar -c eventdump.fcl $next_stage_input -n 1 | grep "Begin processing the 1st record" | awk '{match($0, /run: ([0-9]+)/, arr); print arr[1]}'`
echo $run_number

input_file=''
# try to get metadata of input file
samweb get-metadata $next_stage_input
if [ $? -eq 0 ]; then
echo "Get the correct input file name"
input_file=$next_stage_input
else
echo "Try to revert the input file name from ${next_stage_input} to ${next_stage_input:0:-28}.root"
input_file=${next_stage_input:0:-28}.root
mv $next_stage_input ${input_file}
fi

samweb get-metadata ${input_file}

if [ $? -eq 0 ]; then
echo "Input file name correct: ${input_file}"
else
echo "Input file name is wrong: ${input_file}"
exit 1
fi
#echo ${next_stage_input:0:-28}.root
echo ${input_file}

ifdh cp /pnfs/uboone/resilient/users/liangliu/crt/check_crt_merge.py . 
chmod u+x check_crt_merge.py
python check_crt_merge.py -f ${input_file}

#mv $next_stage_input ${next_stage_input:0:-28}.root

crt_status=$?
echo "the crt status $crt_status"

echo "$crt_status" > crt_status.txt

