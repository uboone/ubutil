#!/bin/bash

source setup.sh

# appends trailing backslash to OUTDIR in case where it's not included
[ "${OUTDIR: -1}" != "/" ] && OUTDIR=${OUTDIR}/

g++ -o getFlashInformation getFlashInformation.C `root-config --cflags --glibs`
./getFlashInformation "$FILE1" "$FILE1_DATAORMC" "$FILE1_LABEL" "$FILE2" "$FILE2_DATAORMC" "$FILE2_LABEL" "$OUTDIR" "$COMP_TYPE" "$PE_CUT" "$IS_CI" "$CHISQ_NOTIFIER"  


rm getFlashInformation
