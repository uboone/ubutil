#!/bin/bash

if [[ $UBUTIL_DIR == "/cvmfs"* ]]
then
  echo "not running locally."
  source ${UBUTIL_DIR}/bin/setup.sh $1 $2 $3 $4 $5 $6
  export IS_LOCAL=0
else
  echo "running locally."
  source setup.sh $1 $2 $3 $4 $5 $6
  export IS_LOCAL=1
fi

if [ $IS_LOCAL -eq 1 ]
then

  mkdir bin
  cp *.* bin/
  cd bin
  export UBUTIL_DIR="${PWD}/../"

fi

# appends trailing backslash to OUTDIR in case where it's not included
[ "${OUTDIR: -1}" != "/" ] && OUTDIR=${OUTDIR}/

if [ $PE_CUT -gt 0 ]
then
g++ -o getNflsInformation getNflsInformation.C `root-config --cflags --glibs`
  ./getNflsInformation "$FILE1" "$FILE1_DATAORMC" "$FILE1_LABEL" "$FILE2" "$FILE2_DATAORMC" "$FILE2_LABEL" "$OUTDIR" "$COMP_TYPE" "$PE_CUT" "opflashBeam" 10 "$IS_CI "$CHISQ_NOTIFIER" "
  ./getNflsInformation "$FILE1" "$FILE1_DATAORMC" "$FILE1_LABEL" "$FILE2" "$FILE2_DATAORMC" "$FILE2_LABEL" "$OUTDIR" "$COMP_TYPE" "$PE_CUT" "opflashCosmic" 150 "$IS_CI" "$CHISQ_NOTIFIER" 
  ./getNflsInformation "$FILE1" "$FILE1_DATAORMC" "$FILE1_LABEL" "$FILE2" "$FILE2_DATAORMC" "$FILE2_LABEL" "$OUTDIR" "$COMP_TYPE" "$PE_CUT" "simpleFlashBeam" 10 "$IS_CI" "$CHISQ_NOTIFIER" 
  ./getNflsInformation "$FILE1" "$FILE1_DATAORMC" "$FILE1_LABEL" "$FILE2" "$FILE2_DATAORMC" "$FILE2_LABEL" "$OUTDIR" "$COMP_TYPE" "$PE_CUT" "simpleFlashCosmic" 75 "$IS_CI" "$CHISQ_NOTIFIER" 
fi

rm getNflsInformation
if [ $IS_LOCAL -eq 1 ]
then
  cd ..
  rm -rf bin
fi
