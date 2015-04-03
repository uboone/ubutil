#! /bin/bash
#----------------------------------------------------------------------
#
# Name: make_xml_mcc6a.0.sh
#
# Purpose: Make xml files for mcc 6.0.  This script loops over all
#          generator-level fcl files in the source area of the currently 
#          setup version of uboonecode (that is, under 
#          $UBOONECODE_DIR/source/fcl/gen), and makes a corresponding xml
#          project file in the local directory.
#
#          This version of this script makes two xml project files for
#          each generator file.  One project runs simulation (stages gen
#          through detsim).  The second project runs reconstruction (stages
#          reco1 through mergeana).  The two projects may have different
#          larsoft/uboonecode versions.
#
# Usage:
#
# make_xml_mcc6.0.sh [-h|--help] [-rs <sim-release>] [-rr <reco-release>] [-u|--user <user>] [--local <dir|tar>] [--nev <n>] [--nevjob <n>] [--nevgjob <n>]
#
# Options:
#
# -h|--help     - Print help.
# -rs <release> - Use the specified larsoft/uboonecode release for simulation.
# -rr <release> - Use the specified larsoft/uboonecode release for reconstruction.
# -t|--tag <tag> - Specify sample tag (default "mcc6.0").
# -u|--user <user> - Use users/<user> as working and output directories
#                    (default is to use uboonepro).
# --local <dir|tar> - Specify larsoft local directory or tarball (xml 
#                     <local>...</local>).
# --nev <n>     - Specify number of events for all samples.  Otherwise
#                 use hardwired defaults.
# --nevjob <n>  - Specify the default number of events per job.
# --nevgjob <n> - Specify the maximum number of events per gen/g4 job.
#
#----------------------------------------------------------------------

# Parse arguments.

rs=v04_03_01
rr=v04_03_03
userdir=uboonepro
userbase=$userdir
nevarg=0
nevjob=100
nevgjobarg=0
local=''
tag=mcc6.0

