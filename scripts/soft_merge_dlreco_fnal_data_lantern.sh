#!/bin/bash
#------------------------------------------------------------------
#
# Purpose: This script runs merge_dlreco_fnal_data_lantern.sh. 
#          but only if the grid was unable to fetch the dlreco file.
#
# Created: Ben Bogart (benbogart777@gmail.com@fnal.gov), 15-Nov-2025 
#
#------------------------------------------------------------------

fetch_merge_dlreco_status=$(head -n 1 fetch_merge_dlreco_status.txt)
if [ $fetch_merge_dlreco_status -eq 0 ]; then
	echo "Was able to fetch dlreco, will not run merge_dlreco_fnal_data_lantern.sh"
else
        bash merge_dlreco_fnal_data_lantern.sh
fi
