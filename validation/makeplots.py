#! /usr/bin/env python
###############################################################################
#
# Name: makeplots.py
# 
# Purpose: Make plots from root files and save them in gif and pdf or ps formats.
# 	   In the case of hit data, all gif/pdf files are written to a directory 
#	   called "hits". In the case of tracking, calorimetry, momentum resolution, 
#	   a postscript file is created tracking.ps, calorimetry.ps and 
#   	   momresolu.ps and all plots are written to the postscript file.
#
# Authors: Tingjun Yang, Sowjanya Gollapinni
#
# Usage:
#
# makeplots.py <options>
#
# Options:
#
# --input <inputfile> - Inputfile(s) that contain histograms, 
#                       can be seperated by commas
#
# --calorimetry       - Make calorimetry validation plots
#
# --tracking	      - Make tracking validation plots
#
# --momresol	      - Make momentum resolution plots 
#
# --hit               - Make hitfinder validation plots
#
# --flash             - Make flash validation plots
#
# --pid	              - Make PID plots
#
# --dir 	      - Specify an ouput directory to dump all the
#			.ps and .gif files
#
#
###############################################################################
import sys, os
# Prevent root from printing garbage on initialization.
if os.environ.has_key('TERM'):
    del os.environ['TERM']

# Hide command line arguments from ROOT module.
myargv = sys.argv
sys.argv = myargv[0:1]
sys.argv.append( '-b' )

from ROOT import TFile, TCanvas, TH1F, TH2F, TProfile, TLegend, TF1
from ROOT import gDirectory, gROOT, gPad
#ROOT.gErrorIgnoreLevel = ROOT.kError
sys.argv = myargv

from validation_utilities import *

# Get the object with a given name from a list of objects in the directory
def GetObject(name,list):
    for i in list:
        if i.GetName()==name:
            return i.ReadObj()
    return 0

#rearrange stat boxes, from Trish Vahle
def SortOutStats(pad, fracPadx, fracPady, startx, starty):
    pad.Update()
    pad.Modified()
    numStats = 0
    list = pad.GetListOfPrimitives()
    for i in list:
        if i.InheritsFrom('TH1'):
            numStats += 1
    if numStats != 0:
        xwidth = fracPadx
        ywidth = fracPady
        xgap = 0.01
        ygap = 0.01
        x2 = startx
        y2 = starty
        x1 = x2 - xwidth
        y1 = y2 - ywidth
        cnt = 0
        for i in list:
            if i.InheritsFrom('TH1'):
                col = i.GetLineColor()
                stat = i.FindObject('stats')
                stat.SetTextColor(col)
                stat.SetX1NDC(x1)
                stat.SetX2NDC(x2)
                stat.SetY1NDC(y1-cnt*(ywidth+ygap))
                stat.SetY2NDC(y2-cnt*(ywidth+ygap))
                cnt+=1

# Plot 1d histograms and make legends.
def plot1d(dataset,hname,inname,can,leg,nplots,list):
    if dataset not in can:
        nplots[dataset] = 0
        can[dataset] = TCanvas('can'+hname+dataset,'can'+hname+dataset,800,600)
        leg[dataset] = TLegend(0.67,0.2,0.9,0.35)
        leg[dataset].SetFillStyle(0)
    can[dataset].cd()
    nplots[dataset] += 1
    hist = GetObject(hname+dataset,list)
    if hist:
        if nplots[dataset] == 1:
            hist.GetXaxis().SetLabelSize(0.04)
            hist.Draw()
        else:
            hist.SetLineColor(nplots[dataset])
            hist.Draw("sames")
            hist1 = gPad.GetListOfPrimitives()[0]
            if hist.GetMaximum()*1.1>hist1.GetMaximum():
                  hist1.GetYaxis().SetRangeUser(0,hist.GetMaximum()*1.1)
        leg[dataset].AddEntry(hist,inname,'l')


# Plot 1d histograms and make legends.
def plot1d3plane(dataset,hname,inname,can,leg,nplots,list,drawopt=''):
    if dataset not in can:
        nplots[dataset] = 0
        can[dataset] = TCanvas('can'+hname+dataset,'can'+hname+dataset,1000,800)
        can[dataset].Divide(2,2)
        leg[dataset] = TLegend(0.67,0.2,0.9,0.35)
        leg[dataset].SetFillStyle(0)
    can[dataset].cd()
    nplots[dataset] += 1
    for i in range(3):
        can[dataset].cd(i+1)
        hist = GetObject(hname+str(i)+dataset,list)
        if hist:
            if drawopt=='colz':
                hist.SetStats(0)
            if nplots[dataset] == 1:
                hist.GetXaxis().SetLabelSize(0.04)
                hist.Draw(drawopt)
            else:
                hist.SetLineColor(nplots[dataset])
                hist.Draw('sames'+drawopt)
                hist1 = gPad.GetListOfPrimitives()[0]
                if hist.GetMaximum()>hist1.GetMaximum():
                    hist1.GetYaxis().SetRangeUser(0,hist.GetMaximum()*1.2)
            if i==0:
                leg[dataset].AddEntry(hist,inname,'l')


