#! /usr/bin/env python
###############################################################################
#
# Name: calorimetry.py
# 
# Purpose: Make and save hit validation histograms to a root file.
#
# Authors: Tingjun Yang
#
# Usage:
#
# hit.py <options>
#
# Options:
#
# --input <inputfile>       - Input AnalysisTree root file.
#
# --output <outputfile>     - Output root file that contain histograms.
#
# --dataset <dataset name>  - Specify a dataset name, singlemu or BNB etc.
#                             All histograms will be saved in output:hit/dataset
# 
# --dir <directory name>    - Specify a directory to dump .root files
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
        if line[2:8] == 'hit.py':
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
    outfile = 'hit.root'
    dataset = 'histdir'
    outdir  = ''
    args = argv[1:]
    while len(args) > 0:
        if args[0] == '-h' or args[0] == '--help':
            help()
            return 0
        elif args[0] == '--input' and len(args) > 1:
            infile = args[1]
            del args[0:2]
	elif args[0] == '--dir' and len(args) > 1:
	    outdir = args[1]
	    del args[0:2]    
        elif args[0] == '--output' and len(args) > 1:
            outfile = args[1]
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
    mychain.SetBranchStatus("no_hits",1);
    mychain.SetBranchStatus("hit_*",1);
    
    if outdir == '':
    	 outdir = os.getcwd()
    
    if not os.path.exists(outdir):
    	os.makedirs(outdir)
    os.chdir(outdir)
    
    hfile = gROOT.FindObject(outfile)
    if hfile:
        hfile.Close()
    hfile = TFile(outfile, 'RECREATE')
    
    dir1 = hfile.mkdir('hit')
    dir1.cd()

    if dataset!='':
        dir2 = dir1.mkdir(dataset)
        dir2.cd()

    hno_hits = TH1F('hno_hits'+dataset,dataset+';Number of hits;Number of events',100,0,5000)
    fillhno_hits = hno_hits.Fill
    hhit_plane = TH1F('hhit_plane'+dataset,dataset+';Hit plane number;Number of hits',6,0,6)
    fillhhit_plane = hhit_plane.Fill
    hhit_wire = TH1F('hhit_wire'+dataset,dataset+';Hit wire number;Number of hits',100,0,6000)
    fillhhit_wire = hhit_wire.Fill
    hhit_channel = TH1F('hhit_channel'+dataset,dataset+';Hit channel number;Number of hits',100,0,12000)
    fillhhit_channel = hhit_channel.Fill
    hhit_peakT = TH1F('hhit_peakT'+dataset,dataset+';Hit peak time (tick);Number of hits',100,3000,10000)
    fillhhit_peakT = hhit_peakT.Fill
    hhit_charge = {}
    fillhhit_charge = {}
    hhit_ph = {}
    fillhhit_ph = {}
    hhit_charge_nelec = {}
    fillhhit_charge_nelec = {}
    hhit_ph_nelec = {}
    fillhhit_ph_nelec = {}
    hchargeperelec = {}
    fillhchargeperelec = {}
    hphperelec = {}
    fillhphperelec = {}
    for i in range(3):
        hhit_charge[str(i)] = TH1F('hhit_charge'+str(i)+dataset,dataset+', Plane = %d;Hit area (ADC);Number of hits'%i,100,0,1500)
        fillhhit_charge[str(i)] = hhit_charge[str(i)].Fill
        hhit_ph[str(i)] = TH1F('hhit_ph'+str(i)+dataset,dataset+', Plane = %d;Hit pulseheight (ADC);Number of hits'%i,100,0,200)
        fillhhit_ph[str(i)] = hhit_ph[str(i)].Fill
        hhit_charge_nelec[str(i)] = TH2F('hhit_charge_nelec'+str(i)+dataset,dataset+', Plane = %d; Number of electrons;Hit area (ADC)'%i,1000,0,1e5,1000,0,1000)
        fillhhit_charge_nelec[str(i)] = hhit_charge_nelec[str(i)].Fill
        hhit_ph_nelec[str(i)] = TH2F('hhit_ph_nelec'+str(i)+dataset,dataset+', Plane = %d; Number of electrons;Hit pulseheight (ADC)'%i,1000,0,1e5,1000,0,100)
        fillhhit_ph_nelec[str(i)] = hhit_ph_nelec[str(i)].Fill
        hchargeperelec[str(i)] = TH1F('hchargeperelec'+str(i)+dataset,dataset+', Plane = %d;ADC (area) per electron'%i,1000,0,0.02)
        fillhchargeperelec[str(i)] = hchargeperelec[str(i)].Fill
        hphperelec[str(i)] = TH1F('hphperelec'+str(i)+dataset,dataset+', Plane = %d;ADC (pulse height) per electron'%i,1000,0,0.003)
        fillhphperelec[str(i)] = hphperelec[str(i)].Fill


    vno_hits = array("i",[0])
    mychain.SetBranchAddress("no_hits",vno_hits)
    vhit_plane = array("h",[0]*25000)
    mychain.SetBranchAddress("hit_plane",vhit_plane)
    vhit_wire = array("h",[0]*25000)
    mychain.SetBranchAddress("hit_wire",vhit_wire)
    vhit_channel = array("h",[0]*25000)
    mychain.SetBranchAddress("hit_channel",vhit_channel)
    vhit_peakT = array("f",[0]*25000)
    mychain.SetBranchAddress("hit_peakT",vhit_peakT)
    vhit_charge = array("f",[0]*25000)
    mychain.SetBranchAddress("hit_charge",vhit_charge)
    vhit_ph = array("f",[0]*25000)
    mychain.SetBranchAddress("hit_ph",vhit_ph)
    vhit_nelec = array("f",[0]*25000)
    mychain.SetBranchAddress("hit_nelec",vhit_nelec)

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
        
        nhits = vno_hits[0]
        fillhno_hits(nhits)
        if nhits > 25000:
            nhits = 25000
        for i in range(nhits):
            fillhhit_plane(vhit_plane[i])
            fillhhit_wire(vhit_wire[i])
            fillhhit_channel(vhit_channel[i])
            fillhhit_peakT(vhit_peakT[i])
            if (vhit_plane[i]>=0 and vhit_plane[i]<3):
                fillhhit_ph_nelec[str(vhit_plane[i])](vhit_nelec[i],vhit_ph[i])
                fillhhit_charge_nelec[str(vhit_plane[i])](vhit_nelec[i],vhit_charge[i])
                fillhhit_charge[str(vhit_plane[i])](vhit_charge[i])
                fillhhit_ph[str(vhit_plane[i])](vhit_ph[i])
                
                if vhit_nelec[i]>0:
                    fillhphperelec[str(vhit_plane[i])](vhit_ph[i]/vhit_nelec[i])
                    fillhchargeperelec[str(vhit_plane[i])](vhit_charge[i]/vhit_nelec[i])
    del fillhno_hits
    del fillhhit_plane
    del fillhhit_wire
    del fillhhit_channel
    del fillhhit_peakT
    for i in range(3):
        del fillhhit_charge[str(i)]
        del fillhhit_ph[str(i)]
        del fillhhit_ph_nelec[str(i)]
        del fillhhit_charge_nelec[str(i)]
        del fillhphperelec[str(i)]
        del fillhchargeperelec[str(i)]
    hfile.Write()

    currdir = os.getcwd()
    if outdir != currdir:
    	os.chdir(currdir)

if __name__ == '__main__':
    rc = main(sys.argv)
    sys.exit(rc)
    
    
