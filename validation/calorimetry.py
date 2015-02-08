#!/usr/bin/env python
import sys
from ROOT import TFile, TCanvas, TH1F, TH2F, TProfile
from ROOT import gDirectory, gROOT
from validation_utilities import *

def main(argv):
    infile = '/pnfs/uboone/scratch/users/tjyang/output/v03_08_01/ana/prod_muminus_0.1-2.0GeV_isotropic_uboone/anahist.root'
    outfile = 'calorimetry.root'
    tracker = ''
    histdir = 'histdir'
    args = argv[1:]
    while len(args) > 0:
        if args[0] == '--input' and len(args) > 1:
            infile = args[1]
            del args[0:2]
        elif args[0] == '--output' and len(args) > 1:
            outfile = args[1]
            del args[0:2]
        elif args[0] == '--tracker' and len(args) > 1:
            tracker = args[1]
            del args[0:2]
        elif args[0] == '--histdir' and len(args) > 1:
            histdir = args[1]
            del args[0:2]
        else:
            print 'Unkonw option %s' % args[0]
            return 1

    # open the file
    myfile = TFile(infile)
    #myfile = TFile('anahist.root')

    mychain = gDirectory.Get('analysistree/anatree')

    if tracker == '':
        trackers = GetTrackers(mychain)
    else:
        trackers = tracker.split(",")
    print trackers
    
    mychain.SetBranchStatus("*",0);
    mychain.SetBranchStatus("StartPoint*",1);
    mychain.SetBranchStatus("EndPoint*",1);
    mychain.SetBranchStatus("event",1);

    hfile = gROOT.FindObject(outfile)
    if hfile:
        hfile.Close()
    hfile = TFile(outfile, 'RECREATE')
    
    dir1 = hfile.mkdir('calorimetry')
    dir1.cd()
    
    if histdir!='':
        dir2 = dir1.mkdir(histdir)
        dir2.cd()

    dedxrr = [{},{},{}]
    filldedxrr = [{},{},{}]
    pdedxrr = [{},{},{}]
    fillpdedxrr = [{},{},{}]
    for t in trackers:
        for ipl in range(3):
            dedxrr[ipl][t] = TH2F("dedxrr%d_%s"%(ipl,t),"%s, Plane = %d;Residual Range (cm);dE/dx (MeV/cm)"%(t,ipl),1000,0,1000,1000,0,20);
            filldedxrr[ipl][t] = dedxrr[ipl][t].Fill
            pdedxrr[ipl][t] = TProfile("pdedxrr%d_%s"%(ipl,t),"%s, Plane = %d;Residual Range (cm);dE/dx (MeV/cm)"%(t,ipl),1000,0,1000)
            fillpdedxrr[ipl][t] = pdedxrr[ipl][t].Fill
    #        dedxrr[ipl][t].Print()
        mychain.SetBranchStatus("*_"+t,1)

    #text_file = open("dedx.txt","w")

    entries = mychain.GetEntriesFast()

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
        
        StartPointx = mychain.StartPointx[0]
        StartPointy = mychain.StartPointy[0]
        StartPointz = mychain.StartPointz[0]
        EndPointx = mychain.EndPointx[0]
        EndPointy = mychain.EndPointy[0]
        EndPointz = mychain.EndPointz[0]
        for t in trackers:
            ntracks = int(mychain.GetLeaf("ntracks_"+t).GetValue()+0.1)
            for i in range(ntracks):
                trkstartx = mychain.GetLeaf("trkstartx_"+t).GetValue(i)
                trkstarty = mychain.GetLeaf("trkstarty_"+t).GetValue(i)
                trkstartz = mychain.GetLeaf("trkstartz_"+t).GetValue(i)
                trkendx = mychain.GetLeaf("trkendx_"+t).GetValue(i)
                trkendy = mychain.GetLeaf("trkendy_"+t).GetValue(i)
                trkendz = mychain.GetLeaf("trkendz_"+t).GetValue(i)

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
                            ntrkhits = int(mychain.GetLeaf("ntrkhits_"+t).GetValue(i*3+j)+0.1)
                            if ntrkhits > 2000:
                                ntrkhits = 2000
                            for k in range(ntrkhits):
                                trkdedx = mychain.GetLeaf("trkdedx_"+t).GetValue(i*3*2000+j*2000+k)
                                trkresrg = mychain.GetLeaf("trkresrg_"+t).GetValue(i*3*2000+j*2000+k)
                                if trkdedx>0:
                                    filldedxrr[j][t](trkresrg,trkdedx)
                                    fillpdedxrr[j][t](trkresrg,trkdedx)
    
    for t in trackers:
        for ipl in range(3):
            del filldedxrr[ipl][t]
            del fillpdedxrr[ipl][t]

    hfile.Write()

if __name__ == '__main__':
    rc = main(sys.argv)
    sys.exit(rc)