def savecanvas1d(datasets,can,leg,hname):
    for i in datasets:
        can[i].cd()
        leg[i].Draw()
        SortOutStats(gPad,0.23,0.25,0.9,0.9)
        can[i].Print(hname+'_%s.gif'%i)
        can[i].Print(hname+'_%s.pdf'%i)
    
def savecanvas1d3plane(datasets,can,leg,hname):
    for i in datasets:
        for j in range(3):
            can[i].cd(j+1)
            leg[i].Draw()
            SortOutStats(gPad,0.23,0.25,0.9,0.9)
        can[i].Print(hname+'_%s.gif'%i)
        can[i].Print(hname+'_%s.pdf'%i)

# Print help.

def help():

    filename = sys.argv[0]
    file = open(filename, 'r')

    doprint=0
    
    for line in file.readlines():
        if line[2:14] == 'makeplots.py':
            doprint = 1
        elif line[0:6] == '######' and doprint:
            doprint = 0
        if doprint:
            if len(line) > 2:
                print line[2:],
            else:
                print

# Make calorimetry validation plots.
def plotcalorimetry(infile):
    infiles = infile.split(",")
    myfile = {}
    innames = []
    trackers = []
    datasets = []
    muondEdxR = GetMuondEdxR()
    muondEdxR.SetMarkerStyle(20)
    muondEdxR.SetMarkerSize(0.3)
    muondEdxR.SetMarkerColor(800)
    muondEdxR.SetLineColor(800)
    muondEdxR.SetLineWidth(2)
    protondEdxR = TF1('protondEdxR','17*pow(x,-0.42)',0,30)
    protondEdxR.SetMarkerColor(2)
    protondEdxR.SetLineColor(2)
    protondEdxR.SetLineWidth(2)
    muonKeLen = GetMuonKELen()
    muonKeLen.SetMarkerStyle(20)
    muonKeLen.SetMarkerSize(0.3)
    muonKeLen.SetMarkerColor(800)
    muonKeLen.SetLineColor(800)
    muonKeLen.SetLineWidth(2)
    protonKeLen = GetProtonKELen()
    protonKeLen.SetMarkerStyle(20)
    protonKeLen.SetMarkerSize(0.3)
    protonKeLen.SetMarkerColor(1)
    protonKeLen.SetLineColor(2)
    protonKeLen.SetLineWidth(2)

    legdedxrr1 = TLegend(0.5,0.7,0.7,0.9)
    legdedxrr1.AddEntry(protondEdxR,"Proton","l")
    legdedxrr1.AddEntry(muondEdxR,"Muon","l")

    legkelen1 = TLegend(0.65,0.2,0.85,0.4)
    legkelen1.AddEntry(protonKeLen,"Proton","l")
    legkelen1.AddEntry(muonKeLen,"Muon","l")

    candedxrr = {}
    candedx = {}
    nplotsdedx = {}
    legdedx = {}
    cankelen = {}
    legkelen = {}
    nplotskelen = {}
    # Open all the input root files.
    for file in infiles:
        inname = os.path.splitext(file)[0]
        if inname not in innames:
            innames.append(inname)
        myfile[inname] = TFile(file)
        list1 = myfile[inname].GetListOfKeys()
        # Go to directory calorimetry
        for i in list1:
            if i.GetClassName() == 'TDirectoryFile':
                myfile[inname].cd(i.GetName())
                list2 = gDirectory.GetListOfKeys()
                # Go to dataset directory
                for j in list2:
                    if j.GetClassName() == 'TDirectoryFile':
                        dataset = '%s'%j.GetName()
                        if dataset not in datasets:
                            datasets.append(dataset)
                        gDirectory.cd(dataset)
                        list3 = gDirectory.GetListOfKeys()
                        # Get all tracker names.
                        if len(trackers) == 0:
                            for k in list3:
                                name = k.GetName()
                                tracker = name[name.rfind(dataset)+len(dataset):]
                                if tracker not in trackers:
                                    trackers.append(tracker)
                        # Loop over all trackers and make dE/dx vs Residual Range and dE/dx plots.
                        for t in trackers:
                            #dE/dx vs Residual Range plots.
                            if inname+dataset+t not in candedxrr:
                                candedxrr[inname+dataset+t] = TCanvas("candedxrr_"+inname+dataset+t,"candedxrr_"+inname+dataset+t,1000,800)
                                candedxrr[inname+dataset+t].Divide(2,2)
                                for i in range(3):
                                    candedxrr[inname+dataset+t].cd(i+1)
                                    dedxrr = GetObject('dedxrr%d%s%s'%(i,dataset,t), list3)
                                    if dedxrr:
                                        dedxrr.Draw("colz")
