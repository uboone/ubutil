#!/bin/bash

# remember to use setup.sh to modify your input files and specify your options

export IS_LOCAL=0

if [ $IS_LOCAL -eq 1 ]
then
  # MUST be run from directory containing scripts
  export UBUTIL_DIR="$PWD"
  mkdir ${UBUTIL_DIR}/bin
  cp ${UBUTIL_DIR}/*.* ${UBUTIL_DIR}/bin/
  #cd ${UBUTIL_DIR}/bin
fi

source ${UBUTIL_DIR}/bin/setup.sh $1 $2 $3 $4 $5 $6

# appends trailing backslash to OUTDIR in case where it's not included
[ "${OUTDIR: -1}" != "/" ] && OUTDIR=${OUTDIR}/

if [ $PE_CUT -gt 0 ]
then
  echo ">> Setup complete."
  echo ">> Output directory is ${OUTDIR}"
  echo ">> Compiling... "
  
  g++ -o getNflsInformation ${UBUTIL_DIR}/bin/getNflsInformation.C `root-config --cflags --glibs`
  
  echo ">> Done."
  echo ">> Running script."
  
  ./getNflsInformation "$FILE1" "$FILE1_DATAORMC" "$FILE1_LABEL" "$FILE2" "$FILE2_DATAORMC" "$FILE2_LABEL" "$OUTDIR" "$COMP_TYPE" "$PE_CUT" "opflashBeam" 10 "$IS_CI "$CHISQ_NOTIFIER" "
  ./getNflsInformation "$FILE1" "$FILE1_DATAORMC" "$FILE1_LABEL" "$FILE2" "$FILE2_DATAORMC" "$FILE2_LABEL" "$OUTDIR" "$COMP_TYPE" "$PE_CUT" "opflashCosmic" 150 "$IS_CI" "$CHISQ_NOTIFIER" 
  ./getNflsInformation "$FILE1" "$FILE1_DATAORMC" "$FILE1_LABEL" "$FILE2" "$FILE2_DATAORMC" "$FILE2_LABEL" "$OUTDIR" "$COMP_TYPE" "$PE_CUT" "simpleFlashBeam" 10 "$IS_CI" "$CHISQ_NOTIFIER" 
  ./getNflsInformation "$FILE1" "$FILE1_DATAORMC" "$FILE1_LABEL" "$FILE2" "$FILE2_DATAORMC" "$FILE2_LABEL" "$OUTDIR" "$COMP_TYPE" "$PE_CUT" "simpleFlashCosmic" 75 "$IS_CI" "$CHISQ_NOTIFIER" 

fi


rm getNflsInformation

if [ $IS_LOCAL -eq 1 ]
then
  #cd ..
  rm -rf ${UBUTIL_DIR}/bin
  unset UBUTIL_DIR
fi

