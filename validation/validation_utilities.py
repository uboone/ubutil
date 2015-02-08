
from ROOT import TGraph
import math
import re
from array import array

def GetTrackers(mychain):
    trackers = []
    list = mychain.GetListOfBranches()
    for i in range(len(list)):
        bname = list[i].GetName()
        match = re.search(r'ntracks_(\w+)',bname)
        if match:
            trackers.append(match.group(1))
    return trackers

def PointMatch(x0, y0, z0, x1, y1, z1, cut=10.):
    if math.sqrt(pow(x0-x1,2)+pow(y0-y1,2)+pow(z0-z1,2))<cut:
        return True
    else:
        return False

def Contained(x, y, z, cut = 10.):
    if (x > cut and x < 250 - cut 
        and y > -120 + cut and y < 120 - cut 
        and z > cut and z < 1040 - cut):
        return True
    else:
        return False

def GetMuondEdxR():
    rr, dedx = array('f'), array('f')
    rr.append(0.9833)
    rr.append(1.786)
    rr.append(3.321)
    rr.append(6.598)
    rr.append(10.58)
    rr.append(30.84)
    rr.append(42.50)
    rr.append(67.50)
    rr.append(106.3)
    rr.append(238.5)
    rr.append(493.4)
    rr.append(616.3)
    rr.append(855.2)
    rr.append(1202)
    rr.append(1758)

    dedx.append(5.687)
    dedx.append(4.461)
    dedx.append(3.502)
    dedx.append(2.731)
    dedx.append(2.340)
    dedx.append(1.771)
    dedx.append(1.670)
    dedx.append(1.570)
    dedx.append(1.519)
    dedx.append(1.510)
    dedx.append(1.526)
    dedx.append(1.610)
    dedx.append(1.645)
    dedx.append(1.700)
    dedx.append(1.761)
    dedx.append(1.829)
#    rr = [0.9833,1.786,3.321,6.598,10.58,30.84,42.50,67.32,106.3,172.5,238.5]
#    print len(rr)
#    dedx = [5.687,4.461,3.502,2.731,2.340,1.771,1.670,1.570,1.519,1.510,1.526]
    for i in range(len(rr)):
        rr[i]/=1.396
        dedx[i]*=1.396
    gr = TGraph(len(rr), rr, dedx)
    return gr

