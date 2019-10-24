#! /bin/bash
#------------------------------------------------------------------
#
# Purpose: Batch script for merging jobs.
#
# This script is an adapted and streamlined version of condor_lar.sh.
# The main new feature supported by this script, that is not supported
# by condor_lar.sh, is the ability to run multiple sam projects in
# one job.
#
# This script does not support input methods other than sam.
#
# Many nonrelevant command line options have been removed.
#
# Usage:
#
# condor_merge.sh [options]
#
# Lar options:
#
# -c, --config <arg>      - Configuration (fcl) file (required).
#
# Sam and parallel project options.
#
# --sam_user <arg>        - Specify sam user (default $GRID_USER).
# --sam_group <arg>       - Specify sam group (default --group option).
# --sam_station <arg>     - Specify sam station (default --group option).
# --sam_defname <arg>     - Sam dataset definition name(s).  Colon-separated list.
# --sam_project <arg>     - Sam project name(s).  Colon-separated list.
# --sam_start             - Specify that this worker should be responsible for
#                           starting and stopping the sam projects.
# --recur                 - Recursive input dataset (force snapshot).
# --sam_schema <arg>      - Use this option with argument "root" to stream files using
#                           xrootd.  Leave this option out for standard file copy.
# Validation options.
#
# --declare               - Do sam declaration.
# --validate              - Do validation checks.
# --copy                  - Copy output files directly to FTS dropbox instead of
#                           output directory.
#
# Larsoft options.
#
# --ups <arg>             - Comma-separated list of top level run-time ups products.
# -r, --release <arg>     - Release tag.
# -q, -b, --build <arg>   - Release build qualifier (default "debug", or "prof").
# --localtar <arg>        - Tarball of local test release.
#
# Other options.
#
# -h, --help              - Print help.
# --group <arg>           - Group or experiment (required).
# --outdir <arg>          - Output directory (required).
# --logdir <arg>          - Log directory (required).
# --init-script <arg>     - User initialization script to execute.
# --init-source <arg>     - User initialization script to source (bash).
# --end-script <arg>      - User end-of-job script to execute.
# --init <path>           - Absolute path of environment initialization script.
#
# End options.
#
# Run time environment setup.
#
# MRB run-time environmental setup is controlled by four options:
#  --release (-r), --build (-b, -q), and --localtar.  
#
# a) Use option --release or -r to specify version of top-level product(s).  
# b) Use option --build or -b to specify build full qualifiers (e.g. 
#    "debug:e5" or "e5:prof").
# c) Option --localtar are used to specify your local
#    test release.  Use one or the other (not both).
#
#    Use --localtar to specify thye location of a tarball of your
#    install directory (made relative to $MRB_INSTALL).
#
# Notes.
#
# 1.  A local test release may be specified as an absolute path using
#     a tarball using --localtar.  The location of the tarball
#     may be specified as an absolute path visible on the worker, or a 
#     relative path relative to the work directory.
#
# 2.  The fcl file specified using option -c or --config may be a compound
#     fcl file (similar to compound fcl files used by condor_lar.sh), containing
#     fcl configurations all stages.  The number of stages must match the 
#     number of sam definitions and projects specified using command line option
#     --sam_defname and --sam_project.
#
# 3.  The output directory must exist and be writable by the batch
#     worker (i.e. be group-writable for grid jobs).  The worker
#     makes a new subdirectory called ${CLUSTER}_${PROCESS} in the output
#     directory and copies all files in the batch scratch directory there 
#     at the end of the job.
#
# 4. Option --init <path> is optional.  If specified, it should point to
#    the absolute path of the experiment environment initialization script,
#    which path must be visible from the batch worker (e.g. /cvmfs/...).
#    If this option is not specified, this script will look for and source
#    a script with hardwired name "setup_experiment.sh" in directory
#    ${CONDIR_DIR_INPUT}.
#
#
# Created: H. Greenlee, 21-Oct-2019
#
#------------------------------------------------------------------

# Parse arguments.

FCL=""
UPS_PRDS=""
REL=""
QUAL=""
LOCALTAR=""
GRP=""
OUTDIR=""
LOGDIR=""
SCRATCH=""
INITSCRIPT=""
INITSOURCE=""
ENDSCRIPT=""
SAM_USER=$GRID_USER
SAM_GROUP=""
SAM_STATION=""
SAM_DEFNAME=""
SAM_PROJECT=""
SAM_START=0
RECUR=0
SAM_SCHEMA=""
IFDH_OPT=""
DECLARE_IN_JOB=0
VALIDATE_IN_JOB=0
COPY_TO_FTS=0
INIT=""

