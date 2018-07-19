#! /bin/bash
#------------------------------------------------------------------
#
# Purpose: A batch worker script for starting a sam project.
#
# Usage:
#
# condor_start_project_crt_merge_v06_26_01_13.sh [options]
#
# --sam_user <arg>    - Specify sam user (default $GRID_USER).
# --sam_group <arg>   - Specify sam group (required).
# --sam_station <arg> - Specify sam station (required).
# --sam_defname <arg> - Sam dataset definition name (required).
# --sam_project <arg> - Sam project name (required).
# --logdir <arg>      - Specify log directory (optional). 
# -g, --grid          - No effect (allowed for compatibility).
# --recur             - Recursive input dataset (force snapshot).
# --init <path>       - Absolute path of environment initialization script (optional).
# --max_files <n>     - Specify the maximum number of files to include in this project.
# --prestage_fraction - Fraction of files that should be prestaged.
#                       Specify as floating point number between 0 and 1.
#
# End options.
#
# Created: H. Greenlee, 10-May-2018
#
#------------------------------------------------------------------

# Parse arguments.

SAM_USER=$GRID_USER
SAM_GROUP=""
SAM_STATION=""
SAM_DEFNAME=""
SAM_PROJECT=""
LOGDIR=""
RECUR=0
INIT=""
MAX_FILES=0
PRESTAGE_FRACTION=0
IFDH_OPT=""

