#! /bin/bash
#------------------------------------------------------------------
#
# Purpose: An interactive script for prestaging CRT files matching 
#          a particular TPC file or dataset.
#
# Usage:
#
# prestage_matching_crt_v06_26_01_26.sh [options]
#
# --defname     <arg> - TPC sam dataset definition name.
# --snapshot_id <arg> - TPC sam snapshot id.
# --filename    <arg> - TPC file name.
# --filelist    <arg> - TPC file list.
#
# End options.
#
# Created: H. Greenlee, 10-May-2018
#
#------------------------------------------------------------------

# Parse arguments.

DEFNAME=""
SNAPID=""
FILENAME=""
FILELIST=""

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

    # Sam snapshot id.
    --snapshot_id )
      if [ $# -gt 1 ]; then
        SNAPID=$2
        shift
      fi
      ;;

    # File name.
    --filename )
      if [ $# -gt 1 ]; then
        FILENAME=$2
        shift
      fi
      ;;

    # File list.
    --filelist )
      if [ $# -gt 1 ]; then
        FILELIST=$2
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

if [ x$DEFNAME = x -a x$SNAPID = x -a x$FILENAME = x -a x$FILELIST = x ]; then
  echo "Must specify dataset, snapshot, file name, or file list."
  exit 1
fi

# Construct dimension to select input TPC files.

if [ x$DEFNAME != x ]; then
  dim="defname: $DEFNAME"
elif [ x$SNAPID != x ]; then
  dim="snapshot_id $SNAPID"
elif [ x$FILENAME != x ]; then
  dim="file_name $FILENAME"
else
  if [ ! -f $FILELIST ]; then
    echo "File list $FILELIST not found."
    exit 1
  fi
  dim=""
  while read word rest
  do
    f=`basename $word`
    if [ x"$dim" = x ]; then
      dim="file_name $f"
    else
      dim="$dim, $f"
    fi
  done < $FILELIST
fi

# Execute dimension to find out how many files are selected.

n=`samweb list-files --summary "$dim" | grep 'File count:' | awk '{print $3}'`
echo "$n TPC files."
if [ $n -eq 0 ]; then
  exit
fi

# Find binary raw ancestors of selected files.
# Include the files themselves if they are binary raw files.

echo "Finding binary raw ancestors of TPC files."

binraw=`mktemp`

samweb list-files "file_type data and file_format binary% and data_tier raw and isancestorof: ( $dim with availability physical )" > $binraw
samweb list-files "file_type data and file_format binary% and data_tier raw and $dim" >> $binraw
nbin=`cat $binraw | wc -l`
echo "$nbin binary raw ancestors of TPC files."
if [ $nbin -eq 0 ]; then
  exit
fi

# Loop over binary raw TPC files and find matching CRT raw files.

md=`mktemp`
crtraw=`mktemp`
while read bin
do
  samweb get-metadata $bin > $md
  start=`awk '/Start Time:/{print $3}' $md | cut -d+ -f1`
  end=`awk '/End Time:/{print $3}' $md | cut -d+ -f1`
  samweb list-files "file_type data and file_format crt-binaryraw and data_tier raw and start_time<='$end' and end_time>='$start'" >> $crtraw
done < $binraw
echo
sort -u $crtraw
ncrtbin=`sort -u $crtraw | wc -l`
echo
echo "Found $ncrtbin matching CRT binary files."
if [ $ncrtbin -eq 0 ]; then
  exit
fi

# Loop over CRT binary files and find matching CRT swizzled files.

crtswiz=`mktemp`
sort -u $crtraw | while read crtbin
do
  samweb list-files "file_type data and file_format artroot and ub_project.version prod_v06_26_01_26 and ischildof: ( file_name $crtbin )"  >> $crtswiz
done

echo
cat $crtswiz
ncrtswiz=`cat $crtswiz | wc -l`
echo
echo "Found $ncrtswiz matching CRT swizzled files."
if [ $ncrtswiz -eq 0 ]; then
  exit
fi

# Construct dataset consisting of matching CRT swizzled files."

crt_swizzled_files=(`cat $crtswiz`)
crt_dim_files=`echo ${crt_swizzled_files[*]} | tr ' ' ,`
defname=${USER}_`uuidgen`
echo
echo "Creating dataset definition $defname"
samweb create-definition $defname "file_name ${crt_dim_files}"

# Prestage files.

echo
echo "Prestaging CRT files."
samweb prestage-dataset --defname $defname

# Clean up

rm -f $binraw
rm -f $md
rm -f $crtraw
rm -f $crtswiz