#                                        if 'pro' in dataset:
#                                            dedxrr.GetXaxis().SetRangeUser(0,300)
                                    pdedxrr = GetObject('pdedxrr%d%s%s'%(i,dataset,t), list3)
                                    if pdedxrr:
                                        pdedxrr.SetMarkerStyle(20)
                                        pdedxrr.SetMarkerSize(0.03)
                                        pdedxrr.Draw("same")
                                    muondEdxR.Draw("pc")
                                    protondEdxR.Draw("same")
                                    legdedxrr1.Draw()
                            # dE/dx plots.
                            plot1d3plane(dataset+t,'dedx',inname,candedx,legdedx,nplotsdedx,list3)
                            plot1d3plane(dataset+t,'kelen',inname,cankelen,legkelen,nplotskelen,list3,'colz')
                        gDirectory.cd("..")
    
    if not os.path.exists('calorimetry'):
    	os.makedirs('calorimetry')
    os.chdir('calorimetry')
    
    #Save dE/dx vs Residula Range plots.
    for i in innames:
        for j in datasets:
            for k in trackers:
                if i+j+k in candedxrr:
                    candedxrr[i+j+k].cd()
                    candedxrr[i+j+k].Update()
                    candedxrr[i+j+k].Print('dedxrr_%s_%s.gif'%(j,k))
                    candedxrr[i+j+k].Print('dedxrr_%s_%s.pdf'%(j,k))
                    #candedxrr[i+j+k].Print('dedxrr_%s_%s_%s.pdf'%(i,j,k))
		    candedxrr[i+j+k].Print("calorimetry.ps(")

    #Save dE/dx plots.
    for i in datasets:
        for j in trackers:
            if i+j in candedx:
                for k in range(3):
                    candedx[i+j].cd(k+1)
                    legdedx[i+j].Draw()
                    SortOutStats(gPad,0.3,0.25,0.9,0.9)
                #if (count == len(trackers)*len(datasets)):
		candedx[i+j].Print('dedx_%s_%s.gif'%(i,j))
		candedx[i+j].Print('dedx_%s_%s.pdf'%(i,j))
                candedx[i+j].Print("calorimetry.ps")
            #else:			
                #candedx[i+j].Print("calorimetry.ps(")	
			#candedx[i+j].Print('dedx_%s_%s.gif'%(i,j))
                	#candedx[i+j].Print('dedx_%s_%s.pdf'%(i,j))    
                        
    count = 0	
    #Save KE vs length plot.
    for i in datasets:
        for j in trackers:
            if i+j in cankelen:
                for k in range(3):
                    cankelen[i+j].cd(k+1)
#                    legkelen[i+j].Draw()
                    muonKeLen.Draw("pc")
                    protonKeLen.Draw("pc")
                    legkelen1.Draw()
#                    legkelen = TLegend(0.5,0.5,0.7,0.9)
#                    legkelen.AddEntry(muonKeLen,"Muon","l")
#                    legkelen.AddEntry(protonKeLen,"Proton","l")
#                    legkelen.Draw()
                    #SortOutStats(gPad,0.3,0.25,0.9,0.9)
		count = count+1
		cankelen[i+j].Print('kelen_%s_%s.gif'%(i,j))
		cankelen[i+j].Print('kelen_%s_%s.pdf'%(i,j))
                if (count == len(trackers)*len(datasets)):
                    cankelen[i+j].Print("calorimetry.ps)")
		else:			
                    cankelen[i+j].Print("calorimetry.ps(")	
			#cankelen[i+j].Print('kelen_%s_%s.gif'%(i,j))
                	#cankelen[i+j].Print('kelen_%s_%s.pdf'%(i,j))    


def plottracking(infile):
    infiles = infile.split(",")
    myfile = {}
    innames = []
    trackers = []
    datasets = []
    can = {}
    # Open all the input root files.
    for file in infiles:
        inname = os.path.splitext(file)[0]
        if inname not in innames:
            innames.append(inname)
        myfile[inname] = TFile(file)
        list1 = myfile[inname].GetListOfKeys()
	# Go to directory tracking
	for i in list1:
            if i.GetClassName() == 'TDirectoryFile':
                myfile[inname].cd(i.GetName())
                list2 = gDirectory.GetListOfKeys()
                # Go to dataset directory 
		for j in list2:
			if j.GetClassName() == 'TDirectoryFile':
                            dataset = '%s'%j.GetName()
                            if dataset not in datasets:
                                datasets.append(dataset)
                            gDirectory.cd(dataset)
                            list3 = gDirectory.GetListOfKeys()
			    # Get all the tracker (directory) names
			    for k in list3:
				if k.GetClassName() == 'TDirectoryFile':
				    t = '%s'%k.GetName()
				if t not in trackers:
                                    trackers.append(t)    			     
			        topdir = inname+".root:/tracking/"+dataset    
			        gDirectory.cd(topdir)	
	   		        gDirectory.cd(t)			   
			        list4 = gDirectory.GetListOfKeys()
			        can[inname+dataset+t]=TCanvas("can_"+inname+"_"+dataset+"_"+t,"can_"+inname+dataset+t,1000,800)
			        can[inname+dataset+t].Divide(3,2)
			        mclen = GetObject('mclen_e_%s_%s'%(dataset,t),list4)
			        #mcpdg = GetObject('mcpdg_e_%s_%s'%(dataset,t),list4)
			        mctheta = GetObject('mctheta_e_%s_%s'%(dataset,t),list4)
			        mcphi = GetObject('mcphi_e_%s_%s'%(dataset,t),list4)
			        mcthetaxz = GetObject('mcthetaxz_e_%s_%s'%(dataset,t),list4)
			        mcthetayz = GetObject('mcthetayz_e_%s_%s'%(dataset,t),list4)
			        mcmom = GetObject('mcmom_e_%s_%s'%(dataset,t),list4)
			        can[inname+dataset+t].cd(1)
			        mclen.Draw()
			        can[inname+dataset+t].cd(2)
			        mctheta.Draw()
			        can[inname+dataset+t].cd(3)
			        mcphi.Draw()
			        can[inname+dataset+t].cd(4)
			        mcthetaxz.Draw()
			        can[inname+dataset+t].cd(5)
			        mcthetayz.Draw()
			        can[inname+dataset+t].cd(6)
			        mcmom.Draw()	
    
    if not os.path.exists('tracking'):
    	os.makedirs('tracking')
    os.chdir('tracking')
    count = 0
    for i in innames:
        for j in datasets:
            for k in trackers:
                if i+j+k in can:
		    count = count+1
		    can[i+j+k].Print('eff_%s_%s.gif'%(j,k))
		    can[i+j+k].Print('eff_%s_%s.pdf'%(j,k))
		    if (count == len(trackers)*len(innames)*len(datasets)):
		        can[i+j+k].Print("tracking.ps)")
		    else:		
		        can[i+j+k].Print("tracking.ps(")	
			
