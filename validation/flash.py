#! /usr/bin/env python
###############################################################################
#
# Name: flash.py
# 
# Purpose: Make and save flash validation histograms to a root file.
#
# Authors: Tingjun Yang
#
# Usage:
#
# flash.py <options>
#
# Options:
#
# --input <inputfile>       - Input AnalysisTree root file.
#
# --output <outputfile>     - Output root file that contain histograms.
#
# --dataset <dataset name>  - Specify a dataset name, singlemu or BNB etc.
#                             All histograms will be saved in output:flash/dataset
#
# --dir <directory name>    - Specify a directory to dump .root file
#			      (if no directory is specified, the root file will be 
# 			      stored in the current directory)	
#
###############################################################################
import sys,os
# Prevent root from printing garbage on initialization.
if os.environ.has_key('TERM'):
    del os.environ['TERM']

# Hide command line arguments from ROOT module.
myargv = sys.argv
sys.argv = myargv[0:1]

from ROOT import TFile, TCanvas, TH1F, TH2F, TProfile
from ROOT import gDirectory, gROOT
#ROOT.gErrorIgnoreLevel = ROOT.kError
sys.argv = myargv
from validation_utilities import *

def help():

    filename = sys.argv[0]
    file = open(filename, 'r')

    doprint=0
    
    for line in file.readlines():
        if line[2:10] == 'flash.py':
            doprint = 1
        elif line[0:6] == '######' and doprint:
            doprint = 0
        if doprint:
            if len(line) > 2:
                print line[2:],
            else:
                print


def main(argv):
    infile = '/pnfs/uboone/scratch/users/tjyang/output/v03_08_01/ana/prod_muminus_0.1-2.0GeV_isotropic_uboone/anahist.root'
    outfile = 'flash.root'
    dataset = 'histdir'
    outdir = ''
    args = argv[1:]
    while len(args) > 0:
        if args[0] == '-h' or args[0] == '--help':
            help()
            return 0
        elif args[0] == '--input' and len(args) > 1:
            infile = args[1]
            del args[0:2]
        elif args[0] == '--output' and len(args) > 1:
            outfile = args[1]
            del args[0:2]
	elif args[0] == '--dir' and len(args) > 1:
	    outdir = args[1]
	    del args[0:2]     
        elif args[0] == '--dataset' and len(args) > 1:
            dataset = args[1]
            del args[0:2]
        else:
            print 'Unkonw option %s' % args[0]
            return 1

    # open the file
    myfile = TFile(infile)

    mychain = gDirectory.Get('analysistree/anatree')

    mychain.SetBranchStatus("*",0);
    mychain.SetBranchStatus("no_flashes",1);
    mychain.SetBranchStatus("flash_*",1);
    
    if outdir == '':
    	 outdir = os.getcwd()
    
    if not os.path.exists(outdir):
    	os.makedirs(outdir)
    os.chdir(outdir)
    
    hfile = gROOT.FindObject(outfile)
    if hfile:
        hfile.Close()
    hfile = TFile(outfile, 'RECREATE')
    
    dir1 = hfile.mkdir('flash')
    dir1.cd()

    if dataset!='':
        dir2 = dir1.mkdir(dataset)
        dir2.cd()

    hno_flashes = TH1F('hno_flashes'+dataset,dataset+';Number of flashes;Number of events',100,0,200)
    fillhno_flashes = hno_flashes.Fill
    hflash_time = TH1F('hflash_time'+dataset,dataset+';Flash time (#mus);Number of flashes',100,-2000,5500)
    fillhflash_time = hflash_time.Fill
    hflash_pe = TH1F('hflash_pe'+dataset,dataset+';Flash PE;Number of flashes',100,0,10)
    fillhflash_pe = hflash_pe.Fill
    hflash_ycenter = TH1F('hflash_ycenter'+dataset,dataset+';Flash YCenter;Number of flashes',100,-80,130)
    fillhflash_ycenter = hflash_ycenter.Fill
    hflash_zcenter = TH1F('hflash_zcenter'+dataset,dataset+';Flash ZCenter;Number of flashes',100,0,1500)
    fillhflash_zcenter = hflash_zcenter.Fill


    vno_flashes = array("i",[0])
    mychain.SetBranchAddress("no_flashes",vno_flashes)
    vflash_time = array("f",[0]*1000)
    mychain.SetBranchAddress("flash_time",vflash_time)
    vflash_pe = array("f",[0]*1000)
    mychain.SetBranchAddress("flash_pe",vflash_pe)
    vflash_ycenter = array("f",[0]*1000)
    mychain.SetBranchAddress("flash_ycenter",vflash_ycenter)
    vflash_zcenter = array("f",[0]*1000)
    mychain.SetBranchAddress("flash_zcenter",vflash_zcenter)

    entries = mychain.GetEntriesFast()
    #entries = 100

    for jentry in xrange( entries ):

        if jentry%1000==0:
            print jentry,"/",entries
    
        # get the next tree in the chain and verify
        ientry = mychain.LoadTree( jentry )
        if ientry < 0:
            break
    
        # copy next entry into memory and verify
        nb = mychain.GetEntry( jentry )
        if nb <= 0:
            continue
        
        nflashes = vno_flashes[0]
        fillhno_flashes(nflashes)
        if nflashes > 1000:
            nflashes = 1000
        for i in range(nflashes):
            fillhflash_time(vflash_time[i])
            fillhflash_pe(vflash_pe[i])
            fillhflash_ycenter(vflash_ycenter[i])
            fillhflash_zcenter(vflash_zcenter[i])

    del fillhno_flashes
    del fillhflash_time
    del fillhflash_pe
    del fillhflash_ycenter
    del fillhflash_zcenter

    hfile.Write()
    
    currdir = os.getcwd()
    if outdir != currdir:
    	os.chdir(currdir)

if __name__ == '__main__':
    rc = main(sys.argv)
    sys.exit(rc)
