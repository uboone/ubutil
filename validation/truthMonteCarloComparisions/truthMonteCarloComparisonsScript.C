#include <iostream>
#include <fstream>
#include <string>
#include <algorithm>
#include <cassert>
#include "TH1.h"
#include "TTree.h"
#include "TFile.h"
#include "TCanvas.h"
#include "TLegend.h"
#include "TMath.h"
using namespace std;
   
float FVx = 256.35; //AV dimensions
float FVy = 233; //AV dimensions
float FVz = 1036.8; //AV dimensions
float borderx = 10.; //cut
float bordery = 20.; //cut
float borderz = 10.; //cut

int chisqNotifierCut = 9999999;

//This function returns if a 3D point is within the fiducial volume
bool inFV(Double_t x, Double_t y, Double_t z) {
	if(x < (FVx - borderx) && (x > borderx) && (y < (FVy/2. - bordery)) && (y > (-FVy/2. + bordery)) && (z < (FVz - borderz)) && (z > borderz)) return true;
	else return false;
}



// ------- Function to generate efficiency histograms from reco/true histograms -------- //

TH1D* effcalc(TH1D* hreco, TH1D* htrue, TString label){
  // Check that reco and true histograms have the same binning (well - same number of bins...)
  assert(hreco->GetNbinsX() == htrue->GetNbinsX());

  // Make a new histogram to store efficiencies
  TH1D *heff = (TH1D*)(hreco->Clone());
  heff->Reset();
  heff->SetTitle(label);
  std::string heffname = std::string("heff");
  heffname += std::string(std::string(heff->GetName()).substr(5, string(heff->GetName()).size()).c_str());
  heff->SetName(heffname.c_str());

  // Loop over all bins, including underflow and overflow
  // Set bin in efficiency histogram to be reco/true
  for (int ibin=0; ibin<hreco->GetNbinsX(); ibin++){
    float reco_bc = hreco->GetBinContent(ibin);
    float true_bc = htrue->GetBinContent(ibin);

    // Don't divide by zero!
    if (true_bc == 0){
      heff->SetBinContent(ibin, 0.);
      heff->SetBinError(ibin, 0.);
    }
    else {
      float eff_bc = reco_bc/true_bc;
      if (eff_bc < 0){ eff_bc = 0; }
      if (eff_bc > 1){ eff_bc = 1; }

      float err = TMath::Sqrt(eff_bc * (1.-eff_bc)/true_bc);
      
      heff->SetBinContent(ibin, eff_bc);
      heff->SetBinError(ibin, err);
    }
  }
  heff->SetMinimum(0.);
  heff->SetMaximum(1.05);
  heff->SetMarkerStyle(20);

  return heff;
}





// ------- Function to make all of the plots -------- //

