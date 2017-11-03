##
## Adam Lister and Daniel Devitt
## Date: 03 Nov 2017
## Contact: a.lister1@lancaster.ac.uk
##

#!/bin/bash

# is this continuous integration? If so produce subsample of plots
export IS_CI=0

# value of chisq which defines a bad plot which should be checked by hand
# CHISQ_NOTIFIER = chisq value * 100, i.e. 100 = chisq of 1, 150 = chisq of 1.5
export CHISQ_NOTIFIER=300

# should be either data, or base MC to compare to
export FILE1="/uboone/data/users/kduffy/miniretreat_oct17/mcc8-4_anatree_extunbiased_data_anamerged.root"
export FILE1_DATAORMC="DATA"
export FILE1_LABEL="DATA (EXT-UB)"

# should be MC
export FILE2="/uboone/data/users/alister1/anatree.root"
export FILE2_DATAORMC="MC"
export FILE2_LABEL="MC (CORSIKA)"

# output dir
export OUTDIR="/uboone/data/users/alister1/datamctest2/"

# comparison type 0: area normalised 1: not area normalised
export COMP_TYPE=0

# Flash PE cut (ignored if < 0)
export PE_CUT=-1

# PE cut per PMT (ignored if < 0)
export THRESHOLD=-1
