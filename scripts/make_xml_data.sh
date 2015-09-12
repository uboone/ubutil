#! /bin/bash
#----------------------------------------------------------------------
#
# Name: make_xml_data.sh
#
# Purpose: Make an xml file for reconstructing data.  Input is specified
#          in the form of sam dataset.
#
# Usage:
#
# make_xml_data.sh [-h|--help] [-d|--def <defname>] [-r|--release <release>] [-n|--name <name>] [-u|--user <user>] [-l|--local <dir|tar>] [--nev <n>] [--njob <n>]
#
# Options:
#
# -h|--help - Print help.
# -d|--def <defname> - Specify input dataset definition name.
# -r|--release <release> - Specify release.
# -n|--name <name> - Specify project name (default "datareco").
# -u|--user <user> - Use users/<user> as working and output directories
#                    (default is to use uboonepro).
# -l|--local <dir|tar> - Specify larsoft local directory or tarball.
# --nev <n> - Specify number of events (default 1000000).
# --njob <n> - Specify the number of jobs (default same as input files).
#
#----------------------------------------------------------------------

# Parse arguments.

def=''
rel=v04_21_01
name=datareco
userdir=uboonepro
userbase=$userdir
local=''
nev=1000000
njob=0

while [ $# -gt 0 ]; do
  case "$1" in

    # User directory.

    -h|--help )
      echo "Usage: make_xml_data.sh [-h|--help] [-d|--def <defname>] [-r|--release <release>] [-n|--name <name>] [-u|--user <user>] [-l|--local <dir|tar>] [--nev <n>] [--njob <n>]"
      exit
    ;;

    # Input dataset.

    -d|--def )
    if [ $# -gt 1 ]; then
      def=$2
      shift
    fi
    ;;

    # Release.

    -r|--release )
    if [ $# -gt 1 ]; then
      rel=$2
      shift
    fi
    ;;

    # Project name.

    -n|--name )
    if [ $# -gt 1 ]; then
      name=$2
      shift
    fi
    ;;

    # User.

    -u|--user )
    if [ $# -gt 1 ]; then
      userdir=users/$2
      userbase=$2
      shift
    fi
    ;;

    # Local release.

    -l|--local )
    if [ $# -gt 1 ]; then
      local=$2
      shift
    fi
    ;;

    # Total number of events.

    --nev )
    if [ $# -gt 1 ]; then
      nev=$2
      shift
    fi
    ;;

    # Number of events per job.

    --njob )
    if [ $# -gt 1 ]; then
      njob=$2
      shift
    fi
    ;;

  esac
  shift
done

# Make sure input dataset is specified.

if [ x$def = x ]; then
  echo "No input dataset specified."
  exit 1
fi

# If number of jobs is not specified, use number of files in input dataset.

if [ $njob = 0 ]; then
  njob=`samweb count-definition-files $def`
fi

# Get qualifier.

qual=e7

# Make xml name.

xml=${name}.xml
rm -f $xml
echo "Making ${xml}"

# Reco 1

reco1fcl=reco_uboone_data_stage_1.fcl

# Reco 2

reco2fcl=reco_uboone_data_stage_2_w_cluster3d.fcl

# Merge/Analysis

mergefcl=standard_ana_uboone.fcl

cat <<EOF > $xml
<?xml version="1.0"?>

<!-- Production Project -->

<!DOCTYPE project [
<!ENTITY release "$rel">
<!ENTITY file_type "data">
<!ENTITY run_type "physics">
<!ENTITY name "$name">
]>

<job>

<project name="&name;">

  <!-- Project size -->
  <numevents>$nev</numevents>

  <!-- Operating System -->
  <os>SL6</os>

  <!-- Batch resources -->
  <resource>DEDICATED,OPPORTUNISTIC</resource>

  <!-- Larsoft information -->
  <larsoft>
    <tag>&release;</tag>
    <qual>${qual}:prof</qual>
EOF
  if [ x$local != x ]; then
    echo "local=$local"
    echo "    <local>${local}</local>" >> $xml
  fi
  cat <<EOF >> $xml
  </larsoft>

  <!-- Project stages -->

  <stage name="reco1">
    <inputdef>$def</inputdef>
    <fcl>$reco1fcl</fcl>
    <outdir>/pnfs/uboone/scratch/${userdir}/&release;/&name;/reco1</outdir>
    <logdir>/uboone/data/users/${userbase}/&release;/&name;/reco1</logdir>
    <workdir>/uboone/data/users/${userbase}/work/&release;/&name;/reco1</workdir>
    <numjobs>$njob</numjobs>
    <datatier>reconstructed-2d</datatier>
    <defname>&name;_reco1</defname>
  </stage>

  <stage name="reco2">
    <fcl>$reco2fcl</fcl>
    <outdir>/pnfs/uboone/scratch/${userdir}/&release;/&name;/reco2</outdir>
    <logdir>/uboone/data/users/${userbase}/&release;/&name;/reco2</logdir>
    <workdir>/uboone/data/users/${userbase}/work/&release;/&name;/reco2</workdir>
    <numjobs>$njob</numjobs>
    <datatier>reconstructed-3d</datatier>
    <defname>&name;_reco2</defname>
  </stage>

  <stage name="mergeana">
    <fcl>$mergefcl</fcl>
    <outdir>/pnfs/uboone/scratch/${userdir}/&release;/&name;/mergeana</outdir>
    <logdir>/uboone/data/users/${userbase}/&release;/&name;/mergeana</logdir>
    <workdir>/uboone/data/users/${userbase}/work/&release;/&name;/mergeana</workdir>
    <numjobs>$njob</numjobs>
    <datatier>reconstructed</datatier>
    <anadatatier>root-tuple</anadatatier>
    <defname>&name;</defname>
    <anadefname>&name;_ana</anadefname>
  </stage>

  <!-- file type -->
  <filetype>&file_type;</filetype>

  <!-- run type -->
  <runtype>&run_type;</runtype>

</project>

</job>
EOF