while [ $# -gt 0 ]; do
  case "$1" in

    # Help.
    -h|--help )
      awk '/^# Usage:/,/^# End options/{print $0}' $0 | cut -c3- | head -n -2
      exit
      ;;

    # Sam user.
    --sam_user )
      if [ $# -gt 1 ]; then
        SAM_USER=$2
        shift
      fi
      ;;

    # Sam group.
    --sam_group )
      if [ $# -gt 1 ]; then
        SAM_GROUP=$2
        shift
      fi
      ;;

    # Sam station.
    --sam_station )
      if [ $# -gt 1 ]; then
        SAM_STATION=$2
        shift
      fi
      ;;

    # Sam dataset definition name.
    --sam_defname )
      if [ $# -gt 1 ]; then
        SAM_DEFNAME=$2
        shift
      fi
      ;;

    # Sam project name.
    --sam_project )
      if [ $# -gt 1 ]; then
        SAM_PROJECT=$2
        shift
      fi
      ;;

    # Log directory.
    --logdir )
      if [ $# -gt 1 ]; then
        LOGDIR=$2
        shift
      fi
      ;;

    # Grid flag.
    -g|--grid )
      ;;

    # Recursive flag.
    --recur )
      RECUR=1
      ;;

    # Specify environment initialization script path.
    --init )
      if [ $# -gt 1 ]; then
        INIT=$2
        shift
      fi
      ;;

    # Specify the maximum number of files for this project.
    --max_files )
      if [ $# -gt 1 ]; then
        MAX_FILES=$2
        shift
      fi
      ;;

    # Specify fraction of files that should be prestaged.
    --prestage_fraction )
      if [ $# -gt 1 ]; then
        PRESTAGE_FRACTION=$2
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

echo "Nodename: `hostname`"

# Check and print configuraiton options.

echo "Sam user: $SAM_USER"
echo "Sam group: $SAM_GROUP"
echo "Sam station: $SAM_STATION"
echo "Sam dataset definition: $SAM_DEFNAME"
echo "Sam project name: $SAM_PROJECT"
echo "Recursive flag: $RECUR"
echo "Prestage fraction: $PRESTAGE_FRACTION"

# Complain if SAM_STATION is not defined.

if [ x$SAM_STATION = x ]; then
  echo "Sam station was not specified (use option --sam_station)."
  exit 1
fi

# Complain if SAM_GROUP is not defined.

if [ x$SAM_GROUP = x ]; then
  echo "Sam group was not specified (use option --sam_group)."
  exit 1
fi

# Complain if SAM_DEFNAME is not defined.

if [ x$SAM_DEFNAME = x ]; then
  echo "Sam dataset was not specified (use option --sam_defname)."
  exit 1
fi

# Complain if SAM_PROJECT is not defined.

if [ x$SAM_PROJECT = x ]; then
  echo "Sam project name was not specified (use option --sam_project)."
  exit 1
fi

# Initialize ups products and mrb.

echo "Initializing ups and mrb."

if [ x$INIT != x ]; then
  if [ ! -f $INIT ]; then
    echo "Environment initialization script $INIT not found."
    exit 1
  fi
  echo "Sourcing $INIT"
  source $INIT
else
  echo "Sourcing setup_experiment.sh"
  source ${CONDOR_DIR_INPUT}/setup_experiment.sh
fi

echo PRODUCTS=$PRODUCTS

# Ifdh may already be setup by jobsub wrapper.
# If not, set it up here.

echo "IFDHC_DIR=$IFDHC_DIR"
if [ x$IFDHC_DIR = x ]; then
  echo "Setting up ifdhc, because jobsub did not set it up."
  setup ifdhc
fi
echo "IFDHC_DIR=$IFDHC_DIR"

# Setup sam_web_client, if not already done.

if [ x$SAM_WEB_CLIENT_DIR = x ]; then
  echo "Setting up sam_web_client."
  setup sam_web_client
fi
echo "SAM_WEB_CLIENT_DIR=$SAM_WEB_CLIENT_DIR"

# Set options for ifdh.

echo "IFDH_OPT=$IFDH_OPT"

# Create the scratch directory in the condor scratch diretory.
# Copied from condor_lBdetMC.sh.
# Scratch directory path is stored in $TMP.
# Scratch directory is automatically deleted when shell exits.

# Do not change this section.
# It creates a temporary working directory that automatically cleans up all
# leftover files at the end.
TMP=`mktemp -d ${_CONDOR_SCRATCH_DIR}/working_dir.XXXXXXXXXX`
TMP=${TMP:-${_CONDOR_SCRATCH_DIR}/working_dir.$$}

{ [[ -n "$TMP" ]] && mkdir -p "$TMP"; } || \
  { echo "ERROR: unable to create temporary directory!" 1>&2; exit 1; }
trap "[[ -n \"$TMP\" ]] && { cd ; rm -rf \"$TMP\"; }" 0
cd $TMP
# End of the section you should not change.

echo "Scratch directory: $TMP"

# Save the project name in a file.

echo $SAM_PROJECT > sam_project.txt

# Do some preliminary tests on the input dataset definition.
# If dataset definition returns zero files at this point, abort the job.
# If dataset definition returns too many files compared to --max_files, create
# a new dataset definition by adding a "with limit" clause.

nf=`ifdh translateConstraints "defname: $SAM_DEFNAME" | wc -l`
if [ $nf -eq 0 ]; then
  echo "Input dataset $SAM_DEFNAME is empty."
  exit 1
else
  echo "Input dataset contains $nf files."
fi
if [ $MAX_FILES -ne 0 -a $nf -gt $MAX_FILES ]; then 
  limitdef=${SAM_DEFNAME}_limit_$MAX_FILES

  # Check whether limit def already exists.
  # Have to parse command output because ifdh returns wrong status.

  existdef=`ifdh describeDefinition $limitdef 2>/dev/null | grep 'Definition Name:' | wc -l`
  if [ $existdef -gt 0 ]; then
    echo "Using already created limited dataset definition ${limitdef}."
  else
    ifdh createDefinition $limitdef "defname: $SAM_DEFNAME with limit $MAX_FILES" $SAM_USER $SAM_GROUP

    # Assume command worked, because it returns the wrong status.

    echo "Created limited dataset definition ${limitdef}."
  fi

  # If we get to here, we know that we want to user $limitdef instead of $SAM_DEFNAME
  # as the input sam dataset definition.

  SAM_DEFNAME=$limitdef
  nf=$MAX_FILES
fi

# Calculate the number of files to prestage.

npre=`echo "$PRESTAGE_FRACTION * $nf / 1" | bc`
echo "Will attempt to prestage $npre files."

# If number of prestage files is greater than zero, do prestage here.

if [ $npre -gt 0 ]; then

  # Generate name of prestage project.
  # Here we use a safe name that won't drain recursive datasets (unlike "samweb prestage-dataset").

  prjname=prestage_${SAM_DEFNAME}_`date +%Y%m%d_%H%M%S`
  echo "Prestage project: $prjname"

  # Start prestage project.

  ifdh startProject $prjname $SAM_STATION $SAM_DEFNAME $SAM_USER $SAM_GROUP
  if [ $? -ne 0 ]; then
    echo "Failed to start prestage project."
    exit 1
  fi
  echo "Prestage project started."

  # Get prestage project url.

  prjurl=`ifdh findProject $prjname $SAM_STATION`
  if [ x$prjurl = x ]; then
    echo "Unable to find url for project ${prjname}."
    exit 1
  fi

  # Start consumer process.

  node=`hostname`
  appfamily=prestage
  appname=prestage

  echo "Starting consumer process."
  cpid=`ifdh establishProcess $prjurl $appname 1 $node $SAM_USER $appfamily Prestage $npre`
  if [ x$cpid = x ]; then
    echo "Unable to start consumer process for project ${prjname}."
    exit 1
  fi
  echo "Prestage consumer process ${cpid} started."

  # Loop over files.

  n=0
  while true; do

    # Get next file.
    # When this command returns, the file is prestaged.

    fileurl=`ifdh getNextFile $prjurl $cpid`
    if [ $? -ne 0 -o x$fileurl = x ]; then
      echo "No more files."
      echo "$n files prestaged."
      break
    fi
    filename=`basename $fileurl`
    echo "$filename is prestaged."
    n=$(( $n + 1 ))

    # Release file.

    ifdh updateFileStatus $prjurl $cpid $filename consumed

  done

  # End consumer process.

  ifdh endProcess $prjurl $cpid
  echo "Prestage consumer process stopped."

  # End prestage project.

  ifdh endProject $prjurl
  echo "Prestage project stopped."

fi

# Check CRT files.

# Find the earliest start time in the TPC dataset.

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
  dim="defname: $SAM_DEFNAME and start_time>='$t0s' and start_time<='$t2s'"
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

# Find the latest end time in the TPC dataset.

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
  dim="defname: $SAM_DEFNAME and end_time>='$t2s' and end_time<='$t1s'"
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

swf=crt_swizzled.txt
rm -f $swf
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
    rm $swf
    touch $swf
    break
  fi
  crt_dim_files=`echo ${crt_binary_files[*]} | tr ' ' ,`

  # Get crt swizzled files.

  crt_swizzled_files=(`samweb list-files "file_type data and file_format artroot and data_tier raw and ub_project.version prod_v06_26_01_13 and ischildof: ( file_name ${crt_dim_files} )"`)
  ns=${#crt_swizzled_files[*]}
  if [ $ns -ne 6 ]; then
    echo "Number of matched swizzled files is ${ns}, which is not 6."
    rm $swf
    touch $swf
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
  defname=${SAM_USER}_`uuidgen`
  echo "Creating dataset definition $defname"
  samweb create-definition $defname "file_name ${crt_dim_files}"
  samweb prestage-dataset --defname $defname
fi
rm -f $swf

# If recursive flag, force snapshot of input dataset.

if [ $RECUR -ne 0 ]; then
  echo "Forcing snapshot"
  SAM_DEFNAME=${SAM_DEFNAME}:force
fi

# Start the project.

nostart=1
if [ $ncrt -gt 0 ]; then
  echo "Starting project ${SAM_PROJECT}."
  ifdh startProject $SAM_PROJECT $SAM_STATION $SAM_DEFNAME $SAM_USER $SAM_GROUP
  if [ $? -eq 0 ]; then
    echo "Project successfully started."
    nostart=0
  else
    echo "Start project error status $?"
  fi
fi

# Check the project snapshot.

nf=0
if [ $nostart -eq 0 ]; then
  nf=`ifdh translateConstraints "snapshot_for_project_name $SAM_PROJECT" | wc -l`
  echo "Project snapshot contains $nf files."
fi

# Abort if snapshot contains zero files.  Stop project and eventually exit with error status.

if [ $nostart -eq 0 -a $nf -eq 0 ]; then
  echo "Stopping project."
  nostart=1
  PURL=`ifdh findProject $SAM_PROJECT $SAM_STATION`
  if [ x$PURL != x ]; then
    echo "Project url: $PURL"
    ifdh endProject $PURL
    if [ $? -eq 0 ]; then
      echo "Project successfully stopped."
    fi
  fi
fi

# Stash all of the files we want to save in a local
# directory with a unique name.  Then copy this directory
# and its contents recursively.

if [ x$LOGDIR != x ]; then
  LOGDIR=`echo $LOGDIR | sed 's/@s/sam/'`
  OUTPUT_SUBDIR=${CLUSTER}_start
  mkdir $OUTPUT_SUBDIR
  for outfile in *; do
    if [ $outfile != $OUTPUT_SUBDIR ]; then
      mv $outfile $OUTPUT_SUBDIR
    fi
  done
  echo "ifdh cp -r $IFDH_OPT $OUTPUT_SUBDIR ${LOGDIR}/$OUTPUT_SUBDIR"
  ifdh cp -r $IFDH_OPT $OUTPUT_SUBDIR ${LOGDIR}/$OUTPUT_SUBDIR
  if [ $? -ne 0 ]; then
    echo "ifdh cp failed with status ${stat}."
    exit $stat
  fi 
fi

# Done.  Set exit status to reflect whether project was started (0=success).

exit $nostart
