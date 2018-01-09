#!/bin/bash

# remember to use setup.sh to modify your input files and specify your options

export IS_LOCAL=0

if [ $IS_LOCAL -eq 1 ]
then
  # MUST be run from directory containing scripts
  export UBUTIL_DIR="$PWD"
  mkdir ${UBUTIL_DIR}/bin
  cp ${UBUTIL_DIR}/*.* ${UBUTIL_DIR}/bin/
  cd ${UBUTIL_DIR}/bin
fi

source ${UBUTIL_DIR}/bin/setup.sh $1 $2 $3 $4 $5 $6

# appends trailing backslash to OUTDIR in case where it's not included
[ "${OUTDIR: -1}" != "/" ] && OUTDIR=${OUTDIR}/

g++ -o getTrackInformation getTrackInformation.C `root-config --cflags --glibs`
./getTrackInformation "$FILE1" "$FILE1_DATAORMC" "$FILE1_LABEL" "$FILE2" "$FILE2_DATAORMC" "$FILE2_LABEL" "$OUTDIR" "$COMP_TYPE" "$IS_CI" "$CHISQ_NOTIFIER" "$TRACKLENGTH" 

rm getTrackInformation

if [ $IS_LOCAL -eq 1 ]
then
  cd ..
  rm -rf ${UBUTIL_DIR}/bin
  unset UBUTIL_DIR
fi
