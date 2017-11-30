#!/bin/bash

# ------------------------------------------------------------------------------------- #

# This is a script to run validation plots on MC including MC truth information and
# absolute performance metrics (eg. resolution)
# We call these scripts the "truth scripts" because they involve MC truth information
# (and therefore cannot be run on data) but they don't only plot true quantities.
# Reconstructed quantities and reco-truth can also be plotted.

# There are two options for how to run this script:
# 1) source runCItruth.sh MC_anatree_file.root MC_name short/long
# 2) source runCItruth.sh MC1_anatree_file.root MC1_name MC2_anatree_file.root MC2_name short/long

# Option 1) will make plots for one MC only
# Option 2) will make plots overlaying two MCs, so they can be compared by eye, and calculate
# the chi2 between them.

# - MC[1/2]_anatree_file.root should be a root file containing merged anatrees (O(>5k) events for
#   decent statistics
# - MC[1/2]_name should be the label you want to give this MC in the plot legend
# - short/long should be literally either "short" or "long". "short" is for the weekly CI validation
#   where we want to produce a reduced number of plots. "long" is for a full validation with
#   all the plots we can produce.

# ------------------------------------------------------------------------------------- #
    

g++ $(root-config --cflags --glibs) truthMonteCarloComparisonsScript.C -o truthMonteCarloComparisons

if [ -z "$4" ]; then
    ./truthMonteCarloComparisons ${1} ${2} ${3}
else
    ./truthMonteCarloComparisons ${1} ${2} ${3} ${4} "100" ${5}
fi
    
rm truthMonteCarloComparisons



