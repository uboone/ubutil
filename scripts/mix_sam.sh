#! /bin/bash
#------------------------------------------------------------------
#
# Purpose: This script is intended to be run inside condor_lar.sh
#          using the initialization script hook.  It makes a wrapper
#          fcl file that overrides certain fcl parameters used by
#          module OverlayRawDataMicroBooNE, specifically:
#
#          physics.filters.mixer.fileNames
#          physics.filters.mixer.detail.SamDefname
#          physics.filters.mixer.detail.SamProject
#          physics.filters.mixer.detail.SamAppVersion
#
# Created: H. Greenlee, 2-Sep-2016
#
#------------------------------------------------------------------

# Make sure batch environment variables needed by this script are defined.

if [ x$FCL = x ]; then
  echo "Variable FCL not defined."
  exit 1
fi

if [ x$MIX_DEFNAME = x ]; then
  echo "Variable MIX_DEFNAME not defined."
  exit 1
fi

if [ x$MIX_PROJECT = x ]; then
  echo "Variable MIX_PROJECT not defined."
  exit 1
fi

if [ x$UBOONECODE_VERSION = x ]; then
  echo "Variable UBOONECODE_VERSION not defined."
  exit 1
fi

# Make sure fcl file $FCL exists.

if [ ! -f $FCL ]; then
  echo "Fcl file $FCL does not exist."
  exit 1
fi

# Rename the existing fcl file $FCL to something else.

mv $FCL mix_wrapper.fcl

# Generate wrapper.

cat <<EOF > $FCL
#include "mix_wrapper.fcl"

physics.filters.mixer.fileNames: []
physics.filters.mixer.detail.SamDefname: $MIX_DEFNAME
physics.filters.mixer.detail.SamProject: $MIX_PROJECT
physics.filters.mixer.detail.SamAppVersion: $UBOONECODE_VERSION

EOF

# Make sure IFDH service is configured in fcl file.

if ! lar --debug-config=/dev/stdout -c $FCL | grep -q IFDH:; then
  cat <<EOF >> $FCL
services.IFDH:
{
}

EOF
fi
