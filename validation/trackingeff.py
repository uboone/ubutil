#! /usr/bin/env python
###############################################################################
#
# Name: trackingeff.py
# 
# Purpose: Make and save tracking validation histograms to a root file. Within 
#          the root file, for each tracker, separate directories are created
#          and plots are stored in their respective directories.
#
# Authors: Sowjanya Gollapinni
#
# Usage:
#
# trackingeff.py <options>
#
# Options:
#
# --input <inputfile>       - Input AnalysisTree root file.
#
# --output <outputfile>     - Output root file that contain histograms.
#			      by default, output root file name is "tracking.root" 
#
# --tracker <tracker name>  - Optional. Can be separated by commas. 
#                             If not specified, all trackers will be used.
#
# --dataset <dataset name>  - Specify a dataset name, singlemu or BNB etc.
#                             All histograms will be saved in output:
#			      tracking/dataset/<trackername>
#			      (for each tracker separate directories are created)
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
        if line[2:16] == 'trackingeff.py':
            doprint = 1
        elif line[0:6] == '######' and doprint:
            doprint = 0
        if doprint:
            if len(line) > 2:
                print line[2:],
            else:
                print
		
#function to evaluate efficiency of histograms
def effcalc(hnum, hden, heff):
   nbins = hnum.GetNbinsX()
   assert(nbins == hden.GetNbinsX())
   assert(nbins == heff.GetNbinsX())

   # Loop over bins, including underflow and overflow.
   for ibin in xrange(nbins+1):
     num = hnum.GetBinContent(ibin)
     den = hden.GetBinContent(ibin)
     if(den == 0.):
       heff.SetBinContent(ibin, 0.)
       heff.SetBinError(ibin, 0.)     
     else:
       eff = num / den
       if (eff <0):
       	   eff=0
       if (eff >1):
	   eff=1	
       err = math.sqrt(eff * (1.-eff) / den)
       if (eff >1):
           err = 0
       if (eff<=1):
           heff.SetBinContent(ibin, eff);
           heff.SetBinError(ibin, err);
     
   heff.SetMinimum(0.)
   heff.SetMaximum(1.05)
   heff.SetMarkerStyle(20)
    
		
		
