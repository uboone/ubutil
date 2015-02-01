
from ROOT import TFile, TCanvas, TH1F, TH2F, TProfile
from ROOT import gDirectory, gROOT
from utilities import *
#import math
#import re

#def disdiff(x0,x1,y0,y1,z0,z1):
#    return math.sqrt(pow(x0-x1,2)+pow(y0-y1,2)+pow(z0-z1,2))
#
#def contained(x,y,z):
#    if x > 10 and x < 240 and y > -110 and y < 110 and z > 10 and z < 1030:
#        return True
#    else:
#        return False

# Create histograms
#dedxrr = TH2F("dedxrr","dE/dx vs Residual Range",1000,0,1000,1000,0,20);

#dedxrrFill = dedxrr.Fill

# open the file
myfile = TFile('/pnfs/uboone/scratch/users/tjyang/output/v03_06_00/ana/prod_muminus_0.1-2.0GeV_isotropic_modbox_uboone/anahist.root')
#myfile = TFile('anahist.root')

mychain = gDirectory.Get('analysistree/anatree')

trackers = GetTrackers(mychain)
trackers = ['trackkalmanhit']
print trackers

mychain.SetBranchStatus("*",0);
mychain.SetBranchStatus("StartPoint*",1);
mychain.SetBranchStatus("EndPoint*",1);
#mychain.SetBranchStatus("event",1);

hfile = gROOT.FindObject('calorimetry.root')
if hfile:
    hfile.Close()
hfile = TFile('calorimetry.root', 'RECREATE')

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

    #print mychain.ntracks_costrkcc
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
                        if ntrkhits > 1000:
                            ntrkhits = 1000
                        for k in range(ntrkhits):
                            trkdedx = mychain.GetLeaf("trkdedx_"+t).GetValue(i*3*1000+j*1000+k)
                            trkresrg = mychain.GetLeaf("trkresrg_"+t).GetValue(i*3*1000+j*1000+k)
                            if (trkdedx>0):
                                filldedxrr[j][t](trkresrg,trkdedx)
                                fillpdedxrr[j][t](trkresrg,trkdedx)
    

canvas = {}
muondEdxR = GetMuondEdxR()
for t in trackers:
    canvas[t] = TCanvas("can_"+t,"can_"+t,1000,800)
    canvas[t].Divide(2,2)
    for i in range(3):
        canvas[t].cd(i+1)
        dedxrr[i][t].Draw("colz")
        pdedxrr[i][t].SetMarkerStyle(20)
        pdedxrr[i][t].SetMarkerSize(0.3)
        pdedxrr[i][t].Draw("same")
        muondEdxR.SetMarkerStyle(20)
        muondEdxR.SetMarkerSize(0.3)
        muondEdxR.SetMarkerColor(800)
        muondEdxR.SetLineColor(800)
        muondEdxR.SetLineWidth(2)
        muondEdxR.Draw("pc")

for t in trackers:
    for ipl in range(3):
        del filldedxrr[ipl][t]
        del fillpdedxrr[ipl][t]

hfile.Write()