def plotpid(infile):
    infiles = infile.split(",")
    myfile = {}
    innames = []
    trackers = []
    datasets = []
    can = {}
    # Open all the input root files.
    for file in infiles:
        inname = os.path.splitext(file)[0]
        if inname not in innames:
            innames.append(inname)
        myfile[inname] = TFile(file)
        list1 = myfile[inname].GetListOfKeys()
	# Go to directory pid
	for i in list1:
            if i.GetClassName() == 'TDirectoryFile':
                myfile[inname].cd(i.GetName())
                list2 = gDirectory.GetListOfKeys()
                # Go to dataset directory 
		for j in list2:
			if j.GetClassName() == 'TDirectoryFile':
                            dataset = '%s'%j.GetName()
                            if dataset not in datasets:
                                datasets.append(dataset)
                            gDirectory.cd(dataset)
                            list3 = gDirectory.GetListOfKeys()
			    # Get all the tracker (directory) names
			    for k in list3:
				if k.GetClassName() == 'TDirectoryFile':
				    t = '%s'%k.GetName()
				if t not in trackers:
                                    trackers.append(t)    			     
			        topdir = inname+".root:/pid/"+dataset    
			        gDirectory.cd(topdir)	
	   		        gDirectory.cd(t)			   
			        list4 = gDirectory.GetListOfKeys()
			        can[inname+dataset+t]=TCanvas("can_"+inname+"_"+dataset+"_"+t,"can_"+inname+dataset+t,1000,800)
			        can[inname+dataset+t].Divide(1,2)
			        pida = GetObject('pida_%s_%s'%(dataset,t),list4)
			        pdgchi2 = GetObject('pdgchi2_%s_%s'%(dataset,t),list4)
			        can[inname+dataset+t].cd(1)
			        pida.Draw()
			        can[inname+dataset+t].cd(2)
			        pdgchi2.Draw()
			        
    
    if not os.path.exists('pid'):
    	os.makedirs('pid')
    os.chdir('pid')
    count = 0
    for i in innames:
        for j in datasets:
            for k in trackers:
                if i+j+k in can:
		    count = count+1
		    can[i+j+k].Print('pid_%s_%s.gif'%(j,k))
		    can[i+j+k].Print('pid_%s_%s.pdf'%(j,k))		    
		    if (count == len(trackers)*len(innames)*len(datasets)):
		        can[i+j+k].Print("pid.ps)")
		    else:			
			can[i+j+k].Print("pid.ps(")				

