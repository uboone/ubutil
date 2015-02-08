#!/usr/bin/env python
import sys
from ROOT import TFile, TCanvas, TH1F, TH2F, TProfile
from ROOT import gDirectory, gROOT
from validation_utilities import *

def plotcalorimetry(infile):
    # open the file
#    myfile = TFile(infile)
#    gDirectory.ls()
#    gDirectory.cd('calorimetry')
#    gDirectory.ls()
#    dirlist = myfile.GetListOfKeys()
#    for dir in dirlist:
#        print dir.GetName(),dir.GetClassName()
#        if dir.GetClassName() == 'TDirectoryFile':
#            gDirectory.cd(dir.GetName())
#            gDirectory.ls()
    trackers = []
    datasets = []
    muondEdxR = GetMuondEdxR()
    canvas = {}
    myfile = TFile(infile)
    list1 = myfile.GetListOfKeys()
    for i in list1:
        if i.GetClassName() == 'TDirectoryFile':
            myfile.cd(i.GetName())
            #print gDirectory.ls()
            list2 = gDirectory.GetListOfKeys()
            for j in list2:
                if j.GetClassName() == 'TDirectoryFile':
                    dataset = '%s'%j.GetName()
                    if dataset not in datasets:
                        datasets.append(dataset)
                    gDirectory.cd(dataset)
                    if (dataset not in canvas):
                        canvas[dataset] = canvas.get(dataset,{})
                        #gDirectory.ls()
                    list3 = gDirectory.GetListOfKeys()
                    if len(trackers) == 0:
                        for k in list3:
                            name = k.GetName()
                            match = re.search(r'_(\w+)$',name)
                            if match:
                                if match.group(1) not in trackers:
                                    trackers.append(match.group(1))
                    for t in trackers:
                        if t not in canvas[dataset]:
                            canvas[dataset][t] = TCanvas("can_"+dataset+t,"can_"+dataset+t,1000,800)
                            canvas[dataset][t].Divide(2,2)
                            for i in range(3):
                                canvas[dataset][t].cd(i+1)
                                for k in list3:
                                    if k.GetName()=='dedxrr%d_%s'%(i,t):
                                        k.ReadObj().Draw("colz")
                                for k in list3:
                                    if k.GetName()=='pdedxrr%d_%s'%(i,t):
                                        k.ReadObj().SetMarkerStyle(20)
                                        k.ReadObj().SetMarkerSize(0.3)
                                        k.ReadObj().Draw("same")
                                muondEdxR.SetMarkerStyle(20)
                                muondEdxR.SetMarkerSize(0.3)
                                muondEdxR.SetMarkerColor(800)
                                muondEdxR.SetLineColor(800)
                                muondEdxR.SetLineWidth(2)
                                muondEdxR.Draw("pc")

    for i in datasets:
        for j in trackers:
            canvas[i][j].Print('dedxrr_%s_%s.gif'%(i,j))
            canvas[i][j].Print('dedxrr_%s_%s.pdf'%(i,j))

                            
#                            print name
#                            l = name.rfind("_")
#                            tracker = name[k+1:]
#                            print tracker

def main(argv):

    infile=''
    calorimetry = 0
    args = argv[1:]
    while len(args) > 0:
        if args[0] == '--input' and len(args) > 1:
            infile = args[1]
            del args[0:2]
        elif args[0] == '--calorimetry':
            calorimetry = 1
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

if __name__ == '__main__':
    rc = main(sys.argv)
    sys.exit(rc)
