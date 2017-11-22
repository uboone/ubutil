#!/bin/bash

source setup.sh

# appends trailing backslash to OUTDIR in case where it's not included
[ "${OUTDIR: -1}" != "/" ] && OUTDIR=${OUTDIR}/

g++ -o getNflsInformation getNflsInformation.C `root-config --cflags --glibs`
./getNflsInformation "$FILE1" "$FILE1_DATAORMC" "$FILE1_LABEL" "$FILE2" "$FILE2_DATAORMC" "$FILE2_LABEL" "$OUTDIR" "$COMP_TYPE" "$PE_CUT" "opflashBeam" 10 "$IS_CI "$CHISQ_NOTIFIER" "
./getNflsInformation "$FILE1" "$FILE1_DATAORMC" "$FILE1_LABEL" "$FILE2" "$FILE2_DATAORMC" "$FILE2_LABEL" "$OUTDIR" "$COMP_TYPE" "$PE_CUT" "opflashCosmic" 150 "$IS_CI" "$CHISQ_NOTIFIER" 
./getNflsInformation "$FILE1" "$FILE1_DATAORMC" "$FILE1_LABEL" "$FILE2" "$FILE2_DATAORMC" "$FILE2_LABEL" "$OUTDIR" "$COMP_TYPE" "$PE_CUT" "simpleFlashBeam" 10 "$IS_CI" "$CHISQ_NOTIFIER" 
./getNflsInformation "$FILE1" "$FILE1_DATAORMC" "$FILE1_LABEL" "$FILE2" "$FILE2_DATAORMC" "$FILE2_LABEL" "$OUTDIR" "$COMP_TYPE" "$PE_CUT" "simpleFlashCosmic" 75 "$IS_CI" "$CHISQ_NOTIFIER" 

rm getNflsInformation