void FillPlots_MC( TTree* tree, std::vector<TH1D> &hvector, std::string tracking_algorithm, std::string version, std::string short_long ) {

   const int kMaxTracks = 5000;
   Short_t         ntracks;
   Float_t         trkstartx[kMaxTracks];
   Float_t         trkendx[kMaxTracks];
   Float_t         trkstarty[kMaxTracks];
   Float_t         trkendy[kMaxTracks];
   Float_t         trkstartz[kMaxTracks];
   Float_t         trkendz[kMaxTracks];
   Float_t         trklength[kMaxTracks];
   Int_t 	   trkg4id[kMaxTracks];
   Float_t         trkmomrange[kMaxTracks];
   Float_t         trkmcsfwdmom[kMaxTracks];
   Float_t         trkmcsbwdmom[kMaxTracks];
   Float_t	   trkpidpida[kMaxTracks][3];
   Short_t         trkpidbestplane[kMaxTracks];

   const int kMaxVertices = 100;
   Short_t         nnuvtx;
   Float_t         nuvtxx[kMaxVertices];
   Float_t         nuvtxy[kMaxVertices];
   Float_t         nuvtxz[kMaxVertices];

   const int kMaxGeant = 10000;
   Int_t           geant_list_size;
   Float_t         StartX[kMaxGeant];
   Float_t         StartY[kMaxGeant];
   Float_t         StartZ[kMaxGeant];
   Float_t         EndX[kMaxGeant];
   Float_t         EndY[kMaxGeant];
   Float_t         EndZ[kMaxGeant];
   Float_t         real_StartX[kMaxGeant];
   Float_t         real_StartX_nosc[kMaxGeant];
   Float_t         real_StartY[kMaxGeant];
   Float_t         real_StartZ[kMaxGeant];
   Float_t         real_EndX[kMaxGeant];
   Float_t         real_EndY[kMaxGeant];
   Float_t         real_EndZ[kMaxGeant];
   Float_t         pathlen[kMaxGeant];
   Int_t           origin[kMaxGeant];
   Int_t           pdg[kMaxGeant];
   Int_t           TrackId[kMaxGeant];
   Int_t           status[kMaxGeant];
   Int_t           Mother[kMaxGeant];
   Float_t         P[kMaxGeant];
   Float_t         Px[kMaxGeant];
   Float_t         Py[kMaxGeant];
   Float_t         Pz[kMaxGeant];
   Float_t         theta[kMaxGeant];
   Float_t         theta_xz[kMaxGeant];
   Float_t         theta_yz[kMaxGeant];
   Float_t         phi[kMaxGeant];

   const int maxtruth = 10;
   Int_t           mcevts_truth;               //number of neutrino interactions in the spill
   Float_t         nuvtxx_truth[maxtruth];    //neutrino vertex x in cm
   Float_t         nuvtxy_truth[maxtruth];    //neutrino vertex y in cm
   Float_t         nuvtxz_truth[maxtruth];    //neutrino vertex z in cm

   const int maxgenie = 70;
   Int_t           genie_no_primaries; 
   Int_t           genie_primaries_pdg[maxgenie];
   Int_t           genie_status_code[maxgenie];

   // Initialise only the branches we want (makes it run faster)
   // and set branch addresses
   tree -> SetBranchStatus("*",0);
   std::string branch_name = "ntracks_" + tracking_algorithm;
   tree -> SetBranchStatus(branch_name.c_str(),1);
   tree -> SetBranchAddress(branch_name.c_str(), &ntracks);
   branch_name = "trkstartx_" + tracking_algorithm;
   tree -> SetBranchStatus(branch_name.c_str(),1);
   tree -> SetBranchAddress(branch_name.c_str(), trkstartx);
   branch_name = "trkendx_" + tracking_algorithm;
   tree -> SetBranchStatus(branch_name.c_str(),1);
   tree -> SetBranchAddress(branch_name.c_str(), trkendx);
   branch_name = "trkstarty_" + tracking_algorithm;
   tree -> SetBranchStatus(branch_name.c_str(),1);
   tree -> SetBranchAddress(branch_name.c_str(), trkstarty);
   branch_name = "trkendy_" + tracking_algorithm;
   tree -> SetBranchStatus(branch_name.c_str(),1);
   tree -> SetBranchAddress(branch_name.c_str(), trkendy);
   branch_name = "trkstartz_" + tracking_algorithm;
   tree -> SetBranchStatus(branch_name.c_str(),1);
   tree -> SetBranchAddress(branch_name.c_str(), trkstartz);
   branch_name = "trkendz_" + tracking_algorithm;
   tree -> SetBranchStatus(branch_name.c_str(),1);
   tree -> SetBranchAddress(branch_name.c_str(), trkendz);
   branch_name = "trklen_" + tracking_algorithm;
   tree -> SetBranchStatus(branch_name.c_str(),1);
   tree -> SetBranchAddress(branch_name.c_str(), trklength);
   branch_name = "trkg4id_" + tracking_algorithm;
   tree -> SetBranchStatus(branch_name.c_str(),1);
   tree -> SetBranchAddress(branch_name.c_str(), trkg4id);
   branch_name = "trkmomrange_" + tracking_algorithm;
   tree -> SetBranchStatus(branch_name.c_str(),1);
   tree -> SetBranchAddress(branch_name.c_str(), trkmomrange);
   branch_name = "trkmcsfwdmom_" + tracking_algorithm;
   tree -> SetBranchStatus(branch_name.c_str(),1);
   tree -> SetBranchAddress(branch_name.c_str(), trkmcsfwdmom);
   branch_name = "trkmcsbwdmom_" + tracking_algorithm;
   tree -> SetBranchStatus(branch_name.c_str(),1);
   tree -> SetBranchAddress(branch_name.c_str(), trkmcsbwdmom);
   branch_name = "trkpidpida_" + tracking_algorithm;
   tree -> SetBranchStatus(branch_name.c_str(),1);
   tree -> SetBranchAddress(branch_name.c_str(), trkpidpida);
   branch_name = "trkpidbestplane_" + tracking_algorithm;
   tree -> SetBranchStatus(branch_name.c_str(),1);
   tree -> SetBranchAddress(branch_name.c_str(), trkpidbestplane);
   
   tree -> SetBranchStatus("geant_list_size",1);
   tree -> SetBranchAddress("geant_list_size", &geant_list_size);
   tree -> SetBranchStatus("TrackId",1);
   tree -> SetBranchAddress("TrackId", TrackId);
   // Don't use space charge correction for MCC 8
   // Note: this is only really true if you're looking at BNB
   // For cosmics you will want to edit this to use space charge correction
   if((string(version).find("MCC8") != std::string::npos) || (string(version).find("mcc8") != std::string::npos) || (string(version).find("v06_26") != std::string::npos)){
     tree -> SetBranchStatus("StartPointx_tpcAV",1);
     tree -> SetBranchAddress("StartPointx_tpcAV", StartX);
     tree -> SetBranchStatus("StartPointy_tpcAV",1);
     tree -> SetBranchAddress("StartPointy_tpcAV", StartY);
     tree -> SetBranchStatus("StartPointz_tpcAV",1);
     tree -> SetBranchAddress("StartPointz_tpcAV", StartZ);
     tree -> SetBranchStatus("EndPointx_tpcAV",1);
     tree -> SetBranchAddress("EndPointx_tpcAV", EndX);
     tree -> SetBranchStatus("EndPointy_tpcAV",1);
     tree -> SetBranchAddress("EndPointy_tpcAV", EndY);
     tree -> SetBranchStatus("EndPointz_tpcAV",1);
     tree -> SetBranchAddress("EndPointz_tpcAV", EndZ);
     tree -> SetBranchStatus("StartPointx",1);
     tree -> SetBranchAddress("StartPointx", real_StartX);
     tree -> SetBranchStatus("StartPointy",1);
     tree -> SetBranchAddress("StartPointy", real_StartY);
     tree -> SetBranchStatus("StartPointz",1);
     tree -> SetBranchAddress("StartPointz", real_StartZ);
     tree -> SetBranchStatus("EndPointx",1);
     tree -> SetBranchAddress("EndPointx", real_EndX);
     tree -> SetBranchStatus("EndPointy",1);
     tree -> SetBranchAddress("EndPointy", real_EndY);
     tree -> SetBranchStatus("EndPointz",1);
     tree -> SetBranchAddress("EndPointz", real_EndZ);
     tree -> SetBranchStatus("nuvtx*",1);
     tree -> SetBranchAddress("nuvtxx_truth", nuvtxx_truth);
     tree -> SetBranchAddress("nuvtxy_truth", nuvtxy_truth);
     tree -> SetBranchAddress("nuvtxz_truth", nuvtxz_truth);
     branch_name = "nnuvtx_" + tracking_algorithm;
     tree -> SetBranchStatus(branch_name.c_str(),1);
     tree -> SetBranchAddress(branch_name.c_str(), &nnuvtx);
     branch_name = "nuvtxx_" + tracking_algorithm;
     tree -> SetBranchStatus(branch_name.c_str(),1);
     tree -> SetBranchAddress(branch_name.c_str(), &nuvtxx);
     branch_name = "nuvtxy_" + tracking_algorithm;
     tree -> SetBranchStatus(branch_name.c_str(),1);
     tree -> SetBranchAddress(branch_name.c_str(), &nuvtxy);
     branch_name = "nuvtxz_" + tracking_algorithm;
     tree -> SetBranchStatus(branch_name.c_str(),1);
     tree -> SetBranchAddress(branch_name.c_str(), &nuvtxz);
   } else {
     std::cout << "Using space charge correction for start/end points and vertices" << std::endl;
     tree -> SetBranchStatus("sp_charge_corrected*",1);
     tree -> SetBranchAddress("sp_charge_corrected_StartPointx_tpcAV", StartX);
     tree -> SetBranchAddress("sp_charge_corrected_StartPointy_tpcAV", StartY);
     tree -> SetBranchAddress("sp_charge_corrected_StartPointz_tpcAV", StartZ);
     tree -> SetBranchAddress("sp_charge_corrected_EndPointx_tpcAV", EndX);
     tree -> SetBranchAddress("sp_charge_corrected_EndPointy_tpcAV", EndY);
     tree -> SetBranchAddress("sp_charge_corrected_EndPointz_tpcAV", EndZ);
     tree -> SetBranchAddress("sp_charge_corrected_StartPointx", real_StartX);
     tree -> SetBranchAddress("sp_charge_corrected_StartPointy", real_StartY);
     tree -> SetBranchAddress("sp_charge_corrected_StartPointz", real_StartZ);
     tree -> SetBranchAddress("sp_charge_corrected_EndPointx", real_EndX);
     tree -> SetBranchAddress("sp_charge_corrected_EndPointy", real_EndY);
     tree -> SetBranchAddress("sp_charge_corrected_EndPointz", real_EndZ);
     tree -> SetBranchAddress("sp_charge_corrected_nuvtxx_truth", nuvtxx_truth);
     tree -> SetBranchAddress("sp_charge_corrected_nuvtxy_truth", nuvtxy_truth);
     tree -> SetBranchAddress("sp_charge_corrected_nuvtxz_truth", nuvtxz_truth);
     branch_name = "nnuvtx_" + tracking_algorithm;
     tree -> SetBranchStatus(branch_name.c_str(),1);
     tree -> SetBranchAddress(branch_name.c_str(), &nnuvtx);
     branch_name = "nuvtxx_" + tracking_algorithm;
     tree -> SetBranchStatus(branch_name.c_str(),1);
     tree -> SetBranchAddress(branch_name.c_str(), &nuvtxx);
     branch_name = "nuvtxy_" + tracking_algorithm;
     tree -> SetBranchStatus(branch_name.c_str(),1);
     tree -> SetBranchAddress(branch_name.c_str(), &nuvtxy);
     branch_name = "nuvtxz_" + tracking_algorithm;
     tree -> SetBranchStatus(branch_name.c_str(),1);
     tree -> SetBranchAddress(branch_name.c_str(), &nuvtxz);
     }
   tree -> SetBranchStatus("mcevts_truth",1);
   tree -> SetBranchAddress("mcevts_truth", &mcevts_truth);
   tree -> SetBranchStatus("origin",1);
   tree -> SetBranchAddress("origin", origin);
   tree -> SetBranchStatus("pdg",1);
   tree -> SetBranchAddress("pdg", pdg);
   tree -> SetBranchStatus("pathlen_drifted",1);
   tree -> SetBranchAddress("pathlen_drifted", pathlen);
   tree -> SetBranchStatus("P",1);
   tree -> SetBranchAddress("P", P);
   //tree -> SetBranchStatus("Px",1);
   //tree -> SetBranchAddress("Px", Px);
   //tree -> SetBranchStatus("Py",1);
   //tree -> SetBranchAddress("Py", Py);
   //tree -> SetBranchStatus("Pz",1);
   //tree -> SetBranchAddress("Pz", Pz);
   tree -> SetBranchStatus("status",1);
   tree -> SetBranchAddress("status", status);
   tree -> SetBranchStatus("Mother",1);
   tree -> SetBranchAddress("Mother", Mother);
   tree -> SetBranchStatus("genie_no_primaries",1);
   tree -> SetBranchAddress("genie_no_primaries", &genie_no_primaries); 
   tree -> SetBranchStatus("genie_primaries_pdg",1);
   tree -> SetBranchAddress("genie_primaries_pdg", genie_primaries_pdg);
   tree -> SetBranchStatus("genie_status_code",1);
   tree -> SetBranchAddress("genie_status_code", genie_status_code);
   tree -> SetBranchStatus("theta",1);
   tree -> SetBranchAddress("theta", &theta);
   tree -> SetBranchStatus("phi",1);
   tree -> SetBranchAddress("phi", &phi);
   tree -> SetBranchStatus("theta_xz",1);
   tree -> SetBranchAddress("theta_xz", &theta_xz);
   tree -> SetBranchStatus("theta_yz",1);
   tree -> SetBranchAddress("theta_yz", &theta_yz);

   long Size = tree -> GetEntries();
   cout << "Number of events in the tree is: " << Size << endl;

   std::string histoname = "hnreco_" + version;
   TH1D *hnreco = new TH1D(histoname.c_str(), "Number of reco tracks; Number of reco tracks;", 30, 0, 30);
   histoname = "hntrue_" + version;
   TH1D *hntrue = new TH1D(histoname.c_str(), "Number of true primary tracks per event; # True tracks;", 50, 0, 50);
   histoname = "hstartx_" + version;
   TH1D *hstartx = new TH1D(histoname.c_str(), "Track start X position; x [cm];", 100, -200, 500);
   histoname = "hstarty_" + version;
   TH1D *hstarty = new TH1D(histoname.c_str(), "Track start Y position; y [cm];", 100, -150, 150);
   histoname = "hstartz_" + version;
   TH1D *hstartz = new TH1D(histoname.c_str(), "Track start Z position; z [cm];", 100, -500, 1500);
   histoname = "hendx_" + version;
   TH1D *hendx = new TH1D(histoname.c_str(), "Track end X position; x [cm];", 100, -200, 500);
   histoname = "hendy_" + version;
   TH1D *hendy = new TH1D(histoname.c_str(), "Track end Y position; y [cm];", 100, -150, 150);
   histoname = "hendz_" + version;
   TH1D *hendz = new TH1D(histoname.c_str(), "Track end Z position; z [cm];", 100, -500, 1500);
   histoname = "hlreco_" + version;
   TH1D *hlreco = new TH1D(histoname.c_str(), "Track length Reco; Track length [cm];", 100, 0, 1000);
   histoname = "hlrange_" + version;
   TH1D *hlrange = new TH1D(histoname.c_str(), "Track length Range (start point - end point); Track range [cm];", 100, 0, 1000);
   histoname = "hlmc_" + version;
   TH1D *hlmc = new TH1D(histoname.c_str(), "Track length True; Track length [cm];", 100, 0, 1000);
   histoname = "hlrangemc_" + version;
   TH1D *hlrangemc = new TH1D(histoname.c_str(), "Track length Range True (start point - end point); Track range [cm];", 100, 0, 1000);
   histoname = "hldiff_" + version;
   TH1D *hldiff = new TH1D(histoname.c_str(), "Track length - Track range (Reco); Track length - track range [cm];", 200, -100, 100);
   histoname = "hldiffmc_" + version;
   TH1D *hldiffmc = new TH1D(histoname.c_str(), "Track length - Track range (True); Track length - track range [cm];", 200, -100, 100);
   histoname = "hlres_" + version;
   TH1D *hlres = new TH1D(histoname.c_str(), "Track length (Reco) - Track length (True); Track length reco - track length true  [cm];", 100, -50, 50);
   histoname = "hlresrange_" + version;
   TH1D *hlresrange = new TH1D(histoname.c_str(), "Track length range (Reco) - track length range (True); Track range reco - track range true [cm];", 100, -50, 50);
   histoname = "hresstart_" + version;
   TH1D *hresstart = new TH1D(histoname.c_str(), "Track start resolution; abs(Track start position (reco) - track start position (true)) [cm];", 50, 0, 50);
   histoname = "hresend_" + version;
   TH1D *hresend = new TH1D(histoname.c_str(), "Track end resolution; abs(Track end position (reco) - track end position (true)) [cm];", 50, 0, 50);
   histoname = "hresostartx_" + version;
   TH1D *hresostartx = new TH1D(histoname.c_str(),"Track start resolution (x); Track start x-position (reco) - Track start x-position (true) [cm];", 2000, -20, 20); 
   histoname = "hresostarty_" + version;
   TH1D *hresostarty = new TH1D(histoname.c_str(),"Track start resolution (y); Track start y-position (reco) - Track start y-position (true) R [cm];", 2000, -20, 20); 
   histoname = "hresostartz_" + version;
   TH1D *hresostartz = new TH1D(histoname.c_str(),"Track start resolution (z); Track start z-position (reco) - Track start z-position (true) [cm];", 2000, -20, 20); 
   histoname = "hresoendx_" + version;
   TH1D *hresoendx = new TH1D(histoname.c_str(),"Track end resolution (x); Track end x-position (reco) - Track end x-position (true) [cm];", 2000, -20, 20); 
   histoname = "hresoendy_" + version;
   TH1D *hresoendy = new TH1D(histoname.c_str(),"Track end resolution (y); Track end y-position (reco) - Track end y-position (true) [cm];", 2000, -20, 20); 
   histoname = "hresoendz_" + version;
   TH1D *hresoendz = new TH1D(histoname.c_str(),"Track end resolution (z); Track end z-position (reco) - Track end z-position (true) [cm];", 2000, -20, 20); 
   histoname = "hresomomentum_range_" + version;
   TH1D *hresomom_range = new TH1D(histoname.c_str(),"Momentum from range - momentum from MC; #Delta P [GeV/c];", 2000, -1, 1); 
   histoname = "hresomomentum_MCSfwd_" + version;
   TH1D *hresomom_MCSfwd = new TH1D(histoname.c_str(),"Momentum from MCS forward-going track - momentum from MC; #Delta P [GeV/c];", 2000, -2, 2); 
   histoname = "hresomomentum_llhd_" + version;
   TH1D *hresomom_MCSbwd = new TH1D(histoname.c_str(),"Momentum from MCS backward-going track - momentum from MC; #Delta P [GeV/c];", 2000, -2, 2); 
   histoname = "hresomomentum_contained_chi2_" + version;
   TH1D *hresomom_contained_MCSfwd = new TH1D(histoname.c_str(),"Momentum from MCS forward-going track - momentum from MC for contained tracks; #Delta P [GeV/c];", 2000, -2, 2); 
   histoname = "hresomomentum__contained_llhd_" + version;
   TH1D *hresomom_contained_MCSbwd = new TH1D(histoname.c_str(),"Momentum from MCS backward-going track - momentum from MC for contained tracks; #Delta P [GeV/c];", 2000, -2, 2); 
   histoname = "hpidpida_total_" + version;
   TH1D *hpidpida_total = new TH1D(histoname.c_str(),"PIDA for all reco tracks; PIDA;", 100, 0, 30); 
   histoname = "hpidpida_muon_" + version;
   TH1D *hpidpida_muon = new TH1D(histoname.c_str(),"PIDA for all reco muons; PIDA;", 100, 0, 30);  
   histoname = "hvertres_" + version;
   TH1D *hvertres = new TH1D(histoname.c_str(),"Vertex resolution; abs(Vertex position - true vertex) (cm);", 20, 0, 10); 
   histoname = "hvertresx_" + version;
   TH1D *hvertresx = new TH1D(histoname.c_str(),"Vertex resolution in x; Vertex position - true vertex in x (cm);", 200, -10, 10); 
   histoname = "hvertresy_" + version;
   TH1D *hvertresy = new TH1D(histoname.c_str(),"Vertex resolution in y; Vertex position - true verted in y (cm);", 200, -10, 10); 
   histoname = "hvertresz_" + version;
   TH1D *hvertresz = new TH1D(histoname.c_str(),"Vertex resolution in z; Vertex position - true verted in z (cm);", 200, -10, 10); 
   histoname = "htrkstart_" + version;
   TH1D *hvertdist = new TH1D(histoname.c_str(),"Closest track start to reco vertex; Closest track start (cm);", 100, 0, 20); 
   histoname = "hnprotons_" + version;
   TH1D *hnprotons = new TH1D(histoname.c_str(),"Proton multiplicity; Number of protons;", 7, -0.5, 6.5); 

   // Define track efficiency truth histograms
   histoname = "htrue_mclen_" + version;
   TH1D *htrue_mclen = new TH1D(histoname.c_str(),"True Length", 60, 0, 1200);
   histoname = "htrue_mcpdg_" + version;
   TH1D *htrue_mcpdg = new TH1D(histoname.c_str(),"True PDG", 20, 0, 5000);
   histoname = "htrue_mctheta_" + version;
   TH1D *htrue_mctheta = new TH1D(histoname.c_str(),"True Theta", 20, 0, 180);
   histoname = "htrue_mcphi_" + version;
   TH1D *htrue_mcphi = new TH1D(histoname.c_str(),"True Phi", 20, -180, 180);
   histoname = "htrue_mcthetaxz_" + version;
   TH1D *htrue_mcthetaxz = new TH1D(histoname.c_str(),"True ThetaXZ", 20, -180, 180);
   histoname = "htrue_mcthetayz_" + version;
   TH1D *htrue_mcthetayz = new TH1D(histoname.c_str(),"True ThetaYZ", 20, -180, 180);
   histoname = "htrue_mcmom_" + version;
   TH1D *htrue_mcmom = new TH1D(histoname.c_str(),"True Momentum", 20, 0, 2.2);

   // Define track efficiency reco histograms
   histoname = "hreco_mclen_" + version;
   TH1D *hreco_mclen = new TH1D(histoname.c_str(),"Reco Length", 60, 0, 1200);
   histoname = "hreco_mcpdg_" + version;
   TH1D *hreco_mcpdg = new TH1D(histoname.c_str(),"Reco PDG", 20, 0, 5000);
   histoname = "hreco_mctheta_" + version;
   TH1D *hreco_mctheta = new TH1D(histoname.c_str(),"Reco Theta", 20, 0, 180);
   histoname = "hreco_mcphi_" + version;
   TH1D *hreco_mcphi = new TH1D(histoname.c_str(),"Reco Phi", 20, -180, 180);
   histoname = "hreco_mcthetaxz_" + version;
   TH1D *hreco_mcthetaxz = new TH1D(histoname.c_str(),"Reco ThetaXZ", 20, -180, 180);
   histoname = "hreco_mcthetayz_" + version;
   TH1D *hreco_mcthetayz = new TH1D(histoname.c_str(),"Reco ThetaYZ", 20, -180, 180);
   histoname = "hreco_mcmom_" + version;
   TH1D *hreco_mcmom = new TH1D(histoname.c_str(),"Reco Momentum", 20, 0, 2.2);

   // Define track efficiency histograms
  TH1D* heff_mclen;
  TH1D* heff_mcpdg;
  TH1D* heff_mctheta;
  TH1D* heff_mcphi;
  TH1D* heff_mcthetaxz;
  TH1D* heff_mcthetayz;
  TH1D* heff_mcmom;
   
   int mutrue = 0;
   double d = 0;
   double dmc = 0;
   double d1 = 0;
   double d2 = 0;
  
   for(long i = 0; i < Size; i++) {
   if (i!=0 && i%1000==0) std:: cout << "Processing " << i << "/" << Size << std::endl;
      tree -> GetEntry(i);
      
      if (geant_list_size > kMaxGeant){
	std::cout << "Error: geant_list_size = " << geant_list_size << " is larger than kMaxGeant = " << kMaxGeant << std::endl
		  << "Skipping event" << std::endl;
	continue;
      }

   hnreco -> Fill(ntracks);

   // reconstructed info
   std::vector<Int_t> recoID_vector;
   Int_t nbroken = 0;
   bool is_first = true;
   mutrue = 0;
   for (int recoTracks = 0; recoTracks < ntracks; recoTracks++){
	Int_t recoID = trkg4id[recoTracks];
	if (std::find( recoID_vector.begin(), recoID_vector.end(), recoID) != recoID_vector.end() ) {
		std::cout << "Found Broken track!" << std:: endl;
		nbroken++;
	}
	
	 hstartx -> Fill(trkstartx[recoTracks]);
         hstarty -> Fill(trkstarty[recoTracks]);
         hstartz -> Fill(trkstartz[recoTracks]);
         hendx -> Fill(trkendx[recoTracks]);
         hendy -> Fill(trkendy[recoTracks]);
         hendz -> Fill(trkendz[recoTracks]);

         hlreco -> Fill(trklength[recoTracks]);
         d = sqrt( pow(trkstartx[recoTracks] - trkendx[recoTracks],2) + pow(trkstarty[recoTracks] - trkendy[recoTracks],2) + pow(trkstartz[recoTracks] - trkendz[recoTracks],2) );
         hlrange -> Fill(d);
         hldiff -> Fill(trklength[recoTracks] - d);
           
      bool is_found = false;
      for(Int_t j = 0; j < geant_list_size; j++) {
                Int_t G4ID = TrackId[j];
		if ( is_first && status[j]==1 && Mother[j]==0 && pdg[j] == 13) mutrue++;
                if (recoID == G4ID){ //j is the proper index for the mc particle to be used for this track
                        if (is_found) { 
				std::cout << "Error! Double matching of the same MC particle" << std::endl;
				break;
			}
			is_found = true;
               
			//calculate MC track range, and fill track range and track length
               		dmc = sqrt( pow(StartX[j] - EndX[j], 2) + pow(StartY[j] - EndY[j],2) + pow(StartZ[j] - EndZ[j],2) );
               		hlrangemc -> Fill(dmc);
               		hlmc -> Fill(pathlen[j]);
               		hldiffmc -> Fill(pathlen[j] - dmc);

                  	hlres -> Fill(trklength[recoTracks] - pathlen[j]);
                  	hlresrange -> Fill(d - dmc);
		  
		  	hresostartx -> Fill(trkstartx[recoTracks]-StartX[j]);
		  	hresostarty -> Fill(trkstarty[recoTracks]-StartY[j]);
		  	hresostartz -> Fill(trkstartz[recoTracks]-StartZ[j]);
		  	hresoendx -> Fill(trkendx[recoTracks]-EndX[j]);
		  	hresoendy -> Fill(trkendy[recoTracks]-EndY[j]);
		  	hresoendz -> Fill(trkendz[recoTracks]-EndZ[j]);
		 	
			//if ( inFV( real_StartX[j], real_StartY[j], real_StartZ[j] ) && inFV( real_EndX[j], real_EndY[j], real_EndZ[j] ) ) { //contained tracks
			if ( inFV( trkstartx[recoTracks], trkstarty[recoTracks], trkstartz[recoTracks] ) && inFV( trkendx[recoTracks], trkendy[recoTracks], trkendz[recoTracks] ) ) { //contained tracks
			hresomom_range-> Fill( trkmomrange[recoTracks] - P[j] );
			hresomom_contained_MCSfwd-> Fill( trkmcsfwdmom[recoTracks] - P[j] );
			hresomom_contained_MCSbwd-> Fill( trkmcsbwdmom[recoTracks] - P[j] );
			}

			hresomom_MCSfwd-> Fill( trkmcsfwdmom[recoTracks] - P[j] );
			hresomom_MCSbwd-> Fill( trkmcsbwdmom[recoTracks] - P[j] );

			hpidpida_total -> Fill ( trkpidpida[recoTracks][trkpidbestplane[recoTracks]] );
			if ( pdg[j] == 13 )
			hpidpida_muon -> Fill ( trkpidpida[recoTracks][trkpidbestplane[recoTracks]] );
		  
                  	//calculate start point resolution
                  	d1 = sqrt( pow(StartX[j] - trkstartx[recoTracks], 2) + pow(StartY[j] - trkstarty[recoTracks],2) + pow(StartZ[j] - trkstartz[recoTracks], 2) );
                  	d2 = sqrt( pow(StartX[j] - trkendx[recoTracks], 2) + pow(StartY[j] - trkendy[recoTracks], 2) + pow(StartZ[j] - trkendz[recoTracks], 2) );
                  	if(d1 < d2) {
                     		hresstart -> Fill(d1);
                     		d1 = sqrt( pow(EndX[j] - trkendx[recoTracks], 2) + pow(EndY[j] - trkendy[recoTracks], 2) + pow(EndZ[j] - trkendz[recoTracks], 2) );
                     		hresend -> Fill(d1); 
                 	 } else {
                     		hresstart -> Fill(d2);
                     		d2 = sqrt( pow(EndX[j] - trkstartx[recoTracks],2 ) +pow(EndY[j] - trkstarty[recoTracks],2) +pow(EndZ[j] - trkstartz[recoTracks],2));
                     		hresend -> Fill(d2);	
                  	}

			// Add an entry for this matched reco track to reco histogram
			// Only do this for mu, charged pi, charged K, p
			if (abs(pdg[j]) == 13 || abs(pdg[j]) == 211 || abs(pdg[j]) == 321 || abs(pdg[j]) == 2212){
			  hreco_mclen->Fill(pathlen[j]);
			  hreco_mcpdg->Fill(pdg[j]);
			  hreco_mctheta->Fill(theta[j]*180/3.142);
			  hreco_mcphi->Fill(phi[j]*180/3.142);
			  hreco_mcthetaxz->Fill(theta_xz[j]*180/3.142);
			  hreco_mcthetayz->Fill(theta_yz[j]*180/3.142);
			  hreco_mcmom->Fill(P[j]);
			  }
			
               	} // end-if j is the proper index for the mc particle to be used for this track
               } //end loop on MC particles
      		is_first=false;
            } //end loop on reco tracks
   
      	hntrue -> Fill(mutrue);
		
	// Loop over all true geant particles in event and add entries for all tracks to true histogram
	for (int igeant=0; igeant<geant_list_size; igeant++){
	  // Only do this for mu, charged pi, charged K, p
	  if (abs(pdg[igeant]) == 13 || abs(pdg[igeant]) == 211 || abs(pdg[igeant]) == 321 || abs(pdg[igeant]) == 2212){
	    htrue_mclen->Fill(pathlen[igeant]);
	    htrue_mcpdg->Fill(pdg[igeant]);
	    htrue_mctheta->Fill(theta[igeant]*180/3.142);
	    htrue_mcphi->Fill(phi[igeant]*180/3.142);
	    htrue_mcthetaxz->Fill(theta_xz[igeant]*180/3.142);
	    htrue_mcthetayz->Fill(theta_yz[igeant]*180/3.142);
	    htrue_mcmom->Fill(P[igeant]);
	  }
	}
			
	// Vertex information
	double distmin = 10000;
	double dist = 0;
	double dtmin = 10000;
	double dts = 0;
	double dte = 0;
	for (int i_vtx =0; i_vtx < nnuvtx; i_vtx++){ // Loop over reco vertices
	  distmin = 10000;
	  hvertresx->Fill(nuvtxx[i_vtx] - nuvtxx_truth[0]);
	  hvertresy->Fill(nuvtxy[i_vtx] - nuvtxy_truth[0]);
	  hvertresz->Fill(nuvtxz[i_vtx] - nuvtxz_truth[0]);

	  dist = sqrt((nuvtxx[i_vtx] - nuvtxx_truth[0])*(nuvtxx[i_vtx] - nuvtxx_truth[0]) + (nuvtxy[i_vtx] - nuvtxy_truth[0])*(nuvtxy[i_vtx] - nuvtxy_truth[0]) + (nuvtxz[i_vtx] - nuvtxz_truth[0])*(nuvtxz[i_vtx] - nuvtxz_truth[0]));
	  if(dist < distmin) distmin = dist;

	  dtmin = 10000;
	  for(int recoTracks = 0; recoTracks < ntracks; recoTracks++) { // Loop over reco tracks
            dts = sqrt((nuvtxx[i_vtx] - trkstartx[recoTracks])*(nuvtxx[i_vtx] - trkstartx[recoTracks]) + (nuvtxy[i_vtx] - trkstarty[recoTracks])*(nuvtxy[i_vtx] - trkstarty[recoTracks]) + (nuvtxz[i_vtx] - trkstartz[recoTracks])*(nuvtxz[i_vtx] - trkstartz[recoTracks]));         
            dte = sqrt((nuvtxx[i_vtx] - trkendx[recoTracks])*(nuvtxx[i_vtx] - trkendx[recoTracks]) + (nuvtxy[i_vtx] - trkendy[recoTracks])*(nuvtxy[i_vtx] - trkendy[recoTracks]) + (nuvtxz[i_vtx] - trkendz[recoTracks])*(nuvtxz[i_vtx] - trkendz[recoTracks]));
            if(dts < dtmin) dtmin = dts;
            if(dte < dtmin) dtmin = dte;
	  } //end loop over reco tracks
	  if(dtmin < 10000) hvertdist -> Fill(dtmin);
	} //end loop over reco vertices
	if(distmin < 10000) hvertres -> Fill(distmin);

	// Proton multiplicity (from GENIE)
	int nProtons = 0;
	for (int GENIEpar=0; GENIEpar<genie_no_primaries; GENIEpar++){ // loop over GENIE particles in event
	  if (genie_primaries_pdg[GENIEpar] == 2212 && genie_status_code[GENIEpar] == 1){ // if trackable proton
	    nProtons++;
	  }
	} // end loop over GENIE particles
	hnprotons->Fill(nProtons);
	
   } //end loop on events

   // Make efficiency histograms
   heff_mclen = effcalc(hreco_mclen, htrue_mclen, TString("Tracking Efficiency; True Track Length (cm); Efficiency"));
   heff_mcpdg = effcalc(hreco_mcpdg, htrue_mcpdg, TString("Tracking Efficiency; True PDG Code; Efficiency"));
   heff_mctheta = effcalc(hreco_mctheta, htrue_mctheta, TString("Tracking Efficiency; True #theta (degrees); Efficiency"));
   heff_mcphi = effcalc(hreco_mcphi, htrue_mcphi, TString("Tracking Efficiency; True #phi (degrees); Efficiency"));
   heff_mcthetaxz = effcalc(hreco_mcthetaxz, htrue_mcthetaxz, TString("Tracking Efficiency; True #theta_{xz} (degrees); Efficiency"));
   heff_mcthetayz = effcalc(hreco_mcthetayz, htrue_mcthetayz, TString("Tracking Efficiency; True #theta_{yz}; Efficiency"));
   heff_mcmom = effcalc(hreco_mcmom, htrue_mcmom, TString("Tracking Efficiency; True Momentum (GeV); Efficiency"));

   // Only make reduced set of plots for CI
   hvector.push_back(*hresstart);
   hvector.push_back(*hresend);
   // Note: for now, nuvtxx/nuvtxy/nuvtxz are only available in analysistree from pandoraNu
   // So only make these plots for pandoraNu!
   if (tracking_algorithm == "pandoraNu"){
     hvector.push_back(*hvertres);
   }
   if (short_long == "long") { // Full set of plots 
     hvector.push_back(*hnprotons);
     hvector.push_back(*hnreco);
     hvector.push_back(*hstartx);
     hvector.push_back(*hstarty);
     hvector.push_back(*hstartz);
     hvector.push_back(*hendx);
     hvector.push_back(*hendy);
     hvector.push_back(*hendz);
     hvector.push_back(*hlreco);
     hvector.push_back(*hlmc);
     hvector.push_back(*hldiff);
     hvector.push_back(*hldiffmc);
     hvector.push_back(*hlres);
     hvector.push_back(*hresostartx);
     hvector.push_back(*hresostarty);
     hvector.push_back(*hresostartz);
     hvector.push_back(*hresoendx);
     hvector.push_back(*hresoendy);
     hvector.push_back(*hresoendz);
     hvector.push_back(*hresomom_range);
     hvector.push_back(*hresomom_MCSfwd);
     hvector.push_back(*hresomom_MCSbwd);
     hvector.push_back(*hresomom_contained_MCSfwd);
     hvector.push_back(*hresomom_contained_MCSbwd);
     hvector.push_back(*hpidpida_total);
     hvector.push_back(*hlrange);
     hvector.push_back(*hlresrange);
     hvector.push_back(*hlrangemc);
     hvector.push_back(*hntrue);
     hvector.push_back(*hpidpida_muon);
     // Note: for now, nuvtxx/nuvtxy/nuvtxz are only available in analysistree from pandoraNu
     // So only make these plots for pandoraNu!
     if (tracking_algorithm == "pandoraNu"){
       hvector.push_back(*hvertresx);
       hvector.push_back(*hvertresy);
       hvector.push_back(*hvertresz);
       hvector.push_back(*hvertdist);
     }
     // Note 2: seems like efficiency plots only really make sense (or more accurately: we only really
     // understand them) for pandoraCosmic
     // So only make these plots for pandoraCosmic!
     if (tracking_algorithm == "pandoraCosmic"){
       hvector.push_back(*heff_mclen);
       hvector.push_back(*hreco_mclen);
       hvector.push_back(*htrue_mclen);
       hvector.push_back(*heff_mcpdg);
       hvector.push_back(*hreco_mcpdg);
       hvector.push_back(*htrue_mcpdg);
       hvector.push_back(*heff_mctheta);
       hvector.push_back(*hreco_mctheta);
       hvector.push_back(*htrue_mctheta);
       hvector.push_back(*heff_mcphi);
       hvector.push_back(*hreco_mcphi);
       hvector.push_back(*htrue_mcphi);
       hvector.push_back(*heff_mcthetaxz);
       hvector.push_back(*hreco_mcthetaxz);
       hvector.push_back(*htrue_mcthetaxz);
       hvector.push_back(*heff_mcthetayz);
       hvector.push_back(*hreco_mcthetayz);
       hvector.push_back(*htrue_mcthetayz);
       hvector.push_back(*heff_mcmom);
       hvector.push_back(*hreco_mcmom);
       hvector.push_back(*htrue_mcmom);
     }
   }
} //end function


