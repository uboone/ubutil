
from ROOT import TFile, TCanvas, TH1F, TH2F
from ROOT import gDirectory
import math

def disdiff(x0,x1,y0,y1,z0,z1):
    return math.sqrt(pow(x0-x1,2)+pow(y0-y1,2)+pow(z0-z1,2))

def contained(x,y,z):
    if x > 10 and x < 240 and y > -110 and y < 110 and z > 10 and z < 1030:
        return True
    else:
        return False

# Create histograms
dedxrr = TH2F("dedxrr","dE/dx vs Residual Range",1000,0,1000,1000,0,20);

dedxrrFill = dedxrr.Fill

# open the file
myfile = TFile('/pnfs/uboone/scratch/users/tjyang/output/v03_06_00/ana/prod_muminus_0.1-2.0GeV_isotropic_modbox_uboone/anahist.root')
#myfile = TFile('anahist.root')

mychain = gDirectory.Get('analysistree/anatree')
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

    #print mychain.ntracks_trackkalmanhit
    for i in range(mychain.ntracks_trackkalmanhit):
        if (disdiff(mychain.trkstartx_trackkalmanhit[i], mychain.StartPointx[0],
                    mychain.trkstarty_trackkalmanhit[i], mychain.StartPointy[0],
                    mychain.trkstartz_trackkalmanhit[i], mychain.StartPointz[0])<10
            and disdiff(mychain.trkendx_trackkalmanhit[i], mychain.EndPointx[0],
                        mychain.trkendy_trackkalmanhit[i], mychain.EndPointy[0],
                        mychain.trkendz_trackkalmanhit[i], mychain.EndPointz[0])<10
            or disdiff(mychain.trkstartx_trackkalmanhit[i], mychain.EndPointx[0],
                       mychain.trkstarty_trackkalmanhit[i], mychain.EndPointy[0],
                       mychain.trkstartz_trackkalmanhit[i], mychain.EndPointz[0])<10
            and disdiff(mychain.trkendx_trackkalmanhit[i], mychain.StartPointx[0],
                        mychain.trkendy_trackkalmanhit[i], mychain.StartPointy[0],
                        mychain.trkendz_trackkalmanhit[i], mychain.StartPointz[0])<10):
            if (contained(mychain.trkstartx_trackkalmanhit[i],
                          mychain.trkstarty_trackkalmanhit[i],
                          mychain.trkstartz_trackkalmanhit[i])
                and contained(mychain.trkendx_trackkalmanhit[i],
                              mychain.trkendy_trackkalmanhit[i],
                              mychain.trkendz_trackkalmanhit[i])):
                for j in range(mychain.ntrkhits_trackkalmanhit[i*3+2]):
                    if (mychain.trkdedx_trackkalmanhit[i*3*1000+2*1000+j]>0):
                        dedxrrFill(mychain.trkresrg_trackkalmanhit[i*3*1000+2*1000+j],mychain.trkdedx_trackkalmanhit[i*3*1000+2*1000+j])

c1 = TCanvas( 'c1', 'c1', 800, 600)
dedxrr.Draw("colz")
