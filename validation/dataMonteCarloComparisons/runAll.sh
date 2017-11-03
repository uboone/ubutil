#!/bin/bash

# remember to use setup.sh to modify your input files and specify your options

source setup.sh

# appends trailing backslash to OUTDIR in case where it's not included
[ "${OUTDIR: -1}" != "/" ] && OUTDIR=${OUTDIR}/

g++ -o getTrackInformation getTrackInformation.C `root-config --cflags --glibs`
./getTrackInformation "$FILE1" "$FILE1_DATAORMC" "$FILE1_LABEL" "$FILE2" "$FILE2_DATAORMC" "$FILE2_LABEL" "$OUTDIR" "$COMP_TYPE" "$IS_CI" "$CHISQ_NOTIFIER" 

g++ -o getShowerInformation getShowerInformation.C `root-config --cflags --glibs`
./getShowerInformation "$FILE1" "$FILE1_DATAORMC" "$FILE1_LABEL" "$FILE2" "$FILE2_DATAORMC" "$FILE2_LABEL" "$OUTDIR" "$COMP_TYPE" "$IS_CI" "$CHISQ_NOTIFIER" 

g++ -o getHitInformation getHitInformation.C `root-config --cflags --glibs`
./getHitInformation "$FILE1" "$FILE1_DATAORMC" "$FILE1_LABEL" "$FILE2" "$FILE2_DATAORMC" "$FILE2_LABEL" "$OUTDIR" "$COMP_TYPE" "$IS_CI" "$CHISQ_NOTIFIER" 

g++ -o getFlashInformation getFlashInformation.C `root-config --cflags --glibs`
./getFlashInformation "$FILE1" "$FILE1_DATAORMC" "$FILE1_LABEL" "$FILE2" "$FILE2_DATAORMC" "$FILE2_LABEL" "$OUTDIR" "$COMP_TYPE" "$PE_CUT" "$IS_CI" "$CHISQ_NOTIFIER" 

g++ -o getNflsInformation getNflsInformation.C `root-config --cflags --glibs`
#./getNflsInformation "$FILE1" "$FILE1_DATAORMC" "$FILE1_LABEL" "$FILE2" "$FILE2_DATAORMC" "$FILE2_LABEL" "$OUTDIR" "$COMP_TYPE" "$PE_CUT" "opflashBeam" 10 "$IS_CI" "$CHISQ_NOTIFIER"
#./getNflsInformation "$FILE1" "$FILE1_DATAORMC" "$FILE1_LABEL" "$FILE2" "$FILE2_DATAORMC" "$FILE2_LABEL" "$OUTDIR" "$COMP_TYPE" "$PE_CUT" "opflashCosmic" 150 "$IS_CI" "$CHISQ_NOTIFIER"
./getNflsInformation "$FILE1" "$FILE1_DATAORMC" "$FILE1_LABEL" "$FILE2" "$FILE2_DATAORMC" "$FILE2_LABEL" "$OUTDIR" "$COMP_TYPE" "$PE_CUT" "simpleFlashBeam" 10 "$IS_CI" "$CHISQ_NOTIFIER" 
./getNflsInformation "$FILE1" "$FILE1_DATAORMC" "$FILE1_LABEL" "$FILE2" "$FILE2_DATAORMC" "$FILE2_LABEL" "$OUTDIR" "$COMP_TYPE" "$PE_CUT" "simpleFlashCosmic" 75 "$IS_CI" "$CHISQ_NOTIFIER" 

g++ -o getCalorimetryInformation getCalorimetryInformation.C `root-config --cflags --glibs`
./getCalorimetryInformation "$FILE1" "$FILE1_DATAORMC" "$FILE1_LABEL" "$FILE2" "$FILE2_DATAORMC" "$FILE2_LABEL" "$OUTDIR" "$COMP_TYPE" "$PE_CUT" "$IS_CI" "$CHISQ_NOTIFIER" 

#g++ -o getPMTInformation getPMTInformation.C `root-config --cflags --glibs`
#./getPMTInformation "$FILE1" "$FILE1_DATAORMC" "$FILE1_LABEL" "$FILE2" "$FILE2_DATAORMC" "$FILE2_LABEL" "$OUTDIR" "$COMP_TYPE" "$PE_CUT" "$THRESHOLD" "$CHISQ_NOTIFIER" 

rm getTrackInformation
rm getShowerInformation
rm getHitInformation
rm getFlashInformation
rm getCalorimetryInformation
rm getNflsInformation
rm getPMTInformation