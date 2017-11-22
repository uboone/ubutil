# dataMonteCarloComparisons

configurations can be set in any one of the .sh files.

*Designed to have a single hadded anatree as input.* I cannot emphasise this enough: **if you do not hadd your anatrees it is going to take a very long time**. It may seem to waste time up-front but will save you a tonne of time in the long run.

You can modify the tracking/flash algorithms which are used by modifying the algoNames vector in get(*)Information.C files. You can modify the plots which are produced by modifying the (*)PlotNames vector in the get(*)Information code, but note that the (*)PlotValues (which holds the binning, and xlow/xhigh) will have to be similarly modified.

All environment variables are set in setup.sh which is called by other scripts, i.e:

### Usage
- Add target anatree files, labels, output files, and set things like the flash PE cut by modifying setup.sh.
- Run all of the plots together by typing `runAll.sh` else, choose which specific plots you want to produce
