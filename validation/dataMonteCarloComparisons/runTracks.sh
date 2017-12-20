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

g++ -o getTrackInformation getTrackInformation.C `root-config --cflags --glibs`
./getTrackInformation "$FILE1" "$FILE1_DATAORMC" "$FILE1_LABEL" "$FILE2" "$FILE2_DATAORMC" "$FILE2_LABEL" "$OUTDIR" "$COMP_TYPE" "$IS_CI" "$CHISQ_NOTIFIER"

rm getTrackInformation
if [ $IS_LOCAL -eq 1 ]
then
  cd ..
  rm -rf bin
fi
