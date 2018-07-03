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
# --defname  <arg> - TPC sam dataset definition name.
# --filename <arg> - TPC filename.
#
# End options.
#
# Created: H. Greenlee, 10-May-2018
#
#------------------------------------------------------------------

# Parse arguments.

DEFNAME=""
FILENAME=""

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
    --filename )
      if [ $# -gt 1 ]; then
        FILENAME=$2
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

if [ x$DEFNAME = x -a x$FILENAME = x ]; then
  echo "Must specify either dataset or file name."
  exit 1
fi

# Generate list of TPC files to process.

files=`mktemp`
times=`mktemp`
if [ x$FILENAME != x ]; then
  echo $FILENAME > $files
elif [ x$DEFNAME != x ]; then
  samweb list-files "defname: $DEFNAME" > $files
fi
n=`cat $files | wc -l`
echo "$n TPC files."
if [ $n -eq 0 ]; then
  exit 0
fi

while read filename
do
  echo $filename

  # Loop over raw ancestors.

  samweb file-lineage rawancestors $filename | while read raw
  do

    # Loop over times (start and stop).

    samweb get-metadata $raw | egrep 'Start Time:|End Time:' | awk '{print $3}' >> $times
  done
done < $files
rm -f $files

# Loop over times.
# Extract crt binary and crt swizzled files.

swf=`mktemp`
t0=0
sort -u $times | while read t
do
  echo $t
  t1=`echo $t | cut -d+ -f1`
  #echo $t1
  t2=`date +%s -d $t1`
  #echo $t2
  dt=$(( $t2 - $t0 ))
  #echo $dt
  if [ $dt -lt 300 ]; then
    #echo "Skipping this time because it is less than 300 seconds later than previous time."
    continue
  fi
  t0=$t2

  # Get crt binary files.

  crt_binary_files=(`samweb list-files "file_type data and file_format crt-binaryraw and data_tier raw and start_time <= '$t' and end_time >= '$t'"`)
  nb=${#crt_binary_files[*]}
  if [ $nb -ne 4 ]; then
    echo "Number of matched binary files is ${nb}, which is not 4."
    rm -f $swf
    rm -f $times
    break
  fi
  crt_dim_files=`echo ${crt_binary_files[*]} | tr ' ' ,`

  # Get crt swizzled files.

  crt_swizzled_files=(`samweb list-files "file_type data and file_format artroot and data_tier raw and ub_project.version prod_v06_26_01_13 and ischildof: ( file_name ${crt_dim_files} )"`)
  ns=${#crt_swizzled_files[*]}
  if [ $ns -ne 6 ]; then
    echo "Number of matched swizzled files is ${ns}, which is not 6."
    rm -f $swf
    rm -f $times
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
rm -f $times
