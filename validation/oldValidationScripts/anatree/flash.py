#! /usr/bin/env python
##################################################################################
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
# --input <inputfile>               - Input AnalysisTree root file.
#
# --output <outputfile>             - Output root file that contain histograms.
#
# --flashalg <flash algorithm name> - Optional. Can be separated by commas.
#                                     If not specified, both SimpleFlashBeam and
#                                     SimpleFlashCosmic will be used.
#
# --dataset <dataset name>          - Specify a dataset name, singlemu or BNB etc.
#                                     All histograms will be saved in output:flash/dataset
#
# --dir <directory name>            - Specify a directory to dump .root file
#                                     (if no directory is specified, the root file will be 
#                                     stored in the current directory)  
#
##################################################################################
from __future__ import absolute_import
from __future__ import print_function
import sys,os
# Prevent root from printing garbage on initialization.
if 'TERM' in os.environ:
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
                print(line[2:], end=' ')
            else:
                print()


def main(argv):
    infile = '/pnfs/uboone/scratch/users/tjyang/output/v03_08_01/ana/prod_muminus_0.1-2.0GeV_isotropic_uboone/anahist.root'
    outfile = 'flash.root'
    flashalg = ''
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
        elif args[0] == '--flashalg' and len(args) > 1:
            flashalg = args[1]
            del args[0:2]
        elif args[0] == '--dir' and len(args) > 1:
            outdir = args[1]
            del args[0:2]     
        elif args[0] == '--dataset' and len(args) > 1:
            dataset = args[1]
            del args[0:2]
        else:
            print('Unkonwn option %s' % args[0])
            return 1

    # open the file
    myfile = TFile(infile)

    mychain = gDirectory.Get('analysistree/anatree')

    # Set flash algorithm to use. If none is defined, use SimpleFlashBeam and SimpleFlashCosmic as default
    if flashalg == '':
        flashalgs = ['simpleFlashBeam','simpleFlashCosmic']
    else:
        flashalgs = flashalg.split(",")
    print(flashalgs)

    mychain.SetBranchStatus("*",0);
    mychain.SetBranchStatus("nfls_*",1);
    mychain.SetBranchStatus("fls*",1);
    
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

    hno_flashes = {}
    fillhno_flashes = {}
    hflash_time = {}
    fillhflash_time = {}
    fillhflash_pe = {}
    hflash_pe = {}
    fillhflash_ycenter = {}
    hflash_ycenter = {}
    fillhflash_zcenter = {}
    hflash_zcenter = {}

    vno_flashes = {}
    vflash_time = {}
    vflash_pe = {}
    vflash_ycenter = {}
    vflash_zcenter = {}

    for f in flashalgs:
        hno_flashes[f] = TH1F('hno_flashes'+dataset+f,"%s, %s;Number of flashes;Number of events"%(dataset,f),100,0,200)
        fillhno_flashes[f] = hno_flashes[f].Fill
        hflash_time[f] = TH1F('hflash_time'+dataset+f,"%s, %s;Flash time (#mus);Number of flashes"%(dataset,f),100,-2000,5500)
        fillhflash_time[f] = hflash_time[f].Fill
        hflash_pe[f] = TH1F('hflash_pe'+dataset+f,"%s, %s;Flash PE;Number of flashes"%(dataset,f),100,0,10000)
        fillhflash_pe[f] = hflash_pe[f].Fill
        hflash_ycenter[f] = TH1F('hflash_ycenter'+dataset+f,"%s, %s;Flash YCenter;Number of flashes"%(dataset,f),100,-80,130)
        fillhflash_ycenter[f] = hflash_ycenter[f].Fill
        hflash_zcenter[f] = TH1F('hflash_zcenter'+dataset+f,"%s, %s;Flash ZCenter;Number of flashes"%(dataset,f),100,0,1500)
        fillhflash_zcenter[f] = hflash_zcenter[f].Fill
        vno_flashes[f] = array("i",[0])
        mychain.SetBranchAddress("nfls_"+f,vno_flashes[f])
        vflash_time[f] = array("f",[0]*1000)
        mychain.SetBranchAddress("flsTime_"+f,vflash_time[f])
        vflash_pe[f] = array("f",[0]*1000)
        mychain.SetBranchAddress("flsPe_"+f,vflash_pe[f])
        vflash_ycenter[f] = array("f",[0]*1000)
        mychain.SetBranchAddress("flsYcenter_"+f,vflash_ycenter[f])
        vflash_zcenter[f] = array("f",[0]*1000)
        mychain.SetBranchAddress("flsZcenter_"+f,vflash_zcenter[f])

    entries = mychain.GetEntriesFast()
    #entries = 100

    for jentry in range( entries ):

        if jentry%1000==0:
            print(jentry,"/",entries)
    
        # get the next tree in the chain and verify
        ientry = mychain.LoadTree( jentry )
        if ientry < 0:
            break
    
        # copy next entry into memory and verify
        nb = mychain.GetEntry( jentry )
        if nb <= 0:
            continue

        for f in flashalgs:
            nflashes = vno_flashes[f][0]
            fillhno_flashes[f](nflashes)
            if nflashes > 1000:
                nflashes = 1000
            for i in range(nflashes):
                fillhflash_time[f](vflash_time[f][i])
                fillhflash_pe[f](vflash_pe[f][i])
                fillhflash_ycenter[f](vflash_ycenter[f][i])
                fillhflash_zcenter[f](vflash_zcenter[f][i])

    for f in flashalgs:
        del fillhno_flashes[f]
        del fillhflash_time[f]
        del fillhflash_pe[f]
        del fillhflash_ycenter[f]
        del fillhflash_zcenter[f]

    hfile.Write()
    
    currdir = os.getcwd()
    if outdir != currdir:
        os.chdir(currdir)

if __name__ == '__main__':
    rc = main(sys.argv)
    sys.exit(rc)