def plotmomresolution(infile):
    infiles = infile.split(",")
    myfile = {}
    innames = []
    trackers = []
    momalgs = []
    datasets = []
    cantrue = {}
    legtruelen = {}
    legtruemom = {}
    canrecolen = {}
    legrecolen = {}
    canrecomom = {}
    legrecomom = {}    
    can1 = {}
    can2 = {}
    momtags = ["mcsall", "mcscont", "rangecont", "calocont"]
    # Open all the input root files.
    for file in infiles:
        inname = os.path.splitext(file)[0]
        if inname not in innames:
            innames.append(inname)
        myfile[inname] = TFile(file)
        list1 = myfile[inname].GetListOfKeys()
	# Go to directory momresolution
	for i in list1:
            if i.GetClassName() == 'TDirectoryFile':
                myfile[inname].cd(i.GetName())
                list2 = gDirectory.GetListOfKeys()
                # Go to dataset directory 
		for j in list2:
			if j.GetClassName() == 'TDirectoryFile':
                            dataset = '%s'%j.GetName()
                            if dataset not in datasets:
                                datasets.append(dataset)
                            gDirectory.cd(dataset)
                            list3 = gDirectory.GetListOfKeys()
			    cantrue[inname+dataset] = TCanvas("cantrue_"+inname+"_"+dataset,"cantrue"+inname+dataset,1200,500)
			    legtruelen[inname+dataset] = TLegend(0.7,0.2,0.9,0.35)
    			    legtruelen[inname+dataset].SetFillStyle(0)
			    legtruemom[inname+dataset] = TLegend(0.1,0.7,0.4,0.85)
    			    legtruemom[inname+dataset].SetFillStyle(0)
			    cantrue[inname+dataset].Divide(2,1)
			    cantrue[inname+dataset].cd(1)
    			    truelenall = GetObject('truelen_all_%s'%(dataset),list3)
			    truelencont = GetObject('truelen_cont_%s'%(dataset),list3)
			    truemomall  = GetObject('truemom_all_%s'%(dataset),list3)
			    truemomcont = GetObject('truemom_cont_%s'%(dataset),list3)
			    if truelenall:	
			    	truelenall.Draw()
			    if truelencont:
			    	truelencont.SetLineColor(2)
			    	truelencont.Draw("sames")
			    legtruelen[inname+dataset].AddEntry(truelenall,'all tracks','l')
			    legtruelen[inname+dataset].AddEntry(truelencont,'cont tracks','l')
			    legtruelen[inname+dataset].Draw("same")
			    SortOutStats(gPad,0.2,0.25,0.9,0.9)
			    cantrue[inname+dataset].cd(2)
			    if truemomall:	
			    	truemomall.Draw()
			    if truemomcont:
			    	truemomcont.SetLineColor(2)
			    	truemomcont.Draw("sames")
			    legtruemom[inname+dataset].AddEntry(truemomall,'all tracks','l')
			    legtruemom[inname+dataset].AddEntry(truemomcont,'cont tracks','l')
			    legtruemom[inname+dataset].Draw("same")
			    SortOutStats(gPad,0.2,0.25,0.9,0.9)
			    for k in list3:
				if k.GetClassName() == 'TDirectoryFile':
				    t = '%s'%k.GetName()
				    if t not in trackers:
                                       trackers.append(t)    			     
			            topdir = inname+".root:/momresolution/"+dataset    
			            gDirectory.cd(topdir)	
	   		            gDirectory.cd(t)			   
			            list4 = gDirectory.GetListOfKeys()
				    canrecolen[inname+dataset+t] = TCanvas("canrecolen_"+inname+"_"+dataset+"_"+t,"canrecolen"+inname+dataset+t)
				    legrecolen[inname+dataset+t] = TLegend(0.1,0.7,0.4,0.85)
				    legrecolen[inname+dataset+t].SetFillStyle(0)
				    canrecolen[inname+dataset+t].cd()
				    recolenall = GetObject('recolen_all_%s_%s'%(dataset,t),list4)
				    recolencont = GetObject('recolen_cont_%s_%s'%(dataset,t),list4)
				    recolenmatch  = GetObject('recolen_match_%s_%s'%(dataset,t),list4)
				    if recolenall:	
				    	recolenall.Draw()
				    if recolencont:
				    	recolencont.SetLineColor(2)
				    	recolencont.Draw("sames")
				    if recolenmatch:
				    	recolenmatch.SetLineColor(3)
					recolenmatch.Draw("sames")	
				    legrecolen[inname+dataset+t].AddEntry(recolenall,'all tracks','l')
				    legrecolen[inname+dataset+t].AddEntry(recolencont,'cont tracks','l')
				    legrecolen[inname+dataset+t].AddEntry(recolenmatch,'matched tracks','l')	
				    legrecolen[inname+dataset+t].Draw("same")
			    	    SortOutStats(gPad,0.2,0.25,0.9,0.9)			    
				    c = -1
				    for k1 in list4:
					if k1.GetClassName() == 'TDirectoryFile':
				   		m = '%s'%k1.GetName()
						c += 1
						if m not in momalgs:    
		 		     	  		 momalgs.append(m)
						subtopdir = inname+".root:/momresolution/"+dataset+"/"+t
						gDirectory.cd(subtopdir)
						gDirectory.cd(m)
						list5 = gDirectory.GetListOfKeys()
						canrecomom[inname+dataset+t+momtags[c]] = TCanvas("canrecomom_"+inname+"_"+dataset+"_"+t+"_"+momtags[c],"canrecomom"+inname+dataset+t+momtags[c])
						legrecomom[inname+dataset+t+momtags[c]] = TLegend(0.1,0.7,0.4,0.85)
						legrecomom[inname+dataset+t+momtags[c]].SetFillStyle(0)
						canrecomom[inname+dataset+t+momtags[c]].cd()
						recomomall = GetObject('recomom_%s_%s_%s'%(dataset,t,momtags[c]),list5)
						recomommatch = GetObject('recomom_match_%s_%s_%s'%(dataset,t,momtags[c]),list5)
						if recomomall:    
						    recomomall.Draw()
						if recomommatch:
						    recomommatch.SetLineColor(2)
						    recomommatch.Draw("sames")
						legrecomom[inname+dataset+t+momtags[c]].AddEntry(recomomall,'all tracks','l')
				   		legrecomom[inname+dataset+t+momtags[c]].AddEntry(recomommatch,'matched tracks','l')
						legrecomom[inname+dataset+t+momtags[c]].Draw("same")
			    			SortOutStats(gPad,0.2,0.25,0.9,0.9)
						can1[inname+dataset+t+momtags[c]]=TCanvas("can1_"+inname+"_"+dataset+"_"+t+"_"+momtags[c],"can1_"+inname+dataset+t+momtags[c])
						can1[inname+dataset+t+momtags[c]].Divide(2,4)
						can2[inname+dataset+t+momtags[c]]=TCanvas("can2_"+inname+"_"+dataset+"_"+t+"_"+momtags[c],"can2_"+inname+dataset+t+momtags[c])
						can2[inname+dataset+t+momtags[c]].Divide(2,4)
						recovstruth = GetObject('recoVstruth_%s_%s_%s'%(dataset,t,momtags[c]),list5)
						resolvstruth = GetObject('resolVstruth_%s_%s_%s'%(dataset,t,momtags[c]),list5)
						resolvsreco = GetObject('resolVsreco_%s_%s_%s'%(dataset,t,momtags[c]),list5)
						resol = GetObject('resol_%s_%s_%s'%(dataset,t,momtags[c]),list5)
						resol1 = GetObject('resol_0to100MeV_%s_%s_%s'%(dataset,t,momtags[c]),list5)
						resol2 = GetObject('resol_100to200MeV_%s_%s_%s'%(dataset,t,momtags[c]),list5)
						resol3 = GetObject('resol_200to300MeV_%s_%s_%s'%(dataset,t,momtags[c]),list5)
						resol4 = GetObject('resol_300to400MeV_%s_%s_%s'%(dataset,t,momtags[c]),list5)
						resol5 = GetObject('resol_400to500MeV_%s_%s_%s'%(dataset,t,momtags[c]),list5)
						resol6 = GetObject('resol_500to600MeV_%s_%s_%s'%(dataset,t,momtags[c]),list5)
						resol7 = GetObject('resol_600to700MeV_%s_%s_%s'%(dataset,t,momtags[c]),list5)
						resol8 = GetObject('resol_700to800MeV_%s_%s_%s'%(dataset,t,momtags[c]),list5)
						resol9 = GetObject('resol_800to900MeV_%s_%s_%s'%(dataset,t,momtags[c]),list5)
						resol10 = GetObject('resol_900to1000MeV_%s_%s_%s'%(dataset,t,momtags[c]),list5)
						resol11 = GetObject('resol_1000to2000MeV_%s_%s_%s'%(dataset,t,momtags[c]),list5)
						can1[inname+dataset+t+momtags[c]].cd(1)
						recovstruth.Draw("colz")
						can1[inname+dataset+t+momtags[c]].cd(2)
				     	        resolvstruth.Draw("colz")
				    	        can1[inname+dataset+t+momtags[c]].cd(3)
				                resolvsreco.Draw("colz")
				                can1[inname+dataset+t+momtags[c]].cd(4)
				                resol.Draw()
				                can1[inname+dataset+t+momtags[c]].cd(5)
				                resol1.Draw()
				                can1[inname+dataset+t+momtags[c]].cd(6)
				                resol2.Draw()
				        	can1[inname+dataset+t+momtags[c]].cd(7)
				        	resol3.Draw()
				       	        can1[inname+dataset+t+momtags[c]].cd(8)
				       	        resol4.Draw()
				        	#
				        	can2[inname+dataset+t+momtags[c]].cd(1)
				        	resol5.Draw()
				        	can2[inname+dataset+t+momtags[c]].cd(2)
				        	resol6.Draw()
				        	can2[inname+dataset+t+momtags[c]].cd(3)
				        	resol7.Draw()
				        	can2[inname+dataset+t+momtags[c]].cd(4)
				        	resol8.Draw()
				        	can2[inname+dataset+t+momtags[c]].cd(5)
				        	resol9.Draw()
				        	can2[inname+dataset+t+momtags[c]].cd(6)
				        	resol10.Draw()
				        	can2[inname+dataset+t+momtags[c]].cd(7)
				        	resol11.Draw()
					
					    
    
    if not os.path.exists('momresolution'):
    	os.makedirs('momresolution')
    os.chdir('momresolution')
    count = 0
    for i in innames:
        for j in datasets:
	    cantrue[i+j].Print('cantrue_%s.png'%(j)) 
	    cantrue[i+j].Print('cantrue_%s.pdf'%(j)) 
	    cantrue[i+j].Print("momresolu.ps(")
            for k in trackers:
	        canrecolen[i+j+k].Print('canrecolen_%s_%s.png'%(j,k))
	        canrecolen[i+j+k].Print('canrecolen_%s_%s.pdf'%(j,k))
	    	canrecolen[i+j+k].Print("momresolu.ps")
	    	for l in momtags:
		       count = count+1
		       canrecomom[i+j+k+l].Print('canrecomom_%s_%s_%s.png'%(j,k,l))
		       canrecomom[i+j+k+l].Print('canrecomom_%s_%s_%s.pdf'%(j,k,l))
	    	       canrecomom[i+j+k+l].Print("momresolu.ps")
 	               if i+j+k+l in can1:
		              can1[i+j+k+l].Print('can1_%s_%s_%s.pdf'%(j,k,l))
			      can1[i+j+k+l].Print('can1_%s_%s_%s.gif'%(j,k,l))
			      can1[i+j+k+l].Print('can1_%s_%s_%s.png'%(j,k,l))
		    	      can1[i+j+k+l].Print("momresolu.ps")
		       if i+j+k+l in can2:
		              can2[i+j+k+l].Print('can2_%s_%s_%s.pdf'%(j,k,l))
			      can2[i+j+k+l].Print('can2_%s_%s_%s.png'%(j,k,l))
			      can2[i+j+k+l].Print('can2_%s_%s_%s.gif'%(j,k,l))
		       	      if (count==len(momtags)):	
		    		   can2[i+j+k+l].Print("momresolu.ps)")
		    	      else:			
		        	   can2[i+j+k+l].Print("momresolu.ps")
   			    
    		