def main(argv):
    infile = '/pnfs/uboone/scratch/users/tjyang/output/v03_08_01/ana/prod_muminus_0.1-2.0GeV_isotropic_uboone/anahist.root'
    outfile = 'tracking.root'
    tracker = ''
    dataset = 'histdir'
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
        elif args[0] == '--dataset' and len(args) > 1:
            dataset = args[1]
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
    
    dntracks = {}
    
    mychain.SetBranchStatus("*",0)
    mychain.SetBranchStatus("geant_list_size",1)    
    mychain.SetBranchStatus("geant_list_size_in_tpcAV",1)
    mychain.SetBranchStatus("inTPCActive",1)
    mychain.SetBranchStatus("Eng",1)
    mychain.SetBranchStatus("StartPoint*",1)
    mychain.SetBranchStatus("EndPoint*",1)
    mychain.SetBranchStatus("thet*",1)
    mychain.SetBranchStatus("phi",1)
    mychain.SetBranchStatus("pathlen",1)
    mychain.SetBranchStatus("pdg",1)
    mychain.SetBranchStatus("P",1)
    mychain.SetBranchStatus("Mass",1)
    mychain.SetBranchStatus("Px",1)
    mychain.SetBranchStatus("Py",1)
    mychain.SetBranchStatus("Pz",1)
    
    mclen_all = TH1F('TrueLength','',60,0,1200)
    mcpdg_all = TH1F('TruePDG','',20,0,5000)
    mctheta_all = TH1F('TrueTheta','',20,0,180)
    mcphi_all = TH1F('TruePhi','',20,-180,180)
    mcthetaxz_all = TH1F('TrueThetaXZ','',20,-180,180)
    mcthetayz_all = TH1F('TrueThetaYZ','',20,-180,180)
    mcmom_all = TH1F('TrueMom','',20,0,2.2)
   
    mclen_g = {}
    fillmclen_g = {}
    mcpdg_g = {}
    fillmcpdg_g = {}
    mctheta_g = {}
    fillmctheta_g = {}
    mcphi_g = {}
    fillmcphi_g = {}
    mcthetaxz_g = {}
    fillmcthetaxz_g = {}
    mcthetayz_g = {}
    fillmcthetayz_g = {}
    mcmom_g = {}
    fillmcmom_g = {}
    
    mclen_e	= {}
    mctheta_e	= {}
    mcphi_e	= {}
    mcmom_e	= {}
    mcthetaxz_e = {}
    mcthetayz_e = {}
    mcpdg_e	= {}
      	    
    for t in trackers:
    	mclen_g[t] = TH1F("mclen_g_%s_%s"%(dataset,t),'',60,0,1200);
	fillmclen_g[t] = mclen_g[t].Fill
    	mcpdg_g[t] = TH1F("mcpdg_g_%s_%s"%(dataset,t),'',20,0,5000);
	fillmcpdg_g[t] = mcpdg_g[t].Fill
    	mctheta_g[t] = TH1F("mctheta_g_%s_%s"%(dataset,t),'',20,0,180);
	fillmctheta_g[t] = mctheta_g[t].Fill
	mcphi_g[t] = TH1F("mcphi_g_%s_%s"%(dataset,t),'',20,-180,180);
	fillmcphi_g[t] = mcphi_g[t].Fill
    	mcthetaxz_g[t] = TH1F("mcthetaxz_g_%s_%s"%(dataset,t),'',20,-180,180);
	fillmcthetaxz_g[t] = mcthetaxz_g[t].Fill
    	mcthetayz_g[t] = TH1F("mcthetayz_g_%s_%s"%(dataset,t),'',20,-180,180);
	fillmcthetayz_g[t] = mcthetayz_g[t].Fill
     	mcmom_g[t] = TH1F("mcmom_g_%s_%s"%(dataset,t),'',20,0,2.2);
	fillmcmom_g[t] = mcmom_g[t].Fill
	# efficiency histograms
	mclen_e[t] = TH1F("mclen_e_%s_%s"%(dataset,t),"%s, %s; Track length (cm);Efficiency"%(dataset,t),60,0,1200);
    	mcpdg_e[t] = TH1F("mcpdg_e_%s_%s"%(dataset,t),"%s, %s; PDG Code;Efficiency"%(dataset,t),20,0,5000);
    	mctheta_e[t] = TH1F("mctheta_e_%s_%s"%(dataset,t),"%s, %s; #theta (degrees);Efficiency"%(dataset,t),20,0,180)
	mcphi_e[t] = TH1F("mcphi_e_%s_%s"%(dataset,t),"%s, %s; #phi (degrees);Efficiency"%(dataset,t),20,-180,180)
    	mcthetaxz_e[t] = TH1F("mcthetaxz_e_%s_%s"%(dataset,t),"%s, %s; #theta_{xz} (degrees);Efficiency"%(dataset,t),20,-180,180)
    	mcthetayz_e[t] = TH1F("mcthetayz_e_%s_%s"%(dataset,t),"%s, %s; #theta_{yz} (degrees);Efficiency"%(dataset,t),20,-180,180)
     	mcmom_e[t] = TH1F("mcmom_e_%s_%s"%(dataset,t),"%s, %s; momentum (GeV);Efficiency"%(dataset,t),20,0,2.2)
        mychain.SetBranchStatus("ntracks_"+t,1)
        mychain.SetBranchStatus("trkstartdcosx_"+t,1)
        mychain.SetBranchStatus("trkstartdcosy_"+t,1)
        mychain.SetBranchStatus("trkstartdcosz_"+t,1)
        mychain.SetBranchStatus("trkendx_"+t,1)
        mychain.SetBranchStatus("trkendy_"+t,1)
        mychain.SetBranchStatus("trkendz_"+t,1)
        mychain.SetBranchStatus("trkstartx_"+t,1)
        mychain.SetBranchStatus("trkstarty_"+t,1)
        mychain.SetBranchStatus("trkstartz_"+t,1)
	mychain.SetBranchStatus("trklen_"+t,1)
	dntracks[t] = array("h",[0])
        mychain.SetBranchAddress("ntracks_"+t,dntracks[t])	

    minKE = 0.05
    
    #entries = mychain.GetEntriesFast()
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
	    
	for i in xrange( mychain.geant_list_size_in_tpcAV ):
		apdg = abs(mychain.pdg[i])
		if (mychain.inTPCActive[i] == 1):
			if ( (apdg == 13  and mychain.Eng[i]>=0.001*mychain.Mass[i]+minKE) or (apdg == 211 and mychain.Eng[i]>=0.001*mychain.Mass[i]+minKE) or (apdg == 321 and
	    	        mychain.Eng[i]>=0.001*mychain.Mass[i]+minKE) or (apdg == 2212 and mychain.Eng[i]>=0.001*mychain.Mass[i]+minKE) ):
				mclen_all.Fill(mychain.pathlen[i])
				mcpdg_all.Fill(mychain.pdg[i])
				mctheta_all.Fill(mychain.theta[i]*180/3.142)
				mcphi_all.Fill(mychain.phi[i]*180/3.142)
				mcthetaxz_all.Fill(mychain.theta_xz[i]*180/3.142)
				mcthetayz_all.Fill(mychain.theta_yz[i]*180/3.142)
				mcmom_all.Fill(mychain.P[i])				    

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
		trkstartdcosx = mychain.GetLeaf("trkstartdcosx_"+t).GetValue(i)
		trkstartdcosy = mychain.GetLeaf("trkstartdcosy_"+t).GetValue(i)
		trkstartdcosz = mychain.GetLeaf("trkstartdcosz_"+t).GetValue(i)
		trklen = mychain.GetLeaf("trklen_"+t).GetValue(i)
		for j in xrange(mychain.geant_list_size_in_tpcAV):
			apdg = abs(mychain.pdg[j])
			mcstartx = mychain.StartPointx_tpcAV[j]
			mcstarty = mychain.StartPointy_tpcAV[j]
			mcstartz = mychain.StartPointz_tpcAV[j]
			mcendx = mychain.EndPointx_tpcAV[j]
			mcendy = mychain.EndPointy_tpcAV[j]
			mcendz = mychain.EndPointz_tpcAV[j]
			theta = mychain.theta[j]*180/3.142
			phi = mychain.phi[j]*180/3.142	
			px = mychain.Px[j]		
			py = mychain.Py[j]		
			pz = mychain.Pz[j]	
			p = mychain.P[j]
			if (mychain.inTPCActive[j] == 1):
			 	if ( (apdg == 13  and mychain.Eng[j]>=0.001*mychain.Mass[j]+minKE) or (apdg == 211 and mychain.Eng[j]>=0.001*mychain.Mass[j]+minKE) or (apdg == 321 and
	    	        	mychain.Eng[j]>=0.001*mychain.Mass[j]+minKE) or (apdg == 2212 and mychain.Eng[j]>=0.001*mychain.Mass[j]+minKE) ):
					num = ((trkstartdcosx*px)+(trkstartdcosy*py)+(trkstartdcosz*pz))
					angle=num/p
					if (angle>1): 
						angle=1	
					if (angle<-1):
						angle=-1					
				        ang = math.degrees(math.acos(angle))
					if ( (abs(ang)<=10) or (abs(180-(ang))<=10)):
						# do start point matching
						pmatch1 = math.sqrt(pow(mcstartx-trkstartx,2)+pow(mcstarty-trkstarty,2)+pow(mcstartz-trkstartz,2))
						pmatch2 = math.sqrt(pow(mcstartx-trkendx,2)+pow(mcstarty-trkendy,2)+pow(mcstartz-trkendz,2))
						minstart = min(pmatch1, pmatch2)
						if (minstart<=5):
							if (trklen >= 0.5*mychain.pathlen[j]):
								fillmclen_g[t](mychain.pathlen[j])
								fillmcpdg_g[t](mychain.pdg[j])
								fillmctheta_g[t](mychain.theta[j]*180/3.142)
								fillmcphi_g[t](mychain.phi[j]*180/3.142)
								fillmcthetaxz_g[t](mychain.theta_xz[j]*180/3.142)
								fillmcthetayz_g[t](mychain.theta_yz[j]*180/3.142)
								fillmcmom_g[t](p)			
					
  	
    hfile = gROOT.FindObject(outfile)
    if hfile:
        hfile.Close()
    hfile = TFile(outfile, 'RECREATE')
    
    dir1 = hfile.mkdir('tracking')
    dir1.cd()
    
    if dataset!='':
        dir2 = dir1.mkdir(dataset)
        dir2.cd()	
	
    # Fill the efficiency histograms	
    for t in trackers:		
	    direc = dir2.mkdir(str(t))
            direc.cd()		
            effcalc(mclen_g[t],     mclen_all,     mclen_e[t])
	    effcalc(mcpdg_g[t],     mcpdg_all,     mcpdg_e[t])
	    effcalc(mctheta_g[t],   mctheta_all,   mctheta_e[t])
	    effcalc(mcphi_g[t],     mcphi_all,     mcphi_e[t])
	    effcalc(mcthetaxz_g[t], mcthetaxz_all, mcthetaxz_e[t])
	    effcalc(mcthetayz_g[t], mcthetayz_all, mcthetayz_e[t])
	    effcalc(mcmom_g[t],     mcmom_all,     mcmom_e[t])	    	
    	    mclen_e[t].Write()
	    mcpdg_e[t].Write()
    	    mctheta_e[t].Write()
    	    mcphi_e[t].Write()
    	    mcthetaxz_e[t].Write()
    	    mcthetayz_e[t].Write()
    	    mcmom_e[t].Write()


if __name__ == '__main__':
    rc = main(sys.argv)
    sys.exit(rc)
