#! /usr/bin/env python
###############################################################################
#
# Name: pid.py
# 
# Purpose: Make and save pid validation histograms to a root file. Within 
#          the root file, for each tracker, separate directories are created
#          and plots are stored in their respective directories.
#
# Authors: Sowjanya Gollapinni
#
# Usage:
#
# pid.py <options>
#
# Options:
#
# --input <inputfile>       - Input AnalysisTree root file.
#
# --output <outputfile>     - Output root file that contain histograms.
#                             by default, output root file name is "pid.root" 
#
# --tracker <tracker name>  - Optional. Can be separated by commas. 
#                             If not specified, all trackers will be used.
#
# --dataset <dataset name>  - Specify a dataset name, singlemu or BNB etc.
#                             All histograms will be saved in output:
#                             tracking/dataset/<trackername>
#                             (for each tracker separate directories are created)
#
# --dir <directory name>    - Specify a directory to dump .root files
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
        if line[2:16] == 'pid.py':
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
    outfile = 'pid.root'
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
    
    dntracks = {}
    
    mychain.SetBranchStatus("*",0)
    mychain.SetBranchStatus("geant_list_size_in_tpcAV",1)
    mychain.SetBranchStatus("geant_list_size",1)
    mychain.SetBranchStatus("inTPCActive",1)
    mychain.SetBranchStatus("Eng",1)
    mychain.SetBranchStatus("StartPoint*",1)
    mychain.SetBranchStatus("EndPoint*",1)
    mychain.SetBranchStatus("pdg",1)
    mychain.SetBranchStatus("Mass",1)
    mychain.SetBranchStatus("processname",1)
      
    pida = {}
    fillpida = {}
    pdgchi2 = {}
    fillpdgchi2 = {}
    dtrkpidpida = {}
    dtrkpidpdg = {}
            
    for t in trackers:
        pida[t] = TH1F("pida_%s_%s"%(dataset,t),"%s, %s, using plane with most hits; PIDA (MeV/cm^{1.42})"%(dataset,t),100,0,50);
        fillpida[t] = pida[t].Fill
        pdgchi2[t] = TH1F("pdgchi2_%s_%s"%(dataset,t),"%s, %s; PDG from PDGChi2 method"%(dataset,t),100,0,500);
        fillpdgchi2[t] = pdgchi2[t].Fill
        mychain.SetBranchStatus("ntracks_"+t,1)
        mychain.SetBranchStatus("trkendx_"+t,1)
        mychain.SetBranchStatus("trkendy_"+t,1)
        mychain.SetBranchStatus("trkendz_"+t,1)
        mychain.SetBranchStatus("trkstartx_"+t,1)
        mychain.SetBranchStatus("trkstarty_"+t,1)
        mychain.SetBranchStatus("trkstartz_"+t,1)
        mychain.SetBranchStatus("trkpidbestplane_"+t,1) 
        mychain.SetBranchStatus("trkpidpida_"+t,1)
        mychain.SetBranchStatus("trkpidpdg_"+t,1)
        dntracks[t] = array("h",[0])
        mychain.SetBranchAddress("ntracks_"+t,dntracks[t])
        dtrkpidpida[t] = array("f",[0.0]*1000*3)
        mychain.SetBranchAddress("trkpidpida_"+t,dtrkpidpida[t])        

    minKE = 0.05
    
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

           
        for t in trackers:          
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
                trkpidbestplane = mychain.GetLeaf("trkpidbestplane_"+t).GetValue(i)
                trkpidpdg =     mychain.GetLeaf("trkpidpdg_"+t).GetValue(i)
                if ( Contained(trkstartx,trkstarty,trkstartz) and Contained(trkendx,trkendy,trkendz) ):
                   for j in range(mychain.geant_list_size_in_tpcAV):
                        apdg = abs(mychain.pdg[j])
                        mcstartx = mychain.StartPointx_tpcAV[j]
                        mcstarty = mychain.StartPointy_tpcAV[j]
                        mcstartz = mychain.StartPointz_tpcAV[j]
                        mcendx = mychain.EndPointx_tpcAV[j]
                        mcendy = mychain.EndPointy_tpcAV[j]
                        mcendz = mychain.EndPointz_tpcAV[j]
                        mass = mychain.Mass[j]
                        e = mychain.Eng[j]      
                        if ( (mychain.inTPCActive[j] == 1) and ( (apdg == 13  and e>=0.001*mass+minKE) or (apdg == 211 and e>=0.001*mass+minKE) 
                        or (apdg == 321 and e>=0.001*mass+minKE) or (apdg == 2212 and e>=0.001*mass+minKE) ) ):
                           if ( Contained(mcstartx,mcstarty,mcstartz) and Contained(mcendx,mcendy,mcendz) ):
                                # do start point matching
                                pmatch1 = math.sqrt(pow(mcstartx-trkstartx,2)+pow(mcstarty-trkstarty,2)+pow(mcstartz-trkstartz,2))
                                pmatch2 = math.sqrt(pow(mcstartx-trkendx,2)+pow(mcstarty-trkendy,2)+pow(mcstartz-trkendz,2))
                                # do end point matching
                                pmatch3 = math.sqrt(pow(mcendx-trkstartx,2)+pow(mcendy-trkstarty,2)+pow(mcendz-trkstartz,2))
                                pmatch4 = math.sqrt(pow(mcendx-trkendx,2)+pow(mcendy-trkendy,2)+pow(mcendz-trkendz,2))
                                minstart = min(pmatch1, pmatch2)
                                minend   = min(pmatch3, pmatch4)
                                if ( (minstart<10) and (minend<10)):
                                      trkpidpida=dtrkpidpida[t][i*3+int(trkpidbestplane)]
                                      fillpida[t](trkpidpida);
                                      fillpdgchi2[t](trkpidpdg);
                                        
        
    if outdir == '':
         outdir = os.getcwd()

    if not os.path.exists(outdir):
        os.makedirs(outdir)
    os.chdir(outdir)     
                
    hfile = gROOT.FindObject(outfile)
    if hfile:
        hfile.Close()
    hfile = TFile(outfile, 'RECREATE')
    
    dir1 = hfile.mkdir('pid')
    dir1.cd()
    
    if dataset!='':
        dir2 = dir1.mkdir(dataset)
        dir2.cd()       
        
    # Fill the PID histograms   
    for t in trackers:          
            direc = dir2.mkdir(str(t))
            direc.cd()          
            pida[t].Write()
            pdgchi2[t].Write()   
          
    currdir = os.getcwd()
    if outdir != currdir:
        os.chdir(currdir)               


if __name__ == '__main__':
    rc = main(sys.argv)
    sys.exit(rc)