def plothit(infile):
    infiles = infile.split(",")
    myfile = {}
    innames = []
    datasets = []
    canno_hits = {}
    nplotsno_hits = {}
    legno_hits = {}
    canhit_plane = {}
    nplotshit_plane = {}
    leghit_plane = {}
    canhit_wire = {}
    nplotshit_wire = {}
    leghit_wire = {}
    canhit_channel = {}
    nplotshit_channel = {}
    leghit_channel = {}
    canhit_peakT = {}
    nplotshit_peakT = {}
    leghit_peakT = {}
    canhit_charge = {}
    nplotshit_charge = {}
    leghit_charge = {}
    canhit_ph = {}
    nplotshit_ph = {}
    leghit_ph = {}
    canphperelec = {}
    nplotsphperelec = {}
    legphperelec = {}
    canchargeperelec = {}
    nplotschargeperelec = {}
    legchargeperelec = {}

    # Open all the input root files.
    for file in infiles:
        inname = os.path.splitext(file)[0]
        if inname not in innames:
            innames.append(inname)
        myfile[inname] = TFile(file)
        list1 = myfile[inname].GetListOfKeys()
        # Go to directory calorimetry
        for i in list1:
            if i.GetClassName() == 'TDirectoryFile' and i.GetName() == 'hit':
                myfile[inname].cd(i.GetName())
                list2 = gDirectory.GetListOfKeys()
                # Go to dataset directory
                for j in list2:
                    if j.GetClassName() == 'TDirectoryFile':
                        dataset = '%s'%j.GetName()
                        if dataset not in datasets:
                            datasets.append(dataset)
                        gDirectory.cd(dataset)
                        list3 = gDirectory.GetListOfKeys()
                        plot1d(dataset,'hno_hits',inname,canno_hits,legno_hits,nplotsno_hits,list3)
                        plot1d(dataset,'hhit_plane',inname,canhit_plane,leghit_plane,nplotshit_plane,list3)
                        plot1d(dataset,'hhit_wire',inname,canhit_wire,leghit_wire,nplotshit_wire,list3)
                        plot1d(dataset,'hhit_channel',inname,canhit_channel,leghit_channel,nplotshit_channel,list3)
                        plot1d(dataset,'hhit_peakT',inname,canhit_peakT,leghit_peakT,nplotshit_peakT,list3)
                        plot1d3plane(dataset,'hhit_charge',inname,canhit_charge,leghit_charge,nplotshit_charge,list3)
                        plot1d3plane(dataset,'hhit_ph',inname,canhit_ph,leghit_ph,nplotshit_ph,list3)
                        plot1d3plane(dataset,'hphperelec',inname,canphperelec,legphperelec,nplotsphperelec,list3)
                        plot1d3plane(dataset,'hchargeperelec',inname,canchargeperelec,legchargeperelec,nplotschargeperelec,list3)
                        gDirectory.cd("..")
    # Write all the plots into a separate directory
    if not os.path.exists('hits'):
    	os.makedirs('hits')
    os.chdir('hits')	
    savecanvas1d(datasets,canno_hits,legno_hits,'no_hits')
    savecanvas1d(datasets,canhit_plane,leghit_plane,'hit_plane')
    savecanvas1d(datasets,canhit_wire,leghit_wire,'hit_wire')
    savecanvas1d(datasets,canhit_channel,leghit_channel,'hit_channel')
    savecanvas1d(datasets,canhit_peakT,leghit_peakT,'hit_peakT')
    savecanvas1d3plane(datasets,canhit_charge,leghit_charge,'hit_charge')
    savecanvas1d3plane(datasets,canhit_ph,leghit_ph,'hit_ph')
    savecanvas1d3plane(datasets,canphperelec,legphperelec,'phperelec')
    savecanvas1d3plane(datasets,canchargeperelec,legchargeperelec,'chargeperelec')