while [ $# -gt 0 ]; do
  case "$1" in

    # Help.
    -h|--help )
      awk '/^# Usage:/,/^# End options/{print $0}' $0 | cut -c3- | head -n -2
      exit
      ;;

    # Config file.
    -c|--config )
      if [ $# -gt 1 ]; then
        FCL=$2
        shift
      fi
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

    # Sam start/stop project flag.
    --sam_start )
      SAM_START=1
      ;;

    # Recursive flag.
    --recur )
      RECUR=1
      ;;

    # Sam schema.
    --sam_schema )
      if [ $# -gt 1 ]; then
        SAM_SCHEMA=$2
        shift
      fi
      ;;

    # Top level ups products (comma-separated list).
    --ups )
      if [ $# -gt 1 ]; then
        UPS_PRDS=$2
        shift
      fi
      ;;

    # Release tag.
    -r|--release )
      if [ $# -gt 1 ]; then
        REL=$2
        shift
      fi
      ;;

    # Release build qualifier.
    -q|-b|--build )
      if [ $# -gt 1 ]; then
        QUAL=$2
        shift
      fi
      ;;

    # Local test release tarball.
    --localtar )
      if [ $# -gt 1 ]; then
        LOCALTAR=$2
        shift
      fi
      ;;

    # Group.
    --group )
      if [ $# -gt 1 ]; then
        GRP=$2
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

    # Log directory.
    --logdir )
      if [ $# -gt 1 ]; then
        LOGDIR=$2
        shift
      fi
      ;;

    # User initialization script.
    --init-script )
      if [ $# -gt 1 ]; then
        INITSCRIPT=$2
        shift
      fi
      ;;

    # User source initialization script.
    --init-source )
      if [ $# -gt 1 ]; then
        INITSOURCE=$2
        shift
      fi
      ;;

    # User end-of-job script.
    --end-script )
      if [ $# -gt 1 ]; then
        ENDSCRIPT=$2
        shift
      fi
      ;;
    
    # Declare good output root files to SAM.
    --declare )
      DECLARE_IN_JOB=1
      ;;
      
    # Run validation steps in project.py on root outputs directly in the job.
    --validate )
      VALIDATE_IN_JOB=1
      ;;

   # Copy Output to FTS.
    --copy )
      COPY_TO_FTS=1
      ;;

    # Specify environment initialization script path.
    --init )
      if [ $# -gt 1 ]; then
        INIT=$2
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

#echo "FCL=$FCL"
#echo "REL=$REL"
#echo "QUAL=$QUAL"
#echo "LOCALTAR=$LOCALTAR"
#echo "GRP=$GRP"
#echo "OUTDIR=$OUTDIR"
#echo "LOGDIR=$LOGDIR"
#echo "CLUS=$CLUS"
#echo "PROC=$PROC"
#echo "INITSCRIPT=$INITSCRIPT"
#echo "INITSOURCE=$INITSOURCE"
#echo "ENDSCRIPT=$ENDSCRIPT"
#echo "VALIDATE_IN_JOB=$VALIDATE_IN_JOB"

# Done with arguments.

echo "Nodename: `hostname -f`"
id
echo "Load average:"
cat /proc/loadavg

# Set defaults.

if [ x$QUAL = x ]; then
  QUAL="prof"
fi

if [ x$SAM_GROUP = x ]; then
  SAM_GROUP=$GRP
fi

if [ x$SAM_STATION = x ]; then
  SAM_STATION=$GRP
fi

# Standardize sam_schema (xrootd -> root, xroot -> root).

if [ x$SAM_SCHEMA = xxrootd ]; then
  SAM_SCHEMA=root
fi
if [ x$SAM_SCHEMA = xxroot ]; then
  SAM_SCHEMA=root
fi

echo "uname -r: `uname -r`"
echo "UPS_OVERRIDE: $UPS_OVERRIDE"
echo "Condor dir input: $CONDOR_DIR_INPUT"

# Initialize experiment ups products and mrb.

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
echo "ups flavor: `ups flavor`"

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

# Set options for ifdh.

echo "X509_USER_PROXY = $X509_USER_PROXY"
echo "IFDH_OPT=$IFDH_OPT"

# Make sure fcl file argument was specified.

if [ x$FCL = x ]; then
  echo "No configuration option (-c|--config) was specified."
  exit 1
fi

# Make sure output directory exists and is writable.

if [ x$OUTDIR = x ]; then
  echo "Output directory not specified."
  exit 1
fi
echo "Output directory: $OUTDIR"

# Make sure log directory exists and is writable.

if [ x$LOGDIR = x ]; then
  echo "Log directory not specified."
  exit 1
fi
echo "Log directory: $LOGDIR"

# Make sure scratch directory is defined.
SCRATCH=$_CONDOR_SCRATCH_DIR
if [ x$SCRATCH = x -o ! -d "$SCRATCH" -o ! -w "$SCRATCH" ]; then
  echo "Local scratch directory not defined or not writable."
  exit 1
fi

# Create the scratch directory in the condor scratch diretory.
# Copied from condor_lBdetMC.sh.
# Scratch directory path is stored in $TMP.
# Scratch directory is automatically deleted when shell exits.

# Do not change this section.
# It creates a temporary working directory that automatically cleans up all
# leftover files at the end.
TMP=`mktemp -d ${SCRATCH}/working_dir.XXXXXXXXXX`
TMP=${TMP:-${SCRATCH}/working_dir.$$}

{ [[ -n "$TMP" ]] && mkdir -p "$TMP"; } || \
  { echo "ERROR: unable to create temporary directory!" 1>&2; exit 1; }
trap "[[ -n \"$TMP\" ]] && { rm -rf \"$TMP\"; }" 0
chmod 755 $TMP
cd $TMP
# End of the section you should not change.

echo "Scratch directory: $TMP"

# Copy files from work directory to scratch directory.

echo "No longer fetching files from work directory."
echo "that's now done with using jobsub -f commands"
mkdir work
cp ${CONDOR_DIR_INPUT}/* ./work/
cd work
find . -name \*.tar -exec tar xf {} \;
find . -name \*.py -exec chmod +x {} \;
find . -name \*.sh -exec chmod +x {} \;
echo "Local working directoroy:"
pwd
ls
echo

# Save the hostname and condor job id.

hostname > hostname.txt
echo ${CLUSTER}.${PROCESS} > jobid.txt
if [ x$CLUSTER = x ]; then
  echo "CLUSTER not specified."
  exit 1
fi
if [ x$PROCESS = x ]; then
  echo "PROCESS not specified."
  exit 1
fi
echo "Cluster: $CLUSTER"
echo "Process: $PROCESS"

# Construct name of output subdirectory.

OUTPUT_SUBDIR=${CLUSTER}_${PROCESS}
echo "Output subdirectory: $OUTPUT_SUBDIR"

# Make sure fcl file exists.

if [ ! -f $FCL ]; then
  echo "Configuration file $FCL does not exist."
  exit 1
fi

# Make sure init script exists and is executable (if specified).

if [ x$INITSCRIPT != x ]; then
  if [ -f "$INITSCRIPT" ]; then
    chmod +x $INITSCRIPT
  else
    echo "Initialization script $INITSCRIPT does not exist."
    exit 1
  fi
fi

# Make sure init source script exists (if specified).

if [ x$INITSOURCE != x -a ! -f "$INITSOURCE" ]; then
  echo "Initialization source script $INITSOURCE does not exist."
  exit 1
fi

# Make sure end-of-job script exists and is executable (if specified).

if [ x$ENDSCRIPT != x ]; then
  if [ -f "$ENDSCRIPT" ]; then
    chmod +x $ENDSCRIPT
  else
    echo "Initialization script $ENDSCRIPT does not exist."
    exit 1
  fi
fi

# MRB run time environment setup goes here.

cd $TMP/work

# Setup local larsoft test release from tarball.

if [ x$LOCALTAR != x ]; then
  mkdir $TMP/local
  cd $TMP/local

  # Fetch the tarball.

  echo "Fetching test release tarball ${LOCALTAR}."

  # Make sure ifdhc is setup.

  if [ x$IFDHC_DIR = x ]; then
    echo "Setting up ifdhc before fetching tarball."
    setup ifdhc
  fi
  echo "IFDHC_DIR=$IFDHC_DIR"
  ifdh cp $LOCALTAR local.tar
  stat=$?
  if [ $stat -ne 0 ]; then
    echo "ifdh cp failed with status ${stat}."
    exit $stat
  fi 

  # Extract the tarball.

  tar -xf local.tar

  # Setup the environment.

  cd $TMP/work
  echo "Initializing localProducts from tarball ${LOCALTAR}."
  sed "s@setenv MRB_INSTALL.*@setenv MRB_INSTALL ${TMP}/local@" $TMP/local/setup | \
  sed "s@setenv MRB_TOP.*@setenv MRB_TOP ${TMP}@" > $TMP/local/setup.local
  . $TMP/local/setup.local
  #echo "MRB_INSTALL=${MRB_INSTALL}."
  #echo "MRB_QUALS=${MRB_QUALS}."
  echo "Setting up all localProducts."
  if [ x$IFDHC_DIR != x ]; then
    unsetup ifdhc
  fi
  mrbslp
fi

# Setup specified version of top level run time products
# (if specified, and if local test release did not set them up).

for prd in `echo $UPS_PRDS | tr , ' '`
do
  if ! ups active | grep -q $prd; then
    echo "Setting up $prd $REL -q ${QUAL}."
    if [ x$IFDHC_DIR != x -a x$IFBEAM_DIR = x ]; then
      unsetup ifdhc
    fi
    setup $prd $REL -q $QUAL
  fi
done

ups active

cd $TMP/work

# In case mrb setup didn't setup a version of ifdhc, set up ifdhc again.

if [ x$IFDHC_DIR = x ]; then
  echo "Setting up ifdhc again, because larsoft did not set it up."
  setup ifdhc
fi
echo "IFDH_ART_DIR=$IFDH_ART_DIR"
echo "IFDHC_DIR=$IFDHC_DIR"

#Break the master wrapper fcl into each stage

nfcls=0

while read -r line
do

  if [ "$(echo $line | awk '{print $1}')" = "#---STAGE" ]; then
    stage="$(echo $line | awk '{print $2}')"
    stage_fcl="Stage$stage.fcl"
    nfcls=$(( $nfcls + 1 )) 
    continue
  fi

  if [ "$line" = "#---END_STAGE" ]; then
    continue
  fi

  echo $line >> $stage_fcl
done < $FCL

#We now have nStage fcl files, each which need to be run serially 
stage=0

echo "Start loop over stages"
while [ $stage -lt $nfcls ]; do
  FCL="Stage$stage.fcl"

  # Extract sam dataset definition and sam project for this stage.

  SAM_DEF_STAGE=`echo $SAM_DEFNAME | cut -d: -f$(( $stage + 1 ))`
  SAM_PRJ_STAGE=`echo $SAM_PROJECT | cut -d: -f$(( $stage + 1 ))`
 
  # Sam stuff for this stage.

  PURL=''
  CPID=''

  # Make sure a project name has been specified.

  if [ x$SAM_PRJ_STAGE = x ]; then
    echo "No sam project was specified."
    exit 1
  fi
  echo "Sam project: $SAM_PRJ_STAGE"

  # Start project (if requested).

  if [ $SAM_START -ne 0 ]; then
    if [ x$SAM_DEF_STAGE != x ]; then

      # Do some preliminary tests on the input dataset definition.
      # If dataset definition returns zero files at this point, abort the job.

      nf=`ifdh translateConstraints "defname: $SAM_DEF_STAGE" | wc -l`
      if [ $nf -eq 0 ]; then
        echo "Input dataset $SAM_DEF_STAGE is empty."
        exit 1
      fi

      # If recursive flag, take snapshot of input dataset.

      if [ $RECUR -ne 0 ]; then
        echo "Forcing snapshot"
        SAM_DEF_STAGE=${SAM_DEF_STAGE}:force
      fi

      # Start the project.

      echo "Starting project $SAM_PRJ_STAGE using sam dataset definition $SAM_DEF_STAGE"
      ifdh startProject $SAM_PRJ_STAGE $SAM_STATION $SAM_DEF_STAGE $SAM_USER $SAM_GROUP
      if [ $? -eq 0 ]; then
        echo "Start project succeeded."
      else
        echo "Start projet failed."
        exit 1
      fi
    fi
  fi

  # Get the project url of a running project (maybe the one we just started,
  # or maybe started externally).  This command has to succeed, or we can't
  # continue.

  PURL=`ifdh findProject $SAM_PRJ_STAGE $SAM_STATION`
  if [ x$PURL = x ]; then
    echo "Unable to find url for project ${SAM_PRJ_STAGE}."
    exit 1
  else
    echo "Project url: $PURL"
  fi

  # Start the consumer process.  This command also has to succeed.

  NODE=`hostname`
  APPFAMILY=art

  # Parse fcl file to extract process_name, and use that
  # as the application name for starting the consumer process.

  APPNAME=`fhicl-dump $FCL | grep process_name: | tr -d '"' | awk '{print $2}'`
  if [ $? -ne 0 ]; then
    echo "fhicl-dump $FCL failed to run. May be missing a ups product, library, or fcl file."
    exit 1
  fi
  if [ x$APPNAME = x ]; then
    echo "Trouble determining application name."
    echo "cat $FCL"
    cat $FCL
    exit 1
  fi

  # Make sure release version is not empty, or ifdh command line will be messed up.

  if [ x$REL = x ]; then
    REL=1
  fi

  # Make description, which is conventionally the jobsub job id.
  # This can not be empty.

  DESC=$JOBSUBJOBID
  if [ x$DESC = x ]; then
    DESC=$FCL
  fi

  echo "Starting consumer process."
  echo "ifdh establishProcess $PURL $APPNAME $REL $NODE $SAM_USER $APPFAMILY $DESC $NFILE $SAM_SCHEMA"
  CPID=`ifdh establishProcess $PURL $APPNAME $REL $NODE $SAM_USER $APPFAMILY $DESC $NFILE $SAM_SCHEMA`
  if [ x$CPID = x ]; then
    echo "Unable to start consumer process for project url ${PURL}."
    exit 1
  else
    echo "Consumer process id $CPID"
  fi

  # Stash away the project name and consumer process id in case we need them
  # later for bookkeeping.

  echo $SAM_PRJ_STAGE > sam_project${stage}.txt
  echo $CPID > cpid${stage}.txt

  # Construct options for lar command line.

  LAROPT="-c $FCL --rethrow-default"
  echo "Laropt: $LAROPT"

  if [ x$PURL != x ]; then
    LAROPT="$LAROPT --sam-web-uri $PURL"
  fi

  if [ x$CPID != x ]; then
    LAROPT="$LAROPT --sam-process-id $CPID"
  fi

  # Run/source optional initialization scripts.

  if [ $stage -eq 0 ]; then
    if [ x$INITSCRIPT != x ]; then
      echo "Running initialization script ${INITSCRIPT}."
      if ! ./${INITSCRIPT}; then
        exit $?
      fi
    fi

    if [ x$INITSOURCE != x -a $stage -eq 0 ]; then
      echo "Sourcing initialization source script ${INITSOURCE}."
      . $INITSOURCE
      status=$?
      if [ $status -ne 0 ]; then
        exit $status
      fi
    fi
  fi

  # Save a copy of the environment, which can be helpful for debugging.

  env > env.txt

  # Save a canonicalized version of the fcl configuration.

  fhicl-dump $FCL > cfgStage$stage.fcl

  # Dump proxy information.

  echo
  echo "Proxy:"
  echo
  voms-proxy-info -all

  # Run lar.
  pwd
  echo "lar $LAROPT"
  echo "lar $LAROPT" > commandStage$stage.txt
  lar $LAROPT > larStage$stage.out 2> larStage$stage.err
  stat=$?
  echo $stat > larStage$stage.stat
  echo "lar completed with exit status ${stat}."
  if [ $stat -ne 0 ]; then
    echo
    echo "Proxy:"
    echo
    voms-proxy-info -all
    echo
    echo "tail -1000 larStage$stage.out"
    echo
    tail -1000 larStage$stage.out
    echo
    echo "tail -1000 larStage$stage.err"
    echo
    tail -1000 larStage$stage.err
    echo
  fi

  # Sam cleanups.

  # Get list of consumed files.

  ifdh translateConstraints "consumer_process_id $CPID and consumed_status consumed" > consumed_files${stage}.list

  # End consumer process.

  ifdh endProcess $PURL $CPID

  # Stop project (if appropriate).

  nprj=`ifdh translateConstraints "snapshot_for_project_name $SAM_PRJ_STAGE" | wc -l`
  nconsumed=`ifdh translateConstraints "project_name $SAM_PRJ_STAGE and consumed_status consumed" | wc -l`
  echo "$nprj files in project, $nconsumed files consumed so far."

  if [ $SAM_START -ne 0 -o \( $nprj -gt 0 -a $nconsumed -eq $nprj \) ]; then
    echo "Stopping project."
    ifdh endProject $PURL
  fi

  #If lar returns a status other than 0, do not move on to other stages
  if [ $stat -ne 0 ]; then
    break
  fi
 
  stage=$[$stage +1]
 
  #rename the mem and time profile DBs by stage
  
  if [ -f time.db ]; then
    mv time.db time${stage}.db
  fi
  if [ -f mem.db ]; then
    mv mem.db mem${stage}.db
  fi

done

# Done looping over stages.

# Setup up current version of ifdhc (may be different than version setup by larsoft).

echo "IFDHC_DIR=$IFDHC_DIR"

# Run optional end-of-job script.

if [ x$ENDSCRIPT != x ]; then
  echo "Running end-of-job script ${ENDSCRIPT}."
  if ! ./${ENDSCRIPT}; then
    exit $?
  fi
fi

# Do root file checks.

# Calculate root metadata for all data files and save as json file.
# If json metadata already exists, merge with newly geneated root metadata.

for datafile in *.root; do
  if [ -f $datafile ]; then
    json=${datafile}.json
    ./root_metadata.py $datafile > $json
  fi
done

#create a master lar.stat file which contains the overall exit code of all stages
stageStat=0
overallStat=0
while [ $stageStat -lt $nfcls ]; do
  stat=`cat larStage$stageStat.stat`
  overallStat=$[$stat+$overallStat]
  stageStat=$[$stageStat +1] 
done
echo $overallStat > lar.stat
valstat=$overallStat

# Make local output directories for files that we have to save.

mkdir out
mkdir log

# Stash all of the files we want to save in the local directories that we just created.

# First move data files and corresponding .json files into the out and log subdirectories.

for datafile in *.root; do
  if [ -f $datafile ]; then
    mv $datafile out
    if [ -f ${datafile}.json ]; then
      mv ${datafile}.json log
    fi
  fi
done

# Move any remaining files into the log subdirectory.

for outfile in *; do
  if [ -f $outfile ]; then
    mv $outfile log
  fi
done

# Do validation (if requested).

if [ $VALIDATE_IN_JOB -eq 1 ]; then

  # Do validation function for the whole job.

  valstat=$overallStat
  if [ $valstat -eq 0 ]; then
    curdir=`pwd`
    cd $curdir/log
    echo "./validate_in_job.py --dir $curdir/out --logfiledir $curdir/log --outdir $OUTDIR/$OUTPUT_SUBDIR --declare $DECLARE_IN_JOB --copy $COPY_TO_FTS --maintain_parentage 0 --data_file_type root"
    ./validate_in_job.py --dir $curdir/out --logfiledir $curdir/log --outdir $OUTDIR/$OUTPUT_SUBDIR --declare $DECLARE_IN_JOB --copy $COPY_TO_FTS --maintain_parentage 0 --data_file_type root
    valstat=$?
    cd $curdir
  fi
fi

# Make a tarball of the log directory contents, and save the tarball in the log directory.

rm -f log.tar
tar -cjf log.tar -C log .
mv log.tar log

# Create remote output and log directories.

export IFDH_CP_MAXRETRIES=5

echo "Make directory ${LOGDIR}/${OUTPUT_SUBDIR}."
date
ifdh mkdir $IFDH_OPT ${LOGDIR}/$OUTPUT_SUBDIR
echo "Done making directory ${LOGDIR}/${OUTPUT_SUBDIR}."
date

if [ ${OUTDIR} != ${LOGDIR} ]; then
  echo "Make directory ${OUTDIR}/${OUTPUT_SUBDIR}."
  date
  ifdh mkdir $IFDH_OPT ${OUTDIR}/$OUTPUT_SUBDIR
  echo "Done making directory ${OUTDIR}/${OUTPUT_SUBDIR}."
  date
fi

# Transfer tarball in log subdirectory.

statout=0
echo "ls log"
ls log
echo "ifdh cp -D $IFDH_OPT log/log.tar ${LOGDIR}/$OUTPUT_SUBDIR"
ifdh cp -D $IFDH_OPT log/log.tar ${LOGDIR}/$OUTPUT_SUBDIR
date
stat=$?
if [ $stat -ne 0 ]; then
  statout=1
  echo "ifdh cp failed with status ${stat}."
fi

# Transfer data files in out subdirectory.

if [ $COPY_TO_FTS -eq 0 ]; then

  if [ "$( ls -A out )" ]; then
    echo "ifdh cp -D $IFDH_OPT out/* ${OUTDIR}/$OUTPUT_SUBDIR"
    ifdh cp -D $IFDH_OPT out/* ${OUTDIR}/$OUTPUT_SUBDIR
    stat=$?
    if [ $stat -ne 0 ]; then
      statout=1
      echo "ifdh cp failed with status ${stat}."
    fi
  fi

fi  

if [ $statout -eq 0 -a -f log/lar.stat ]; then
  statout=`cat log/lar.stat`
fi

if [ $statout -eq 0 ]; then
  statout=$valstat
fi  

exit $statout
