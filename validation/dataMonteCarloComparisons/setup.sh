##
## Adam Lister and Daniel Devitt
## Date: 03 Nov 2017
## Contact: a.lister1@lancaster.ac.uk
##

## Example running:
## ./runAll "/path/to/data" "DATA" "DATALABEL" "/path/to/mc" "MC" "MCLABEL"

#!/bin/bash

# is this continuous integration? If so produce subsample of plots
export IS_CI=1

# value of chisq which defines a bad plot which should be checked by hand
# CHISQ_NOTIFIER = chisq value * 100, i.e. 100 = chisq of 1, 150 = chisq of 1.5
export CHISQ_NOTIFIER=300

# should be either data, or base MC to compare to
export FILE1=$1
export FILE1_DATAORMC=$2
export FILE1_LABEL=$3

# should be MC
export FILE2=$4
export FILE2_DATAORMC=$5
export FILE2_LABEL=$6

# output dir
export OUTDIR="/uboone/data/users/alister1/dmctest/"
#export OUTDIR="."
#export OUTDIR="/pnfs/uboone/scratch/users/uboone/ci_validation/"

# comparison type 0: area normalised 1: not area normalised
export COMP_TYPE=0

# Flash PE cut (ignored if < 0)
export PE_CUT=-1

# PE cut per PMT (ignored if < 0)
export THRESHOLD=-1