def plotflash(infile):
    infiles = infile.split(",")
    myfile = {}
    innames = []
    datasets = []
    canno_flashes = {}
    nplotsno_flashes = {}
    legno_flashes = {}
    canflash_time = {}
    nplotsflash_time = {}
    legflash_time = {}
    canflash_pe = {}
    nplotsflash_pe = {}
    legflash_pe = {}
    canflash_ycenter = {}
    nplotsflash_ycenter = {}
    legflash_ycenter = {}
    canflash_zcenter = {}
    nplotsflash_zcenter = {}
    legflash_zcenter = {}
    # Open all the input root files.
    for file in infiles:
        inname = os.path.splitext(file)[0]
        if inname not in innames:
            innames.append(inname)
        myfile[inname] = TFile(file)
        list1 = myfile[inname].GetListOfKeys()
        # Go to directory calorimetry
        for i in list1:
            if i.GetClassName() == 'TDirectoryFile':
                myfile[inname].cd(i.GetName())
                list2 = gDirectory.GetListOfKeys()
                # Go to dataset directory
                for j in list2:
                    if j.GetClassName() == 'TDirectoryFile':
                        dataset = '%s'%j.GetName()
                        if dataset not in datasets:
                            datasets.append(dataset)
                        gDirectory.cd(dataset)
                        list3 = gDirectory.GetListOfKeys()
                        plot1d(dataset,'hno_flashes',inname,canno_flashes,legno_flashes,nplotsno_flashes,list3)
                        plot1d(dataset,'hflash_time',inname,canflash_time,legflash_time,nplotsflash_time,list3)
                        plot1d(dataset,'hflash_pe',inname,canflash_pe,legflash_pe,nplotsflash_pe,list3)
                        plot1d(dataset,'hflash_ycenter',inname,canflash_ycenter,legflash_ycenter,nplotsflash_ycenter,list3)
                        plot1d(dataset,'hflash_zcenter',inname,canflash_zcenter,legflash_zcenter,nplotsflash_zcenter,list3)

    if not os.path.exists('flash'):
    	os.makedirs('flash')
    os.chdir('flash')	
    savecanvas1d(datasets,canno_flashes,legno_flashes,'no_flashes')
    savecanvas1d(datasets,canflash_time,legflash_time,'flash_time')
    savecanvas1d(datasets,canflash_pe,legflash_pe,'flash_pe')
    savecanvas1d(datasets,canflash_ycenter,legflash_ycenter,'flash_ycenter')
    savecanvas1d(datasets,canflash_zcenter,legflash_zcenter,'flash_zcenter')

