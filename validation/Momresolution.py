#! /usr/bin/env python
###############################################################################
#
# Name: Momresolution.py
# 
# Purpose: Make and save momentum resolution histograms to a root file. Within 
#          the root file, for each tracker, separate directories are created
#          and plots are stored in their respective directories.
#	   Momentum resolution is calculated for the following:
#          	1. Multiple Coloumb Scattering (MCS method) -- all tracks
#	   	2. Multiple Coloumb Scattering (MCS method) -- contained tracks
# 	   	3. Range based method -- contained tracks
#          	4. Calorimetry method -- contained tracks
#	  Within each tracker directory, seperate directories are created for 
#	  each one of those cases above 
#
# Authors: Sowjanya Gollapinni
#
# Usage:
#
# momentumresolution.py <options>
#
# Options:
#
# --input <inputfile>       - Input AnalysisTree root file.
#
# --output <outputfile>     - Output root file that contain histograms.
#			      by default, output root file name is "momresol.root" 
#
# --tracker <tracker name>  - Optional. Can be separated by commas. 
#                             If not specified, all trackers will be used.
#
# --dataset <dataset name>  - Specify a dataset name, singlemu or BNB etc.
#                             All histograms will be saved in output:
#			      momresolution/dataset/<trackername>/momentum_algorithm
#			      (for each tracker and algorithm separate directories are created)
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
        if line[2:16] == 'momresolution.py':
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
    outfile = 'momresol.root'
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
    mychain.SetBranchStatus("geant_list_size_in_tpcFV",1)
    mychain.SetBranchStatus("inTPCfiducial",1)
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
    
    truelen_all = TH1F('TrueLengthAll','',200,0,2000)
    truemom_all = TH1F('TrueMomAll','',100,0,2 )
    truelen_cont = TH1F('TrueLenCont','',200,0,1000)
    truemom_cont = TH1F('TrueMomCont','',100,0,2)
    
    recolen_all = {}
    recolen_cont = {}
    recolen_match = {}
    recomom ={}
    recomom_match = {}
    resol = {}
    recoVstruth = {}
    resolVstruth = {}
    resolVsreco = {}    
    fillrecolen_all = {}
    fillrecolen_cont = {}
    fillrecolen_match = {}
    fillrecomom ={}
    fillrecomom_match = {}
    fillresol = {}
    fillrecoVstruth = {}
    fillresolVstruth = {}
    fillresolVsreco = {}    
    resol_0to100MeV = {}
    resol_100to200MeV = {}
    resol_200to300MeV = {}
    resol_300to400MeV = {}
    resol_400to500MeV = {}
    resol_500to600MeV = {}
    resol_600to700MeV = {}
    resol_700to800MeV = {}
    resol_800to900MeV = {}
    resol_900to1000MeV = {}
    resol_1000to2000MeV = {}
    fillresol_0to100MeV = {}
    fillresol_100to200MeV = {}
    fillresol_200to300MeV = {}
    fillresol_300to400MeV = {}
    fillresol_400to500MeV = {}
    fillresol_500to600MeV = {}
    fillresol_600to700MeV = {}
    fillresol_700to800MeV = {}
    fillresol_800to900MeV = {}
    fillresol_900to1000MeV = {}
    fillresol_1000to2000MeV = {}    
    
    tag = ["mcsall","mcscont","rangecont","calocont"]  	    
    for t in trackers:
        # Reco length histograms
        recolen_all[t] = TH1F("recolen_all_%s_%s"%(dataset,t),'',200,0,2000);
	fillrecolen_all[t] = recolen_all[t].Fill
	recolen_cont[t] = TH1F("recolen_cont_%s_%s"%(dataset,t),'',200,0,2000);
	fillrecolen_cont[t] = recolen_cont[t].Fill	
	recolen_match[t] = TH1F("recolen_match_%s_%s"%(dataset,t),'',200,0,2000);
	fillrecolen_match[t] = recolen_match[t].Fill		
	# All tracks (MCS method)
	for j in tag:
		recomom[t+j] = TH1F("recomom_%s_%s_%s"%(j,dataset,t),'',100,0,2);
		fillrecomom[t+j] = recomom[t+j].Fill
		recomom_match[t+j] = TH1F("recomom_match_%s_%s_%s"%(j,dataset,t),'',100,0,2);
		fillrecomom_match[t+j] = recomom_match[t+j].Fill
		resol[t+j] = TH1F("resol_%s_%s_%s"%(j, dataset,t),'',100,-2,2);
		fillresol[t+j] = resol[t+j].Fill
		recoVstruth[t+j] = TH2F("recoVstruth_%s_%s_%s"%(j,dataset,t),'',100,0,2,100,0,2);
		fillrecoVstruth[t+j] = recoVstruth[t+j].Fill	
		resolVstruth[t+j] = TH2F("resolVstruth_%s_%s_%s"%(j,dataset,t),'',100,0,2,100,-2,2);
		fillresolVstruth[t+j] = resolVstruth[t+j].Fill	
		resolVsreco[t+j] = TH2F("resolVsreco_%s_%s_%s"%(j,dataset,t),'',100,0,2,100,-2,2);
		fillresolVsreco[t+j] = resolVsreco[t+j].Fill
		# resolution histograms in energy bins for all trackers
		resol_0to100MeV[t+j] =   TH1F("resol_0to100MeV_%s_%s_%s"%(j, dataset,t),'',100,-2,2);
		fillresol_0to100MeV[t+j] = resol_0to100MeV[t+j].Fill
		resol_100to200MeV[t+j] = TH1F("resol_100to200MeV_%s_%s_%s"%(j, dataset,t),'',100,-2,2);
		fillresol_100to200MeV[t+j] = resol_100to200MeV[t+j].Fill
		resol_200to300MeV[t+j] = TH1F("resol_200to300MeV_%s_%s_%s"%(j, dataset,t),'',100,-2,2);
		fillresol_200to300MeV[t+j] = resol_200to300MeV[t+j].Fill
		resol_300to400MeV[t+j] = TH1F("resol_300to400MeV_%s_%s_%s"%(j, dataset,t),'',100,-2,2);
		fillresol_300to400MeV[t+j] = resol_300to400MeV[t+j].Fill
		resol_400to500MeV[t+j] = TH1F("resol_400to500MeV_%s_%s_%s"%(j, dataset,t),'',100,-2,2);
		fillresol_400to500MeV[t+j] = resol_400to500MeV[t+j].Fill
		resol_500to600MeV[t+j] = TH1F("resol_500to600MeV_%s_%s_%s"%(j, dataset,t),'',100,-2,2);
		fillresol_500to600MeV[t+j] = resol_500to600MeV[t+j].Fill
		resol_600to700MeV[t+j] = TH1F("resol_600to700MeV_%s_%s_%s"%(j, dataset,t),'',100,-2,2);
		fillresol_600to700MeV[t+j] = resol_600to700MeV[t+j].Fill
		resol_700to800MeV[t+j] = TH1F("resol_700to800MeV_%s_%s_%s"%(j, dataset,t),'',100,-2,2);
		fillresol_700to800MeV[t+j] = resol_700to800MeV[t+j].Fill
		resol_800to900MeV[t+j] = TH1F("resol_800to900MeV_%s_%s_%s"%(j, dataset,t),'',100,-2,2);
		fillresol_800to900MeV[t+j] = resol_800to900MeV[t+j].Fill
		resol_900to1000MeV[t+j] = TH1F("resol_900to1000MeV_%s_%s_%s"%(j, dataset,t),'',100,-2,2);
		fillresol_900to1000MeV[t+j] = resol_900to1000MeV[t+j].Fill
		resol_1000to2000MeV[t+j] = TH1F("resol_1000to2000MeV_%s_%s_%s"%(j, dataset,t),'',100,-2,2);
		fillresol_1000to2000MeV[t+j] = resol_1000to2000MeV[t+j].Fill		
		resol_0to100MeV[t+j].Sumw2()
		resol_100to200MeV[t+j].Sumw2()
		resol_200to300MeV[t+j].Sumw2()
		resol_300to400MeV[t+j].Sumw2()
		resol_400to500MeV[t+j].Sumw2()
		resol_500to600MeV[t+j].Sumw2()
		resol_600to700MeV[t+j].Sumw2()
		resol_700to800MeV[t+j].Sumw2()
		resol_800to900MeV[t+j].Sumw2()
		resol_900to1000MeV[t+j].Sumw2()
		resol_1000to2000MeV[t+j].Sumw2()
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
	mychain.SetBranchStatus("trkmom_"+t,1)
	mychain.SetBranchStatus("trkmomrange_"+t,1)
	mychain.SetBranchStatus("trkmommschi2_"+t,1)
	dntracks[t] = array("h",[0])
        mychain.SetBranchAddress("ntracks_"+t,dntracks[t])	

    minKE = 0.05
    tagcont = {"mcscont","rangecont","calocont"}
    
    entries = mychain.GetEntriesFast()    
    entries = 5000
    	
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
	    
	for i in xrange( mychain.geant_list_size_in_tpcFV ):
		apdg = abs(mychain.pdg[i])
		if (mychain.inTPCfiducial[i] == 1):		       
			if ( (apdg == 13  and mychain.Eng[i]>=0.001*mychain.Mass[i]+minKE) or (apdg == 211 and mychain.Eng[i]>=0.001*mychain.Mass[i]+minKE) or (apdg == 321 and
	    	        mychain.Eng[i]>=0.001*mychain.Mass[i]+minKE) or (apdg == 2212 and mychain.Eng[i]>=0.001*mychain.Mass[i]+minKE) ):
			        truelen_all.Fill(mychain.pathlen[i])
				truemom_all.Fill(mychain.P[i])
				if (Contained(mychain.StartPointx[i],mychain.StartPointy[i],mychain.StartPointz[i]) and 
				Contained(mychain.EndPointx[i],mychain.EndPointy[i],mychain.EndPointz[i]) ):
					truelen_cont.Fill(mychain.pathlen[i])
					truemom_cont.Fill(mychain.P[i])				    

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
		trkmomcalo = mychain.GetLeaf("trkmom_"+t).GetValue(i)
		trkmomrange = mychain.GetLeaf("trkmomrange_"+t).GetValue(i)
		trkmommcs = mychain.GetLeaf("trkmommschi2_"+t).GetValue(i)
		trkstart3D = math.sqrt((trkstartx*trkstartx)+(trkstarty*trkstarty)+(trkstartz*trkstartz));	       
	 	trkend3D   = math.sqrt((trkendx*trkendx)+(trkendy*trkendy)+(trkendz*trkendz));
		fillrecolen_all[t](trklen)
		fillrecomom[t+"mcsall"](trkmommcs)	
		if ( Contained(trkstartx,trkstarty,trkstartz) and Contained(trkendx,trkendy,trkendz) ):
		        trkstartx_cont = trkstartx
			trkstarty_cont = trkstarty
			trkstartz_cont = trkstartz
			trkendx_cont = trkendx
			trkendy_cont = trkendy
			trkendz_cont = trkendz
			trkstartdcosx_cont = trkstartdcosx
			trkstartdcosy_cont = trkstartdcosy
			trkstartdcosz_cont = trkstartdcosz
			trklen_cont = trklen
			trkmom_calocont = trkmomcalo
			trkmom_rangecont = trkmomrange/1000
			trkmom_mcscont = trkmommcs
			trkstart3D_cont = trkstart3D	 
			trkend3D_cont   = trkend3D
			fillrecolen_cont[t](trklen_cont)
			fillrecomom[t+"calocont"](trkmom_calocont)
			fillrecomom[t+"mcscont"](trkmom_mcscont)
			fillrecomom[t+"rangecont"](trkmom_rangecont)	
		for j in xrange(mychain.geant_list_size_in_tpcFV):
			apdg = abs(mychain.pdg[j])
			mcstartx = mychain.StartPointx_tpcFV[j]
			mcstarty = mychain.StartPointy_tpcFV[j]
			mcstartz = mychain.StartPointz_tpcFV[j]
			mcendx = mychain.EndPointx_tpcFV[j]
			mcendy = mychain.EndPointy_tpcFV[j]
			mcendz = mychain.EndPointz_tpcFV[j]
			theta = mychain.theta[j]*180/3.142
			phi = mychain.phi[j]*180/3.142	
			px = mychain.Px[j]		
			py = mychain.Py[j]		
			pz = mychain.Pz[j]	
			p = mychain.P[j]
			mass = mychain.Mass[j]
			e = mychain.Eng[j]	
			if ( (mychain.inTPCfiducial[j] == 1) and ( (apdg == 13  and e>=0.001*mass+minKE) or (apdg == 211 and e>=0.001*mass+minKE) 
			or (apdg == 321 and e>=0.001*mass+minKE) or (apdg == 2212 and e>=0.001*mass+minKE) ) ):
				# do start point matching
				pmatch1 = math.sqrt(pow(mcstartx-trkstartx,2)+pow(mcstarty-trkstarty,2)+pow(mcstartz-trkstartz,2))
				pmatch2 = math.sqrt(pow(mcstartx-trkendx,2)+pow(mcstarty-trkendy,2)+pow(mcstartz-trkendz,2))
				# do end point matching
				pmatch3 = math.sqrt(pow(mcendx-trkstartx,2)+pow(mcendy-trkstarty,2)+pow(mcendz-trkstartz,2))
				pmatch4 = math.sqrt(pow(mcendx-trkendx,2)+pow(mcendy-trkendy,2)+pow(mcendz-trkendz,2))
				minstart = min(pmatch1, pmatch2)
				minend   = min(pmatch3, pmatch4)
				if ( (minstart<10) and (minend<10)):
					# resolution plots for all tracks (contained+uncontained) MCS method
					fillrecolen_match[t](trklen)
					fillrecomom_match[t+"mcsall"](trkmommcs)
					fillrecoVstruth[t+"mcsall"](p, trkmommcs)					
					resolmcs = (p-trkmommcs)/p
					fillresol[t+"mcsall"](resolmcs)
					fillresolVstruth[t+"mcsall"](p, resolmcs)
	 				fillresolVsreco[t+"mcsall"](trkmommcs, resolmcs)
					if (p>0   and p<= 0.1): 
						fillresol_0to100MeV[t+"mcsall"](resolmcs)
	   	     	     		if (p>0.1 and p<= 0.2): 
						fillresol_100to200MeV[t+"mcsall"](resolmcs)
	   	     	     		if (p>0.2 and p<= 0.3): 
						fillresol_200to300MeV[t+"mcsall"](resolmcs)
	   	     	     		if (p>0.3 and p<= 0.4): 
						fillresol_300to400MeV[t+"mcsall"](resolmcs)
           	     	     		if (p>0.4 and p<= 0.5): 
						fillresol_400to500MeV[t+"mcsall"](resolmcs)
	   	     	     		if (p>0.5 and p<= 0.6): 
						fillresol_500to600MeV[t+"mcsall"](resolmcs)
	   	     	    	   	if (p>0.6 and p<= 0.7): 
						fillresol_600to700MeV[t+"mcsall"](resolmcs)
	   	     	     		if (p>0.7 and p<= 0.8): 
						fillresol_700to800MeV[t+"mcsall"](resolmcs)
	   	     	     		if (p>0.8 and p<= 0.9): 
						fillresol_800to900MeV[t+"mcsall"](resolmcs)
	   	     	     		if (p>0.9 and p<= 1.0): 
						fillresol_900to1000MeV[t+"mcsall"](resolmcs) 
					if (p>1.0 and p<= 2.0): 
						fillresol_1000to2000MeV[t+"mcsall"](resolmcs) 
					# Do resolution analyis for contained tracks now 			   		        
					if ( Contained(mcstartx,mcstarty,mcstartz) and Contained(mcendx,mcendy,mcendz) ):
						for k in tagcont:
							if (k == "mcscont"):
						 		mom = trkmom_mcscont
							if (k == "rangecont"):
						 		mom = trkmom_rangecont
							if (k == "calocont"):
						 		mom = trkmom_calocont		
							res = "resol"+k
							res = (p-mom)/p
							fillrecomom_match[t+k](mom)
							fillrecoVstruth[t+k](p, mom)				
							fillresol[t+k](res)
							fillresolVstruth[t+k](p, res)
							fillresolVsreco[t+k](mom, res)
							#resolution in energy bins histograms for all methods, filled separately of course!
							if (p>0   and p<= 0.1):
								fillresol_0to100MeV[t+k](res)
							if (p>0.1 and p<= 0.2):
							        fillresol_100to200MeV[t+k](res)
							if (p>0.2 and p<= 0.3):
								fillresol_200to300MeV[t+k](res)
							if (p>0.3 and p<= 0.4):
							        fillresol_300to400MeV[t+k](res)
							if (p>0.4 and p<= 0.5):
								fillresol_400to500MeV[t+k](res)
							if (p>0.5 and p<= 0.6): 
								fillresol_500to600MeV[t+k](res)
							if (p>0.6 and p<= 0.7): 
								fillresol_600to700MeV[t+k](res)
							if (p>0.7 and p<= 0.8): 
								fillresol_700to800MeV[t+k](res)
							if (p>0.8 and p<= 0.9): 
								fillresol_800to900MeV[t+k](res)
							if (p>0.9 and p<= 1.0): 
								fillresol_900to1000MeV[t+k](res)
							if (p>1.0 and p<= 2.0): 
								fillresol_1000to2000MeV[t+k](res) 
									
  	

    tagdesc = ["MCSmethod_alltracks", "MCSmethod_contained", "RangeMethod_contained","Calorimetry_contained"]
    hfile = gROOT.FindObject(outfile)
    if hfile:
        hfile.Close()
    hfile = TFile(outfile, 'RECREATE')
    
    dir1 = hfile.mkdir('momresolution')
    dir1.cd()
    
    if dataset!='':
        dir2 = dir1.mkdir(dataset)
        dir2.cd()	

    
    truelen_all.Write() 
    truemom_all.Write() 
    truelen_cont.Write()
    truemom_cont.Write()	
    # Fill the efficiency histograms	
    for t in trackers:		
	    direc = dir2.mkdir(str(t))
            direc.cd()	
	    recolen_all[t].Write()
	    recolen_cont[t].Write()
	    recolen_match[t].Write()
	    k=-1
	    for j in tag:
	     	    k=k+1
	    	    direc1 = direc.mkdir(tagdesc[k])
		    direc1.cd()		    
		    recomom[t+j].Write()
		    recomom_match[t+j].Write()
		    resol[t+j].Write()
		    recoVstruth[t+j].Write()
		    resolVstruth[t+j].Write()
		    resolVsreco[t+j].Write()	
	    	    resol_0to100MeV[t+j].Write()
		    resol_100to200MeV[t+j].Write()
		    resol_200to300MeV[t+j].Write()
		    resol_300to400MeV[t+j].Write()
		    resol_400to500MeV[t+j].Write()
		    resol_500to600MeV[t+j].Write()
		    resol_600to700MeV[t+j].Write()
		    resol_700to800MeV[t+j].Write()
		    resol_800to900MeV[t+j].Write()
		    resol_900to1000MeV[t+j].Write()
		    resol_1000to2000MeV[t+j].Write()	    
            


if __name__ == '__main__':
    rc = main(sys.argv)
    sys.exit(rc)
