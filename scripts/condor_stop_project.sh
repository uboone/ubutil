#! /bin/bash
#------------------------------------------------------------------
#
# Purpose: A batch worker script for stoping a sam project.
#          This script should run after all workers finish.
#
# Usage:
#
# condor_stop_project.sh [options]
#
# --sam_station <arg> - Specify sam station (default "uboone").
# --sam_project <arg> - Sam project name (required).
# --outdir <arg>      - Specify output directory (optional). 
# -g, --grid          - Be grid-friendly.
# --group <arg>       - Group or experiment (default "uboone").
#
# End options.
#
# Created: H. Greenlee, 29-Aug-2012
#
#------------------------------------------------------------------

# Parse arguments.

SAM_STATION="uboone"
SAM_PROJECT=""
OUTDIR=""
GRID=0
GRP=""
IFDH_OPT=""

while [ $# -gt 0 ]; do
  case "$1" in

    # Help.
    -h|--help )
      awk '/^# Usage:/,/^# End options/{print $0}' $0 | cut -c3- | head -n -2
      exit
      ;;

    # Sam station.
    --sam_station )
      if [ $# -gt 1 ]; then
        SAM_STATION=$2
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

    # Output directory.
    --outdir )
      if [ $# -gt 1 ]; then
        OUTDIR=$2
        shift
      fi
      ;;

    # Grid flag.
    -g|--grid )
      GRID=1
      ;;

    # Group.
    --group )
      if [ $# -gt 1 ]; then
        GRP=$2
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

echo "Sam station: $SAM_STATION"
echo "Sam project name: $SAM_PROJECT"

# Complain if SAM_PROJECT is not defined.

if [ x$SAM_PROJECT = x ]; then
  echo "Sam project name was not specified (use option --sam_project)."
  exit 1
fi

# Set GROUP environment variable.

unset GROUP
if [ x$GRP != x ]; then
  GROUP=$GRP
else
  echo "GROUP not specified."
  exit 1
fi
export GROUP
echo "Group: $GROUP"

# Initialize microboone/lbne ups products and mrb.

echo "Initializing ups and mrb."

if [ $GROUP = uboone ]; then

  OASIS_DIR="/cvmfs/oasis.opensciencegrid.org/microboone/products/"
  FERMIAPP_DIR="/grid/fermiapp/products/uboone/"

  if [[ -d "${FERMIAPP_DIR}" ]]; then
    echo "Sourcing ${FERMIAPP_DIR}setup_uboone.sh file"
    source ${FERMIAPP_DIR}/setup_uboone.sh
	
  elif [[ -d "${OASIS_DIR}" ]]; then
    echo "Sourcing the ${OASIS_DIR}setup_uboone.sh file"
    source ${OASIS_DIR}/setup_uboone.sh
	
  else
    echo "Could not find MRB initialization script setup_uboone.sh"
    exit 1
  fi
elif [ $GROUP = lbne ]; then
  OASIS_DIR="/cvmfs/oasis.opensciencegrid.org/lbne/products/"
  FERMIAPP_DIR="/grid/fermiapp/lbne/software/"

  if [[ -d "${FERMIAPP_DIR}" ]]; then
    echo "Sourcing ${FERMIAPP_DIR}setup_lbne.sh file"
    source ${FERMIAPP_DIR}/setup_lbne.sh
	
  elif [[ -d "${OASIS_DIR}" ]]; then
    echo "Sourcing the ${OASIS_DIR}setup_lbne.sh file"
    source ${OASIS_DIR}/setup_lbne.sh
	
  else
    echo "Could not find MRB initialization script setup_lbne.sh"
    exit 1
  fi
else
  echo "Unknow group ${GROUP}"
  exit 1
fi

# Ifdh may already be setup by jobsub wrapper.
# If not, set it up here.

echo "IFDHC_DIR=$IFDHC_DIR"
if [ x$IFDHC_DIR = x ]; then
  echo "Setting up ifdhc, because jobsub did not set it up."
  setup ifdhc
fi
echo "IFDHC_DIR=$IFDHC_DIR"

# Set options for ifdh.

if [ $GRID -ne 0 ]; then
  echo "X509_USER_PROXY = $X509_USER_PROXY"
  if ! echo $X509_USER_PROXY | grep -q Production; then
    IFDH_OPT="--force=expgridftp"
  fi
fi
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

# See if we need to set umask for group write.

if [ $GRID -eq 0 -a x$OUTDIR != x ]; then
  OUTUSER=`stat -c %U $OUTDIR`
  CURUSER=`whoami`
  if [ $OUTUSER != $CURUSER ]; then
    echo "Setting umask for group write."
    umask 002
  fi
fi

# Save the project name in a file.

echo $SAM_PROJECT > sam_project.txt

# Find project url.

PURL=`ifdh findProject $SAM_PROJECT $SAM_STATION`
if [ x$PURL = x ]; then
  echo "Unable to find url for project ${SAM_PROJECT}."
  exit 1
else
  echo "Project url: $PURL"
fi

# Stop the project.

echo "Stopping project."
ifdh endProject $PURL
if [ $? -eq 0 ]; then
  echo "Project successfully stopped."
else
  echo "Stop project error status $?"
fi

# Stash all of the files we want to save in a local
# directory with a unique name.  Then copy this directory
# and its contents recursively.

if [ x$OUTDIR != x ]; then
  OUTPUT_SUBDIR=${CLUSTER}_stop
  mkdir $OUTPUT_SUBDIR
  for outfile in *; do
    if [ $outfile != $OUTPUT_SUBDIR ]; then
      mv $outfile $OUTPUT_SUBDIR
    fi
  done
  echo "ifdh cp -r $IFDH_OPT $OUTPUT_SUBDIR ${OUTDIR}/$OUTPUT_SUBDIR"
  ifdh cp -r $IFDH_OPT $OUTPUT_SUBDIR ${OUTDIR}/$OUTPUT_SUBDIR
  stat=$?
  if [ $stat -ne 0 ]; then
    echo "ifdh cp failed with status ${stat}."
    exit $stat
  fi 
fi
