#! /usr/bin/env python
###############################################################################
#
# Name: calorimetry.py
# 
# Purpose: Make and save calorimetry validation histograms to a root file.
#
# Authors: Tingjun Yang
#
# Usage:
#
# calorimetry.py <options>
#
# Options:
#
# --input <inputfile>       - Input AnalysisTree root file.
#
# --output <outputfile>     - Output root file that contain histograms.
#
# --tracker <tracker name>  - Optional. Can be separated by commas. 
#                             If not specified, all trackers will be used.
#
# --dataset <dataset name>  - Specify a dataset name, singlemu or BNB etc.
#                             All histograms will be saved in output:calorimetry/dataset
#
# --dir <directory name>    - Specify a directory to dump .root file
#                             (if no directory is specified, the root file will be 
#                             stored in the current directory)  
#
###############################################################################
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
        if line[2:16] == 'calorimetry.py':
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
    outfile = 'calorimetry.root'
    tracker = ''
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
        elif args[0] == '--tracker' and len(args) > 1:
            tracker = args[1]
            del args[0:2]
        elif args[0] == '--dir' and len(args) > 1:
            outdir = args[1]
            del args[0:2]     
        elif args[0] == '--dataset' and len(args) > 1:
            dataset = args[1]
            del args[0:2]
        else:
            print('Unkonw option %s' % args[0])
            return 1

    # open the file
    myfile = TFile(infile)
    #myfile = TFile('anahist.root')

    mychain = gDirectory.Get('analysistree/anatree')

    if tracker == '':
        trackers = GetTrackers(mychain)
    else:
        trackers = tracker.split(",")
    print(trackers)
    
    mychain.SetBranchStatus("*",0)
    mychain.SetBranchStatus("StartPoint*",1)
    mychain.SetBranchStatus("EndPoint*",1)
    mychain.SetBranchStatus("pdg",1)
    mychain.SetBranchStatus("geant_list_size",1)
    mychain.SetBranchStatus("MergedId",1)
    mychain.SetBranchStatus("NumberDaughters",1)
    mychain.SetBranchStatus("processname",1)
    #mychain.SetBranchStatus("event",1);

    if outdir == '':
         outdir = os.getcwd()
    
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    os.chdir(outdir)

    hfile = gROOT.FindObject(outfile)
    if hfile:
        hfile.Close()
    hfile = TFile(outfile, 'RECREATE')
    
    dir1 = hfile.mkdir('calorimetry')
    dir1.cd()
    
    if dataset!='':
        dir2 = dir1.mkdir(dataset)
        dir2.cd()

    dedxrr = {}
    filldedxrr = {}
    pdedxrr = {}
    fillpdedxrr = {}
    dedx = {}
    filldedx = {}
    kelen = {}
    fillkelen = {}
    ke2d = {}
    fillke2d = {}

    dntracks = {}
    dntrkhits = {}
    dtrkdedx = {}
    dtrkresrg = {}

    for t in trackers:
        for ipl in range(3):
            if 'pro' in dataset:
                dedxrr[t+str(ipl)] = TH2F("dedxrr%d%s%s"%(ipl,dataset,t),"%s, %s, Plane = %d;Residual Range (cm);dE/dx (MeV/cm)"%(dataset,t,ipl),100,0,300,1000,0,20)
            else:
                dedxrr[t+str(ipl)] = TH2F("dedxrr%d%s%s"%(ipl,dataset,t),"%s, %s, Plane = %d;Residual Range (cm);dE/dx (MeV/cm)"%(dataset,t,ipl),1000,0,1000,1000,0,20)
            filldedxrr[t+str(ipl)] = dedxrr[t+str(ipl)].Fill
            pdedxrr[t+str(ipl)] = TProfile("pdedxrr%d%s%s"%(ipl,dataset,t),"%s, %s, Plane = %d;Residual Range (cm);dE/dx (MeV/cm)"%(dataset,t,ipl),1000,0,1000)
            fillpdedxrr[t+str(ipl)] = pdedxrr[t+str(ipl)].Fill
            dedx[t+str(ipl)] = TH1F("dedx%d%s%s"%(ipl,dataset,t),"%s, %s, Plane = %d;dE/dx (MeV/cm); Nhits"%(dataset,t,ipl),100,0,10)
            filldedx[t+str(ipl)] = dedx[t+str(ipl)].Fill
            kelen[t+str(ipl)] = TH2F("kelen%d%s%s"%(ipl,dataset,t),"%s, %s, Plane = %d;Track Length (cm); KE (MeV)"%(dataset,t,ipl),100,0,300,100,0,500)
            fillkelen[t+str(ipl)] = kelen[t+str(ipl)].Fill
        mychain.SetBranchStatus("ntracks_"+t,1)
        mychain.SetBranchStatus("trkstartx_"+t,1)
        mychain.SetBranchStatus("trkstarty_"+t,1)
        mychain.SetBranchStatus("trkstartz_"+t,1)
        mychain.SetBranchStatus("trkendx_"+t,1)
        mychain.SetBranchStatus("trkendy_"+t,1)
        mychain.SetBranchStatus("trkendz_"+t,1)
        mychain.SetBranchStatus("ntrkhits_"+t,1)
        mychain.SetBranchStatus("trkdedx_"+t,1)
        mychain.SetBranchStatus("trkresrg_"+t,1)
        mychain.SetBranchStatus("trkke_"+t,1)
        mychain.SetBranchStatus("trklen_"+t,1)
        dntracks[t] = array("h",[0])
        mychain.SetBranchAddress("ntracks_"+t,dntracks[t])
        dntrkhits[t] = array("h",[0]*1000*3)
        mychain.SetBranchAddress("ntrkhits_"+t,dntrkhits[t])
        dtrkdedx[t] = array("f",[0.0]*1000*3*2000)
        mychain.SetBranchAddress("trkdedx_"+t,dtrkdedx[t])
        dtrkresrg[t] = array("f",[0.0]*1000*3*2000)
        mychain.SetBranchAddress("trkresrg_"+t,dtrkresrg[t])

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
#        if mychain.pdg[0]==2212 and mychain.NumberDaughters[0]!=0:
#            continue
        #print mychain.pdg[0],mychain.NumberDaughters[0]
        StartPointx = mychain.StartPointx[0]
        StartPointy = mychain.StartPointy[0]
        StartPointz = mychain.StartPointz[0]
        EndPointx = mychain.EndPointx[0]
        EndPointy = mychain.EndPointy[0]
        EndPointz = mychain.EndPointz[0]
        #numDaughters = mychain.NumberDaughters[0]
        if mychain.pdg[0]==2212:
            numDaughters = 0
            #print mychain.geant_list_size
            for j in range(mychain.geant_list_size):
                if j == 0:
                    continue
                if ('conv' not in mychain.processname[j] and
                    'LowEnConversion' not in mychain.processname[j] and
                    'Pair' not in mychain.processname[j] and
                    'compt' not in mychain.processname[j] and
                    'Compt' not in mychain.processname[j] and
                    'Brem' not in mychain.processname[j] and
                    'phot' not in mychain.processname[j] and
                    'Photo' not in mychain.processname[j] and
                    'Ion' not in mychain.processname[j] and
                    'annihil' not in mychain.processname[j]):
                    numDaughters += 1
            if numDaughters > 0:
                continue
            #print j, mychain.MergedId[j]
