#!/bin/bash
#------------------------------------------------------------------
#
# Purpose: This script runs merge_dlreco_fnal_data_lantern.sh. 
#          but only if the grid was unable to fetch the dlreco file.
#
# Created: Ben Bogart (benbogart777@gmail.com@fnal.gov), 23-May-2026 
#
#------------------------------------------------------------------

# Read the config

deffiletype=''

while [ $# -gt 0 ]; do
  case "$1" in

  -t|--filetype )
    if [ $# -gt 1 ]; then
      echo "Defining WireCell DetVar filetype to be $2"
      deffiletype=$2
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

if [ x$deffiletype = x ]; then
  echo "No WireCell DetVar filetype specified."
  exit 1
fi

echo $deffiletype > $deffiletype.fcl

exit 0