// ------- Function to calculate chi2 between two histograms -------- //

double calculateChiSqDistance(TH1D O, TH1D E){
  
    double chisq = 0;
    for (int i = 1; i < O.GetNbinsX()+1; i++){

        double O_i = O.GetBinContent(i);
        double E_i = E.GetBinContent(i);
        double O_ierr = O.GetBinError(i);
        double E_ierr = E.GetBinError(i);

        if ((O_i == 0 && E_i == 0)){ 
            chisq += 0;
        }
        else{
            chisq += std::pow(O_i - E_i,2)/(std::sqrt(std::pow(O_ierr,2) + std::pow(E_ierr,2)));
        }
    }

    return chisq;

}

// ------- Function to draw histograms (not comparison: one MC version only) -------- //

void DrawHistos ( std::vector<TH1D> hvector , std::string tag, std::string algorithm ) {
  std::string outroot = "MCcomparison_" + tag + "_" + algorithm + ".root";
  TFile outfile (outroot.c_str(), "recreate");

  std::string outname = string("MCplots_" + tag + "_" + algorithm + ".pdf");

  for (unsigned i=0; i<hvector.size(); i++) {
    TCanvas c1;
    hvector[i].SetLineWidth(2);
    hvector[i].Sumw2();
    double integral = hvector[i].Integral();
    //hvector[i].Scale(1.0/integral);
    hvector[i].Draw("hist e0");
    outfile.cd();
    hvector[i].Write();
    std::string outname_print;
    if (i == 0){
      outname_print = string(outname + "(");
    }
    else if (i == hvector.size()-1){
      outname_print = string(outname + ")");
    }
    else{
      outname_print = string(outname);
    }
    c1.Print(outname_print.c_str(),"pdf");
  }
  outfile.Close();
}

