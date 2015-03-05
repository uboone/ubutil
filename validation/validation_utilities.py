
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
    rr.append(172.5)
    rr.append(238.5)
    rr.append(493.4)
    rr.append(616.3)
    rr.append(855.2)
    rr.append(1202)

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

def GetMuonKELen():
    ke, length = array('f'), array('f')
    length.append(0.9833)
    length.append(1.786)
    length.append(3.321)
    length.append(6.598)
    length.append(10.58)
    length.append(30.84)
    length.append(42.50)
    length.append(67.50)
    length.append(106.3)
    length.append(172.5)
    length.append(238.5)
    length.append(493.4)
    length.append(616.3)
    length.append(855.2)
    length.append(1202)
    
    ke.append(10)
    ke.append(14)
    ke.append(20)
    ke.append(30)
    ke.append(40)
    ke.append(80)
    ke.append(100)
    ke.append(140)
    ke.append(200)
    ke.append(300)
    ke.append(400)
    ke.append(800)
    ke.append(1000)
    ke.append(1400)
    ke.append(2000)

    for i in range(len(length)):
        length[i]/=1.396
    gr = TGraph(len(length), length, ke)
    return gr

def GetProtonKELen():
    ke, length = array('f'), array('f')
    length.append(1.887E-1)
    length.append(3.823E-1)
    length.append(6.335E-1)
    length.append(1.296)
    length.append(2.159)
    length.append(7.375)
    length.append(1.092E1)
    length.append(2.215E1)
    length.append(3.627E1)
    length.append(5.282E1)
    length.append(7.144E1)
    length.append(9.184E1)
    length.append(1.138E2)
    length.append(1.370E2)
    length.append(1.614E2)
    length.append(1.869E2)
    length.append(2.132E2)
    length.append(2.403E2)
    length.append(2.681E2)
    length.append(2.965E2)
    length.append(3.254E2)
    length.append(3.548E2)
    length.append(3.846E2)
    length.append(4.148E2)
    length.append(4.454E2)
    length.append(7.626E2)
    length.append(1.090E3)
    length.append(1.418E3)
    length.append(1.745E3)
    length.append(2.391E3)
    length.append(3.022E3)

    ke.append(10) 
    ke.append(15) 
    ke.append(20) 
    ke.append(30) 
    ke.append(40) 
    ke.append(80) 
    ke.append(100) 
    ke.append(150) 
    ke.append(200) 
    ke.append(250) 
    ke.append(300) 
    ke.append(350) 
    ke.append(400) 
    ke.append(450) 
    ke.append(500) 
    ke.append(550) 
    ke.append(600) 
    ke.append(650) 
    ke.append(700) 
    ke.append(750) 
    ke.append(800) 
    ke.append(850) 
    ke.append(900) 
    ke.append(950) 
    ke.append(1000)
    ke.append(1500) 
    ke.append(2000) 
    ke.append(2500) 
    ke.append(3000) 
    ke.append(4000) 
    ke.append(5000)

    for i in range(len(length)):
        length[i]/=1.396
    gr = TGraph(len(length), length, ke)
    return gr
