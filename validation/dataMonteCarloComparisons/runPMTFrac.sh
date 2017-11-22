#!/bin/bash

source setup.sh

# appends trailing backslash to OUTDIR in case where it's not included
[ "${OUTDIR: -1}" != "/" ] && OUTDIR=${OUTDIR}/

g++ -o getPMTFracInformation getPMTFracInformation.C `root-config --cflags --glibs`
./getPMTFracInformation "$FILE1" "$FILE1_DATAORMC" "$FILE1_LABEL" "$FILE2" "$FILE2_DATAORMC" "$FILE2_LABEL" "$OUTDIR" "$CHISQ_NOTIFIER" 

rm getPMTFracInformation