while [ $# -gt 0 ]; do
  case "$1" in

    # User directory.

    -h|--help )
      echo "Usage: make_xml_mcc6.0.sh [-h|--help] [-rs <sim-release>] [-rr <reco-release>] [-t|--tag <tag>] [-u|--user <user>] [--local <dir|tar>] [--nev <n>] [--nevjob <n>] [--nevgjob <n>]"
      exit
    ;;

    # Simulation release.

    -rs )
    if [ $# -gt 1 ]; then
      rs=$2
      shift
    fi
    ;;

    # Reconstruction release.

    -rr )
    if [ $# -gt 1 ]; then
      rr=$2
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

    --local )
    if [ $# -gt 1 ]; then
      local=$2
      shift
    fi
    ;;

    # Total number of events.

    --nev )
    if [ $# -gt 1 ]; then
      nevarg=$2
      shift
    fi
    ;;

    # Number of events per job.

    --nevjob )
    if [ $# -gt 1 ]; then
      nevjob=$2
      shift
    fi
    ;;

    # Number of events per gen/g4 job.

    --nevgjob )
    if [ $# -gt 1 ]; then
      nevgjobarg=$2
      shift
    fi
    ;;

    # Sample tag.

    -t|--tag )
    if [ $# -gt 1 ]; then
      tag=$2
      shift
    fi
    ;;

  esac
  shift
done

# Get qualifier.

qual=e7

# Delete existing xml files.

rm -f *.xml

# Loop over existing generator fcl files.

find $UBOONECODE_DIR/source/fcl/gen -name \*.fcl | while read fcl
do
  if ! echo $fcl | grep -q common; then
    newprj=`basename $fcl .fcl`
    simxml=${newprj}.xml
    recoxml=${newprj}_reco.xml
    filt=1

    # Make xml file.

    echo "Making ${newprj}.xml"

    # Generator

    genfcl=`basename $fcl`

    # G4

    g4fcl=standard_g4_uboone.fcl
    if echo $newprj | grep -q dirt; then
      g4fcl=standard_g4_dirt_uboone.fcl
    fi

    # Detsim (optical + tpc).

    detsimfcl=standard_detsim_uboone.fcl
    if echo $newprj | grep -q dirt; then
      detsimfcl=standard_detsim_uboone_tpcfilt.fcl
      if echo $newprj | grep -q bnb; then
        filt=25
      else
        filt=20
      fi
    fi

    # Reco 1

    reco1fcl=reco_uboone_stage_1.fcl

    # Reco 2

    reco2fcl=reco_uboone_stage_2.fcl

    # Merge/Analysis

    mergefcl=standard_ana_uboone.fcl

    # Set number of gen/g4 events per job.

    nevgjob=$nevgjobarg
    if [ $nevgjob -eq 0 ]; then
      if echo $newprj | grep -q dirt; then
        if echo $newprj | grep -q cosmic; then
          nevgjob=200
        else
          nevgjob=2000
        fi
      else
        nevgjob=nevjob
      fi
    fi

    # Set number of events.

    nev=$nevarg
    if [ $nev -eq 0 ]; then
      if [ $newprj = prodgenie_bnb_nu_cosmic_uboone ]; then
        nev=200000
      elif [ $newprj = prodgenie_bnb_nu_uboone ]; then
        nev=200000
      elif [ $newprj = prodgenie_bnb_nue_cosmic_uboone ]; then
        nev=20000
      elif [ $newprj = prodgenie_bnb_nue_uboone ]; then
        nev=20000
      elif [ $newprj = prodgenie_bnb_intrinsic_nue_uboone ]; then
        nev=20000
      elif [ $newprj = prodcosmics_uboone ]; then
        nev=200000
      else
        nev=10000
      fi
    fi
    nev=$(( $nev * $filt ))

    # Calculate the number of worker jobs.

    njob1=$(( $nev / $nevgjob ))         # Pre-filter (gen, g4)
    njob2=$(( $nev / $nevjob / $filt ))  # Post-filter (detsim and later)
    if [ $njob1 -lt $njob2 ]; then
      njob1=$njob2
    fi

  cat <<EOF > $simxml
<?xml version="1.0"?>

<!-- Production Project -->

<!DOCTYPE project [
<!ENTITY release "$rs">
<!ENTITY file_type "mc">
<!ENTITY run_type "physics">
<!ENTITY name "$newprj">
<!ENTITY tag "$tag">
]>

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
    echo "    <local>${local}</local>" >> $simxml
  fi
  cat <<EOF >> $simxml
  </larsoft>

  <!-- Project stages -->

  <stage name="gen">
    <fcl>$genfcl</fcl>
    <outdir>/pnfs/uboone/scratch/${userdir}/&tag;/&release;/gen/&name;</outdir>
    <logdir>/uboone/data/users/${userbase}/&tag;/&release;/gen/&name;</logdir>
    <workdir>/uboone/data/users/${userbase}/work/&tag;/&release;/gen/&name;</workdir>
    <output>${newprj}_\${PROCESS}_%tc_gen.root</output>
    <numjobs>$njob1</numjobs>
    <datatier>generated</datatier>
    <defname>&name;_&tag;_gen</defname>
  </stage>

  <stage name="g4">
    <fcl>$g4fcl</fcl>
    <outdir>/pnfs/uboone/scratch/${userdir}/&tag;/&release;/g4/&name;</outdir>
    <logdir>/uboone/data/users/${userbase}/&tag;/&release;/g4/&name;</logdir>
    <workdir>/uboone/data/users/${userbase}/work/&tag;/&release;/g4/&name;</workdir>
    <numjobs>$njob1</numjobs>
    <datatier>simulated</datatier>
    <defname>&name;_&tag;_g4</defname>
  </stage>

  <stage name="detsim">
    <fcl>$detsimfcl</fcl>
    <outdir>/pnfs/uboone/scratch/${userdir}/&tag;/&release;/detsim/&name;</outdir>
    <logdir>/uboone/data/users/${userbase}/&tag;/&release;/detsim/&name;</logdir>
    <workdir>/uboone/data/users/${userbase}/work/&tag;/&release;/detsim/&name;</workdir>
    <numjobs>$njob2</numjobs>
    <datatier>detector-simulated</datatier>
    <defname>&name;_&tag;_detsim</defname>
  </stage>

  <!-- file type -->
  <filetype>&file_type;</filetype>

  <!-- run type -->
  <runtype>&run_type;</runtype>

</project>
EOF

  cat <<EOF > $recoxml
<?xml version="1.0"?>

<!-- Production Project -->

<!DOCTYPE project [
<!ENTITY release "$rr">
<!ENTITY file_type "mc">
<!ENTITY run_type "physics">
<!ENTITY name "${newprj}">
<!ENTITY tag "$tag">
]>

<project name="&name;_reco">

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
    echo "    <local>${local}</local>" >> $recoxml
  fi
  cat <<EOF >> $recoxml
  </larsoft>

  <!-- Project stages -->

  <stage name="reco1">
    <fcl>$reco1fcl</fcl>
    <inputlist>/uboone/data/users/${userbase}/&tag;/${rs}/detsim/&name;/files.list</inputlist>
    <outdir>/pnfs/uboone/scratch/${userdir}/&tag;/&release;/reco1/&name;</outdir>
    <logdir>/uboone/data/users/${userbase}/&tag;/&release;/reco1/&name;</logdir>
    <workdir>/uboone/data/users/${userbase}/work/&tag;/&release;/reco1/&name;</workdir>
    <numjobs>$njob2</numjobs>
    <datatier>reconstructed-2d</datatier>
    <defname>&name;_&tag;_reco1</defname>
  </stage>

  <stage name="reco2">
    <fcl>$reco2fcl</fcl>
    <outdir>/pnfs/uboone/scratch/${userdir}/&tag;/&release;/reco2/&name;</outdir>
    <logdir>/uboone/data/users/${userbase}/&tag;/&release;/reco2/&name;</logdir>
    <workdir>/uboone/data/users/${userbase}/work/&tag;/&release;/reco2/&name;</workdir>
    <numjobs>$njob2</numjobs>
    <datatier>reconstructed-3d</datatier>
    <defname>&name;_&tag;_reco2</defname>
  </stage>

  <stage name="mergeana">
    <fcl>$mergefcl</fcl>
    <outdir>/pnfs/uboone/scratch/${userdir}/&tag;/&release;/mergeana/&name;</outdir>
    <logdir>/uboone/data/users/${userbase}/&tag;/&release;/mergeana/&name;</logdir>
    <workdir>/uboone/data/users/${userbase}/work/&tag;/&release;/mergeana/&name;</workdir>
    <numjobs>$njob2</numjobs>
    <targetsize>8000000000</targetsize>
    <datatier>reconstructed-3d</datatier>
    <defname>&name;_&tag;</defname>
  </stage>

  <!-- file type -->
  <filetype>&file_type;</filetype>

  <!-- run type -->
  <runtype>&run_type;</runtype>

</project>
EOF

done