#            if mychain.MergedId[j] == mychain.MergedId[0]:
#                #print j, mychain.MergedId[j]
#                EndPointx = mychain.EndPointx[j]
#                EndPointy = mychain.EndPointy[j]
#                EndPointz = mychain.EndPointz[j]
#                numDaughters = mychain.NumberDaughters[j]
#        if numDaughters!=0:
#            continue
        for t in trackers:
            #ntracks = int(mychain.GetLeaf("ntracks_"+t).GetValue()+0.1)
            ntracks = dntracks[t][0]
            if ntracks > 1000:
                ntracks = 1000
            for i in range(ntracks):
                trkstartx = mychain.GetLeaf("trkstartx_"+t).GetValue(i)
                trkstarty = mychain.GetLeaf("trkstarty_"+t).GetValue(i)
                trkstartz = mychain.GetLeaf("trkstartz_"+t).GetValue(i)
                trkendx = mychain.GetLeaf("trkendx_"+t).GetValue(i)
                trkendy = mychain.GetLeaf("trkendy_"+t).GetValue(i)
                trkendz = mychain.GetLeaf("trkendz_"+t).GetValue(i)
                trklen  = mychain.GetLeaf("trklen_"+t).GetValue(i)

                if (PointMatch(trkstartx, trkstarty, trkstartz,
                               StartPointx, StartPointy, StartPointz)
                    and PointMatch(trkendx, trkendy, trkendz,
                                   EndPointx, EndPointy, EndPointz)
                    or PointMatch(trkstartx, trkstarty, trkstartz,
                                  EndPointx, EndPointy, EndPointz)
                    and PointMatch(trkendx, trkendy, trkendz,
                                   StartPointx, StartPointy, StartPointz)):
                    if (Contained(trkstartx, trkstarty, trkstartz)
                        and Contained(trkendx, trkendy, trkendz)):
                        for j in range(3):
                            #ntrkhits = int(mychain.GetLeaf("ntrkhits_"+t).GetValue(i*3+j)+0.1)
                            trkke = mychain.GetLeaf("trkke_"+t).GetValue(i*3+j)
                            fillkelen[t+str(j)](trklen,trkke)
                            ntrkhits = dntrkhits[t][i*3+j]
                            if ntrkhits > 2000:
                                ntrkhits = 2000
                            for k in range(ntrkhits):
                                #trkdedx = mychain.GetLeaf("trkdedx_"+t).GetValue(i*3*2000+j*2000+k)
                                #trkresrg = mychain.GetLeaf("trkresrg_"+t).GetValue(i*3*2000+j*2000+k)
                                trkdedx = dtrkdedx[t][i*3*2000+j*2000+k]
                                trkresrg = dtrkresrg[t][i*3*2000+j*2000+k]
                                if trkdedx>0 and trkdedx<20:
                                    filldedxrr[t+str(j)](trkresrg,trkdedx)
                                    fillpdedxrr[t+str(j)](trkresrg,trkdedx)
                                    if trkresrg>90 and trkresrg<110:
                                        filldedx[t+str(j)](trkdedx)
    
    for t in trackers:
        for ipl in range(3):
            del filldedxrr[t+str(ipl)]
            del fillpdedxrr[t+str(ipl)]
            del filldedx[t+str(ipl)]
            del fillkelen[t+str(ipl)]

    hfile.Write()
    
    currdir = os.getcwd()
    if outdir != currdir:
        os.chdir(currdir)

if __name__ == '__main__':
    rc = main(sys.argv)
    sys.exit(rc)
