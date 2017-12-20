#!/bin/bash

# remember to use setup.sh to modify your input files and specify your options

source ${UBUTIL_DIR}/bin/setup.sh $1 $2 $3 $4 $5 $6

# appends trailing backslash to OUTDIR in case where it's not included
[ "${OUTDIR: -1}" != "/" ] && OUTDIR=${OUTDIR}/

g++ -o getTrackInformation ${UBUTIL_DIR}/bin/getTrackInformation.C `root-config --cflags --glibs`
./getTrackInformation "$FILE1" "$FILE1_DATAORMC" "$FILE1_LABEL" "$FILE2" "$FILE2_DATAORMC" "$FILE2_LABEL" "$OUTDIR" "$COMP_TYPE" "$IS_CI" "$CHISQ_NOTIFIER" 

g++ -o getShowerInformation ${UBUTIL_DIR}/bin/getShowerInformation.C `root-config --cflags --glibs`
./getShowerInformation "$FILE1" "$FILE1_DATAORMC" "$FILE1_LABEL" "$FILE2" "$FILE2_DATAORMC" "$FILE2_LABEL" "$OUTDIR" "$COMP_TYPE" "$IS_CI" "$CHISQ_NOTIFIER" 

g++ -o getHitInformation ${UBUTIL_DIR}/bin/getHitInformation.C `root-config --cflags --glibs`
./getHitInformation "$FILE1" "$FILE1_DATAORMC" "$FILE1_LABEL" "$FILE2" "$FILE2_DATAORMC" "$FILE2_LABEL" "$OUTDIR" "$COMP_TYPE" "$IS_CI" "$CHISQ_NOTIFIER" 

g++ -o getFlashInformation ${UBUTIL_DIR}/bin/getFlashInformation.C `root-config --cflags --glibs`
./getFlashInformation "$FILE1" "$FILE1_DATAORMC" "$FILE1_LABEL" "$FILE2" "$FILE2_DATAORMC" "$FILE2_LABEL" "$OUTDIR" "$COMP_TYPE" "$PE_CUT" "$IS_CI" "$CHISQ_NOTIFIER" 

if [ $PE_CUT -gt 0 ]
then
  g++ -o getNflsInformation ${UBUTIL_DIR}/bin/getNflsInformation.C `root-config --cflags --glibs`
  ./getNflsInformation "$FILE1" "$FILE1_DATAORMC" "$FILE1_LABEL" "$FILE2" "$FILE2_DATAORMC" "$FILE2_LABEL" "$OUTDIR" "$COMP_TYPE" "$PE_CUT" "opflashBeam" 10 "$IS_CI" "$CHISQ_NOTIFIER"
  ./getNflsInformation "$FILE1" "$FILE1_DATAORMC" "$FILE1_LABEL" "$FILE2" "$FILE2_DATAORMC" "$FILE2_LABEL" "$OUTDIR" "$COMP_TYPE" "$PE_CUT" "opflashCosmic" 150 "$IS_CI" "$CHISQ_NOTIFIER"
  ./getNflsInformation "$FILE1" "$FILE1_DATAORMC" "$FILE1_LABEL" "$FILE2" "$FILE2_DATAORMC" "$FILE2_LABEL" "$OUTDIR" "$COMP_TYPE" "$PE_CUT" "simpleFlashBeam" 10 "$IS_CI" "$CHISQ_NOTIFIER" 
  ./getNflsInformation "$FILE1" "$FILE1_DATAORMC" "$FILE1_LABEL" "$FILE2" "$FILE2_DATAORMC" "$FILE2_LABEL" "$OUTDIR" "$COMP_TYPE" "$PE_CUT" "simpleFlashCosmic" 75 "$IS_CI" "$CHISQ_NOTIFIER" 
fi
g++ -o getCalorimetryInformation ${UBUTIL_DIR}/bin/getCalorimetryInformation.C `root-config --cflags --glibs`
./getCalorimetryInformation "$FILE1" "$FILE1_DATAORMC" "$FILE1_LABEL" "$FILE2" "$FILE2_DATAORMC" "$FILE2_LABEL" "$OUTDIR" "$COMP_TYPE" "$IS_CI" "$CHISQ_NOTIFIER" 

#g++ -o getPMTInformation getPMTInformation.C `root-config --cflags --glibs`
#./getPMTInformation "$FILE1" "$FILE1_DATAORMC" "$FILE1_LABEL" "$FILE2" "$FILE2_DATAORMC" "$FILE2_LABEL" "$OUTDIR" "$COMP_TYPE" "$PE_CUT" "$THRESHOLD" "$CHISQ_NOTIFIER" 

rm getTrackInformation
rm getShowerInformation
rm getHitInformation
rm getFlashInformation
rm getCalorimetryInformation
rm getNflsInformation
#rm getPMTInformation
