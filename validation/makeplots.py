#! /usr/bin/env python
###############################################################################
#
# Name: makeplots.py
# 
# Purpose: Make plots from root files and save them in gif and pdf formats
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
# --hit               - Make hitfinder validation plots
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

from ROOT import TFile, TCanvas, TH1F, TH2F, TProfile, TLegend
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
        leg[dataset] = TLegend(0.7,0.2,0.9,0.35)
        leg[dataset].SetFillStyle(0)
    can[dataset].cd()
    nplots[dataset] += 1
    hist = GetObject(hname+dataset,list)
    if hist:
        if nplots[dataset] == 1:
            hist.Draw()
        else:
            hist.SetLineColor(nplots[dataset])
            hist.Draw("sames")
            if hist.GetMaximum()*1.1>gPad.GetUymax():
                hist1 = gPad.GetListOfPrimitives()[0]
                hist1.GetYaxis().SetRangeUser(0,hist.GetMaximum()*1.1)
        leg[dataset].AddEntry(hist,inname,'l')

# Plot 1d histograms and make legends.
def plot1d3plane(dataset,hname,inname,can,leg,nplots,list):
    if dataset not in can:
        nplots[dataset] = 0
        can[dataset] = TCanvas('can'+hname+dataset,'can'+hname+dataset,1000,800)
        can[dataset].Divide(2,2)
        leg[dataset] = TLegend(0.7,0.2,0.9,0.35)
        leg[dataset].SetFillStyle(0)
    can[dataset].cd()
    nplots[dataset] += 1
    for i in range(3):
        can[dataset].cd(i+1)
        hist = GetObject(hname+str(i)+dataset,list)
        if hist:
            if nplots[dataset] == 1:
                hist.Draw()
            else:
                hist.SetLineColor(nplots[dataset])
                hist.Draw("sames")
                hist1 = gPad.GetListOfPrimitives()[0]
                if hist.GetMaximum()>hist1.GetMaximum():
                    hist1.GetYaxis().SetRangeUser(0,hist.GetMaximum()*1.2)
            if i==0:
                leg[dataset].AddEntry(hist,inname,'l')


def savecanvas1d(datasets,can,leg,hname):
    for i in datasets:
        can[i].cd()
        leg[i].Draw()
        SortOutStats(gPad,0.2,0.25,0.9,0.9)
        can[i].Print(hname+'_%s.gif'%i)
        can[i].Print(hname+'_%s.pdf'%i)
    
