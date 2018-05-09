#! /bin/bash
#------------------------------------------------------------------
#
# Name: prepare_crt_merge.sh
#
# Purpose: Check snapshot or dataset to ensure that matching crt
#          swizzled data files are available and prestaged.
#
# Usage:
#
# prepare_crt_merge.sh [-h|--help] [-v|--version <version>] [--prestage] [--defname <defname>|--snapshot_id <snapshot id>]
#
# Options:
#
# -h|--help              - Print help message.
# -v|--version <version> - Swizzled crt file version.
# --prestage             - Prestage matching crt files.
# --defname              - TPC dataset definition
# --snapshot_id          - TPC snapshot id
#
# Usage notes:
#
# 1.  This script looks for matching swizzled crt files by querying
#     for files that match the start and end times of all files in
#     the TPC snapshot or dataset.  Success is defined as finding six
#     matching crt files for each time stamp.
#
# 2.  If this script finds that some crt files are not available, it
#     returns an error status.
#
# 3.  If the prestage option is specified, this script will make a
#     new dataset consisting of the matching swizzled crt files and
#     will prestage it, which will cause this script to pend until
#     all files are prestaged.
#
#------------------------------------------------------------------

# Help function.

function dohelp {
  echo "prepare_crt_merge.sh [-h|--help] [-v|--version <version>] [--prestage] [--defname <defname>|--snapshot_id <snapshot id>]"
  exit
}

# Parse arguments.

if [ $# -eq 0 ]; then
  dohelp
fi

version=''
prestage=0
snapid=''
defname=''

while [ $# -gt 0 ]; do
  case "$1" in

    # Help.
    -h|--help )
      dohelp
      exit
      ;;

    -v|--version )
      if [ $# -gt 1 ]; then
        version=$2
        shift
      fi
      ;;

    --defname )
      if [ $# -gt 1 ]; then
        defname=$2
        shift
      fi
      ;;

    --snapshot_id )
      if [ $# -gt 1 ]; then
        snapid=$2
        shift
      fi
      ;;

    --prestage )
      if [ $# -gt 1 ]; then
        prestage=1
      fi
      ;;

  esac
  shift

done

# Verify options.

if [ x$version = x ]; then
  echo "No version specified."
  dohelp
  exit 1
fi

# One, but not both, of snapid and defname must be specified.

if [ x$snapid = x -a x$defname = x ]; then
  echo "No snapshot id or dataset specified."
  dohelp
  exit 1
fi

if [ x$snapid != x -a x$defname != x ]; then
  echo "Both snapshot id and dataset specified."
  dohelp
  exit 1
fi

# Loop over files in this snapshot or dataset.  Extract start and stop times.

tf=`mktemp`
rm -f $tf

dim=''
if [ x$snapid != x ]; then
  dim="snapshot_id $snapid"
else
  dim="defname: $defname"
fi

samweb list-files "$dim" | while read filename
do

  # Loop over raw ancestors.

  samweb file-lineage rawancestors $filename | while read raw
  do

    # Loop over times (start and stop).

    samweb get-metadata $filename | egrep 'Start Time:|End Time:' | awk '{print $3}' >> $tf
  done
done

# Loop over times.
# Extract crt binary and crt swizzled files.

swf=`mktemp`
rm -f $swf
t0=0
sort -u $tf | while read t
do
  echo $t
  t1=`echo $t | cut -d+ -f1`
  #echo $t1
  t2=`date +%s -d $t1`
  #echo $t2
  dt=$(( $t2 - $t0 ))
  #echo $dt
  if [ $dt -lt 300 ]; then
    #echo "Skipping this time because it is less than 60 seconds later than previous time."
    continue
  fi
  t0=$t2

  # Get crt binary files.

  crt_binary_files=(`samweb list-files "file_type data and file_format crt-binaryraw and data_tier raw and start_time <= '$t' and end_time >= '$t'"`)
  nb=${#crt_binary_files[*]}
  if [ $nb -ne 4 ]; then
    echo "Number of matched binary files is ${nb}, which is not 4."
    exit 1
  fi
  crt_dim_files=`echo ${crt_binary_files[*]} | tr ' ' ,`

  # Get crt swizzled files.

  crt_swizzled_files=(`samweb list-files "file_type data and file_format artroot and data_tier raw and ub_project.version $version and ischildof: ( file_name ${crt_dim_files} )"`)
  ns=${#crt_swizzled_files[*]}
  if [ $ns -ne 6 ]; then
    echo "Number of matched swizzled files is ${ns}, which is not 6."
    exit 1
  fi
  echo ${crt_swizzled_files[*]} | tr ' ' '\n' >> $swf

done
rm -f $tf

echo "Total swizzled files"
sort -u $swf

# Prestage crt swizzled files?

if [ $prestage -ne 0 ]; then
  crt_swizzled_files=(`cat $swf`)
  rm -f $swf
  crt_dim_files=`echo ${crt_swizzled_files[*]} | tr ' ' ,`
  defname=${USER}_`uuidgen`
  echo "Creating dataset definition $defname"
  samweb create-definition $defname "file_name ${crt_dim_files}"
  samweb prestage-dataset --defname $defname
fi
