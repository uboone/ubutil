#! /bin/bash
#------------------------------------------------------------------
#
# Purpose: An interactive script for prestaging CRT files matching 
#          a particular TPC file or dataset.
#
# Usage:
#
# prestage_matching_crt_v06_26_01_13.sh [options]
#
# --defname     <arg> - TPC sam dataset definition name.
# --snapshot_id <arg> - TPC sam snapshot id.
#
# End options.
#
# Created: H. Greenlee, 10-May-2018
#
#------------------------------------------------------------------

# Parse arguments.

DEFNAME=""
SNAPID=""

while [ $# -gt 0 ]; do
  case "$1" in

    # Help.
    -h|--help )
      awk '/^# Usage:/,/^# End options/{print $0}' $0 | cut -c3- | head -n -2
      exit
      ;;

    # Sam dataset definition name.
    --defname )
      if [ $# -gt 1 ]; then
        DEFNAME=$2
        shift
      fi
      ;;

    # Sam dataset definition name.
    --snapshot_id )
      if [ $# -gt 1 ]; then
        SNAPID=$2
        shift
      fi
      ;;

    # Other.
    * )
      echo "Unknown option $1"
      exit 1
  esac
  shift
done

# Done with arguments.

if [ x$DEFNAME = x -a x$SNAPID = x ]; then
  echo "Must specify dataset or snapshot."
  exit 1
fi

# Find the earliest start time.

t0=0
t1=4000000000
while [ $t1 -ne $t0 ]; 
do
  #echo $t0
  #echo $t1
  t2=$(( ( $t0 + $t1 ) / 2 ))
  if [ $t2 -eq $t0 -o $t2 -eq $t1 ]; then
    break
  fi
  t0s=`date +%Y-%m-%dT%H:%M:%S -d@$t0`
  t1s=`date +%Y-%m-%dT%H:%M:%S -d@$t1`
  t2s=`date +%Y-%m-%dT%H:%M:%S -d@$t2`
  if [ x$DEFNAME != x ]; then
    dim="defname: $DEFNAME and start_time>='$t0s' and start_time<='$t2s'"
  else
    dim="snapshot_id $SNAPID and start_time>='$t0s' and start_time<='$t2s'"
  fi
  #echo $dim
  n=`samweb list-files --summary "$dim" | awk '/File count:/{print $3}'`
  #echo "$n files."
  echo -n .
  if [ $n -eq 0 ]; then
    t0=$t2
  else
    t1=$t2
  fi
done
early_time=$t0
echo "Early time: `date +%Y-%m-%dT%H:%M:%S -d@$early_time`"

# Find the latest end time

t0=0
t1=4000000000
while [ $t1 -ne $t0 ]; 
do
  #echo $t0
  #echo $t1
  t2=$(( ( $t0 + $t1 ) / 2 ))
  if [ $t2 -eq $t0 -o $t2 -eq $t1 ]; then
    break
  fi
  t0s=`date +%Y-%m-%dT%H:%M:%S -d@$t0`
  t1s=`date +%Y-%m-%dT%H:%M:%S -d@$t1`
  t2s=`date +%Y-%m-%dT%H:%M:%S -d@$t2`
  if [ x$DEFNAME != x ]; then
    dim="defname: $DEFNAME and end_time>='$t2s' and end_time<='$t1s'"
  else
    dim="snapshot_id $SNAPID and end_time>='$t2s' and end_time<='$t1s'"
  fi
  #echo $dim
  n=`samweb list-files --summary "$dim" | awk '/File count:/{print $3}'`
  #echo "$n files."
  echo -n .
  if [ $n -eq 0 ]; then
    t1=$t2
  else
    t0=$t2
  fi
done
late_time=$t1
echo "Late time:  `date +%Y-%m-%dT%H:%M:%S -d@$late_time`"

# Make an array of times to query.

declare -a times
n=0
while [ $early_time -lt $late_time ];
do
  times[$n]=$early_time
  early_time=$(( $early_time + 7200 ))
  n=$(( $n + 1 ))
done
times[$n]=$late_time

echo "All times:"
for t in ${times[*]}
do
  date +%Y-%m-%dT%H:%M:%S -d@$t
done

# Loop over times.
# Extract crt binary and crt swizzled files.

echo
swf=`mktemp`
for t in ${times[*]}
do
  ts=`date +%Y-%m-%dT%H:%M:%S -d@$t`
  echo "Looking for CRT files matching time $ts"

  # Get crt binary files.

  crt_binary_files=(`samweb list-files "file_type data and file_format crt-binaryraw and start_time <= '$ts' and end_time >= '$ts'"`)
  nb=${#crt_binary_files[*]}
  echo "Found $nb CRT files."
  if [ $nb -ne 4 ]; then
    echo "Number of matched binary files is ${nb}, which is not 4."
    break
  fi
  crt_dim_files=`echo ${crt_binary_files[*]} | tr ' ' ,`

  # Get crt swizzled files.

  crt_swizzled_files=(`samweb list-files "file_type data and file_format artroot and data_tier raw and ub_project.version prod_v06_26_01_13 and ischildof: ( file_name ${crt_dim_files} )"`)
  ns=${#crt_swizzled_files[*]}
  if [ $ns -ne 6 ]; then
    echo "Number of matched swizzled files is ${ns}, which is not 6."
    break
  fi
  echo ${crt_swizzled_files[*]} | tr ' ' '\n' >> $swf

done

ncrt=`sort -u $swf | wc -l`
echo "Total CRT swizzled files: $ncrt"
sort -u $swf

# Prestage crt swizzled files.

if [ $ncrt -gt 0 ]; then
  crt_swizzled_files=(`sort -u $swf`)
  rm -f $swf
  crt_dim_files=`echo ${crt_swizzled_files[*]} | tr ' ' ,`
  defname=${USER}_`uuidgen`
  echo "Creating dataset definition $defname"
  samweb create-definition $defname "file_name ${crt_dim_files}"
  samweb prestage-dataset --defname $defname
fi
rm -f $swf