def savecanvas1d3plane(datasets,can,leg,hname):
    for i in datasets:
        for j in range(3):
            can[i].cd(j+1)
            leg[i].Draw()
            SortOutStats(gPad,0.2,0.25,0.9,0.9)
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
    candedxrr = {}
    candedx = {}
    nplotsdedx = {}
    legdedx = {}
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
                                tracker = name[name.rfind("_")+1:]
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
                                    dedxrr = GetObject('dedxrr%s_%d_%s'%(dataset,i,t), list3)
                                    if dedxrr:
                                        dedxrr.Draw("colz")
                                    pdedxrr = GetObject('pdedxrr%s_%d_%s'%(dataset,i,t), list3)
                                    if pdedxrr:
                                        pdedxrr.SetMarkerStyle(20)
                                        pdedxrr.SetMarkerSize(0.03)
                                        pdedxrr.Draw("same")
                                    muondEdxR.SetMarkerStyle(20)
                                    muondEdxR.SetMarkerSize(0.3)
                                    muondEdxR.SetMarkerColor(800)
                                    muondEdxR.SetLineColor(800)
                                    muondEdxR.SetLineWidth(2)
                                    muondEdxR.Draw("pc")
                            # dE/dx plots.
                            if dataset+t not in candedx:
                                nplotsdedx[dataset+t] = 0
                                candedx[dataset+t] = TCanvas("candedx_"+dataset+t,"candedx_"+dataset+t,1000,800)
                                candedx[dataset+t].Divide(2,2)
                                legdedx[dataset+t] = TLegend(0.35,0.6,0.6,0.9)
                            nplotsdedx[dataset+t] += 1
                            # plot all 3 planes
                            for i in range(3):
                                candedx[dataset+t].cd(i+1)
                                dedx = GetObject('dedx%s_%d_%s'%(dataset,i,t), list3)
                                if dedx:
                                    if nplotsdedx[dataset+t] == 1:
                                        dedx.Draw()
                                    else:
                                        dedx.SetLineColor(nplotsdedx[dataset+t])
                                        dedx.Draw("sames")
                                        # if new histogram is too high, adjust y range
                                        if dedx.GetMaximum()*1.1>gPad.GetUymax():
                                            hist = gPad.GetListOfPrimitives()[0]
                                            hist.GetYaxis().SetRangeUser(0,dedx.GetMaximum()*1.1)
                                    if i==0:
                                        legdedx[dataset+t].AddEntry(dedx,inname,'l')

    #Save dE/dx vs Residula Range plots.
    for i in innames:
        for j in datasets:
            for k in trackers:
                if i+j+k in candedxrr:
                    candedxrr[i+j+k].cd()
                    candedxrr[i+j+k].Update()
                    candedxrr[i+j+k].Print('dedxrr_%s_%s_%s.gif'%(i,j,k))
                    candedxrr[i+j+k].Print('dedxrr_%s_%s_%s.pdf'%(i,j,k))

    #Save dE/dx plots.
    for i in datasets:
        for j in trackers:
            if i+j in candedx:
                for k in range(3):
                    candedx[i+j].cd(k+1)
                    legdedx[i+j].Draw()
                    SortOutStats(gPad,0.3,0.25,0.9,0.9)
                candedx[i+j].Print('dedx_%s_%s.gif'%(i,j))
                candedx[i+j].Print('dedx_%s_%s.pdf'%(i,j))

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
                        plot1d(dataset,'hno_hits',inname,canno_hits,legno_hits,nplotsno_hits,list3)
                        plot1d(dataset,'hhit_plane',inname,canhit_plane,leghit_plane,nplotshit_plane,list3)
                        plot1d(dataset,'hhit_wire',inname,canhit_wire,leghit_wire,nplotshit_wire,list3)
                        plot1d(dataset,'hhit_channel',inname,canhit_channel,leghit_channel,nplotshit_channel,list3)
                        plot1d(dataset,'hhit_peakT',inname,canhit_peakT,leghit_peakT,nplotshit_peakT,list3)
                        plot1d3plane(dataset,'hhit_charge',inname,canhit_charge,leghit_charge,nplotshit_charge,list3)
                        plot1d3plane(dataset,'hhit_ph',inname,canhit_ph,leghit_ph,nplotshit_ph,list3)
                        plot1d3plane(dataset,'hphperelec',inname,canphperelec,legphperelec,nplotsphperelec,list3)
                        plot1d3plane(dataset,'hchargeperelec',inname,canchargeperelec,legchargeperelec,nplotschargeperelec,list3)

    savecanvas1d(datasets,canno_hits,legno_hits,'no_hits')
    savecanvas1d(datasets,canhit_plane,leghit_plane,'hit_plane')
    savecanvas1d(datasets,canhit_wire,leghit_wire,'hit_wire')
    savecanvas1d(datasets,canhit_channel,leghit_channel,'hit_channel')
    savecanvas1d(datasets,canhit_peakT,leghit_peakT,'hit_peakT')
    savecanvas1d3plane(datasets,canhit_charge,leghit_charge,'hit_charge')
    savecanvas1d3plane(datasets,canhit_ph,leghit_ph,'hit_ph')
    savecanvas1d3plane(datasets,canphperelec,legphperelec,'phperelec')
    savecanvas1d3plane(datasets,canchargeperelec,legchargeperelec,'chargeperelec')

def main(argv):

    infile=''
    calorimetry = 0
    hit = 0
    args = argv[1:]
    while len(args) > 0:
        if args[0] == '-h' or args[0] == '--help':
            help()
            return 0
        elif args[0] == '--input' and len(args) > 1:
            infile = args[1]
            del args[0:2]
        elif args[0] == '--calorimetry':
            calorimetry = 1
            del args[0]
        elif args[0] == '--hit':
            hit = 1
            del args[0]
        elif args[0] == '-b':
            del args[0]
        else:
            print 'Unknown option %s' % args[0]
            return 1

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

if __name__ == '__main__':
    rc = main(sys.argv)
    sys.exit(rc)