// ------- Function to draw comparison histograms -------- //
	
void DrawComparison( std::vector<TH1D> vector1, std::vector<TH1D> vector2, std::string tag1, std::string tag2, std::string algorithm ) {
	if (vector1.size() != vector2.size() ) { std::cout << "Error! Different size in vec1 and vec2. " << std::endl; exit(-1); }
	std::string outroot = "MCcomparison_" + tag1 + "_" + tag2 + "_" + algorithm + ".root";
	TFile outfile (outroot.c_str(), "recreate");

	
	std::string outname = string("MCcomparison_" + tag1 + "_" + tag2 + "_" + algorithm + ".pdf");
	
	for (unsigned i=0; i<vector1.size(); i++) {
	TCanvas c1;
	vector1[i].SetLineWidth(2);
	vector1[i].SetStats(0);
	vector1[i].Sumw2();
	if(string(vector1[i].GetName()).find("eff") != std::string::npos){ // Don't normalise efficiency histograms (they're already normalised!)
	  // do nothing
	}
	else{
	  double integral1 = vector1[i].Integral();
	  vector1[i].Scale(1.0/integral1);
	}
	vector1[i].Draw("hist e0");
	vector2[i].SetLineWidth(2);
	vector2[i].SetLineColor(2);
	vector2[i].SetStats(0);
	vector2[i].Sumw2();
	if(string(vector2[i].GetName()).find("eff") != std::string::npos){ // Don't normalise efficiency histograms (they're already normalised!)
	  // do nothing
	}
	else{
	  double integral2 = vector2[i].Integral();
	  vector2[i].Scale(1.0/integral2);
	}
	vector2[i].Draw("hist e0 same");
	c1.SetName( string(vector1[i].GetName()).substr(0, string(vector1[i].GetName()).size() - tag1.size() -1 ).c_str() );
	c1.SetTitle( string(vector1[i].GetName()).substr(0, string(vector1[i].GetName()).size() - tag1.size() -1).c_str() );

	// Resize y axis to show both histograms
	double maxval = vector1[i].GetMaximum();
	if (vector2[i].GetMaximum() > maxval){ maxval = vector2[i].GetMaximum(); }
	vector1[i].GetYaxis()->SetRangeUser(0,maxval*1.1);

	// Calculate chi2 between two plots and put in format for legend
	double chisqv = calculateChiSqDistance(vector1[i], vector2[i]);
	TString chisq = Form("#chi^{2}: %g", chisqv);
	int nBins = std::max(vector1[i].GetNbinsX(), vector2[i].GetNbinsX());
	TString NDF = Form("No. Bins: %i", nBins);
	double chisqNDF = chisqv/(double)nBins;
	TString chisqNDFstr = Form("#chi^{2}/No. bins: %g", chisqNDF);

	// If chisq is large, print to file
	if (chisqv >= chisqNotifierCut/100.0){
	  std::ofstream highChisqFile;
	  highChisqFile.open("highChisqPlots.txt", std::ios_base::app);
	  highChisqFile << c1.GetName() << " (" << algorithm << "): chisq = " << chisqv << "\n";
	  highChisqFile.close();
	}
	
	// Make legend
	TLegend *legend = new TLegend(0.55, 0.68, 0.89, 0.89);
        legend->AddEntry( vector1[i].GetName(), tag1.c_str(),"l");
        legend->AddEntry( vector2[i].GetName(), tag2.c_str(),"l");
	legend->AddEntry((TObject*)0, chisq, "");
	legend->AddEntry((TObject*)0, NDF, "");
	legend->AddEntry((TObject*)0, chisqNDFstr, "");
	legend->SetLineWidth(0);
	legend->Draw();

	outfile.cd();
	c1.Write();

	std::string outname_print;
	if (i == 0){
	  outname_print = string(outname+"(");
	}
	else if (i == vector1.size()-1){
	  outname_print = string(outname + ")");
	}
	else{
	  outname_print = string(outname);
	}
	
	c1.Print(outname_print.c_str(),"pdf");
	}
						       
	outfile.Close();
}




