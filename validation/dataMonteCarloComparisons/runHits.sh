#!/bin/bash

export IS_LOCAL=0

if [ $IS_LOCAL -eq 1 ]
then
  # MUST be run from directory containing scripts
  export UBUTIL_DIR="$PWD"
  mkdir ${UBUTIL_DIR}/bin
  cp ${UBUTIL_DIR}/*.* ${UBUTIL_DIR}/bin/
  #cd ${UBUTIL_DIR}/bin
fi

# appends trailing backslash to OUTDIR in case where it's not included
[ "${OUTDIR: -1}" != "/" ] && OUTDIR=${OUTDIR}/

g++ -o getHitInformation ${UBUTIL_DIR}/bin/getHitInformation.C `root-config --cflags --glibs`
./getHitInformation "$FILE1" "$FILE1_DATAORMC" "$FILE1_LABEL" "$FILE2" "$FILE2_DATAORMC" "$FILE2_LABEL" "$OUTDIR" "$COMP_TYPE" "$IS_CI" "$CHISQ_NOTIFIER" 

rm getHitInformation

if [ $IS_LOCAL -eq 1 ]
then
  #cd ..
  rm -rf ${UBUTIL_DIR}/bin
  unset UBUTIL_DIR
fi