def main(argv):
    infile=''
    outdir= ''
    release=''
    calorimetry = 0
    hit = 0
    tracking = 0
    momresol = 0
    flash = 0
    pid = 0
    args = argv[1:]
    while len(args) > 0:
        if args[0] == '-h' or args[0] == '--help':
            help()
            return 0
        elif args[0] == '--input' and len(args) > 1:
            infile = args[1]
            del args[0:2]
	elif args[0] == '--dir':
	    outdir = args[1]   
	    del args[0:2] 
	elif args[0] == '--release':
	    release = args[1] 
	    del args[0:2]
        elif args[0] == '--calorimetry':
            calorimetry = 1
            del args[0]
        elif args[0] == '--hit':
            hit = 1
            del args[0]
	elif args[0] == '--tracking':
            tracking = 1
            del args[0]        
        elif args[0] == '--momresol':
            momresol = 1
            del args[0]
        elif args[0] == '--flash':
            flash = 1
            del args[0]
	elif args[0] == '--pid':
            pid = 1
            del args[0]
	elif args[0] == '-b':
            del args[0]
        else:
            print 'Unknown option %s' % args[0]
            return 1
	   
    if outdir == '':
    	 outdir = os.getcwd()
    
    if not os.path.exists(outdir):
    	os.makedirs(outdir)
    os.chdir(outdir)
   
    if calorimetry:
        if infile == '':
            print 'Please specify input file using --input.'
            return 1
        else:
            plotcalorimetry(infile)

    if hit:
        if infile == '':
            print 'Please specify input file using --input.'
            return 1
        else:
            plothit(infile)

    if flash:
        if infile == '':
            print 'Please specify input file using --input.'
            return 1
        else:
            plotflash(infile)
	    
    if tracking:
        if infile == '':
            print 'Please specify input file using --input.'
            return 1
        else:
            plottracking(infile)
	    
    if momresol:
        if infile == '':
            print 'Please specify input file using --input.'
            return 1
        else:
            plotmomresolution(infile)	    	    
    if pid:
        if infile == '':
            print 'Please specify input file using --input.'
            return 1
        else:
            plotpid(infile)
	    
    currdir = os.getcwd()
    if outdir != currdir:
    	os.chdir(currdir) 	    
	    	  
if __name__ == '__main__':
    rc = main(sys.argv)
    sys.exit(rc)
