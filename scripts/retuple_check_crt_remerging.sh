#!/bin/bash
#------------------------------------------------------------------
#
# Purpose: This script is intended to check if previouse CRT re-merging failed.
#
# Created: Ben Bogart (benbogart777@gmail.com), 10-Dec-2025 
#
#------------------------------------------------------------------

check_config.py --crt
exit_code=$?
echo $exit_code > fetch_merge_dlreco_status.txt

if [ $exit_code -eq 0 ]; then
        echo "Previous CRT remerging was successful"
        PICKED_FHICL="copy"
        echo "0" > crt_status.txt
else
        echo "Previous CRT remerging failed, re-checking now"
        check_crt_merging.sh
fi