// ------------------------------ //
// ------- Main function -------- //
// ------------------------------ //

int main ( int argc, char** argv ) {

	if ( argc != 4 && argc != 7 ) {
		std::cout << "Usage: ./track_comparison anatree1.root tag1 <optional: anatree2.root tag2 chi2cut*100> short/long" << std::endl;
		std::cout << "ex1. ./track_comparison file1.root MCC8.3 file2.root MCC8.4 300 short" << std::endl;
		std::cout << "ex2. ./track_comparison file1.root MCC8.3 long" << std::endl;
		std::cout << "\"long\" will produce and save more (redundant) histograms for deeper analysis." << std::endl;
		std::cout << "\"chi2cut*100\" defines a 'bad' chi2 -- any comparison plots with chi2/nbins>(chi2cut*100/100) will have their names written to file to remind you to check them" << std::endl;
		return -1;
	}
	
	bool comparison = false;
	if (argc == 7) comparison = true;
	
	std::string file1_s ( argv[1] );
	std::string tag1 ( argv[2] );
	std::string short_long ( argv[3] );
	std::string file2_s="", tag2="";
	if (comparison) {
		file2_s = string(argv[3]);
		tag2 = string(argv[4]);
		short_long = string (argv[6]);
		
		std::string chisqNotifierCut_str (argv[5]);
		chisqNotifierCut = std::atoi(chisqNotifierCut_str.c_str());
		std::cout << "Notifying about any comparison plots with chi2 > " << chisqNotifierCut/100.0 << std::endl;
	}

	if ( short_long != "short" && short_long!="long") {
		std::cout << "The last option MUST be \"short\" OR \"long\" " << endl;
		return -1;
	}

	TFile* file1;
	file1 = new TFile(file1_s.c_str(), "open");
	if (file1->IsZombie()) {
		std::cout << "I can't open " << file1_s << std::endl;
		return -1;
	}
	TTree* tree1 = NULL;
	tree1 = (TTree*) file1->Get("analysistree/anatree");
	if (!tree1) {
		std::cout << "I can't find analysistree/anatree in " << file1_s << std::endl;
		return -1;
	}

	TFile* file2;
	TTree* tree2;

	if (comparison) {
	file2 = new TFile(file2_s.c_str(), "open");
	if (file2->IsZombie()) {
		std::cout << "I can't open " << file2_s << std::endl;
		return -1;
	}
	tree2 = (TTree*) file2->Get("analysistree/anatree");
	if (!tree2) {
		std::cout << "I can't find analysistree/anatree in " << file2_s << std::endl;
		file2->ls();
		return -1;
	}
	}

	std::vector<std::string> algorithm = { "pandoraNu" };
	if ( short_long == "long" ) {
	        algorithm.push_back ( "pandoraCosmic" );
		algorithm.push_back ( "pandoraNuKHit" );
		algorithm.push_back ( "pandoraCosmicKHit" );
		algorithm.push_back ( "pandoraNuKalmanTrack" );
		}

	for (unsigned algorithms = 0; algorithms < algorithm.size(); algorithms++) {
	  std::vector<TH1D> vector1;
	  FillPlots_MC ( tree1, vector1, algorithm[ algorithms ], tag1, short_long );
	 
	  
	  // In "long" mode, draw both sets of histograms separately as well as the comparison
	  // Also do this if you're not doing a comparison
	  if (short_long == "long" || !comparison){
	    DrawHistos( vector1, tag1, algorithm[ algorithms ]);
	  }
	  
	  if (!comparison) continue;
	  
	  std::vector<TH1D> vector2;
	  file2->cd();
	  FillPlots_MC ( tree2, vector2, algorithm[ algorithms ], tag2, short_long );
	  // In "long" mode, draw both sets of histograms separately as well as the comparison
	  if (short_long == "long"){ 
	    DrawHistos( vector2, tag2, algorithm[ algorithms ] );
	  }
	  
	  DrawComparison( vector1, vector2, tag1, tag2, algorithm[ algorithms ] );
	  
	}

	return 0;

}
