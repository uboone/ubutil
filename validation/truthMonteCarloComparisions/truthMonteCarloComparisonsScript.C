#include <iostream>
#include <fstream>
#include <cstdlib>
#include <cctype>
#include <functional>
#include <string>
#include <algorithm>
#include <cassert>
#include "TH1.h"
#include "TH2.h"
#include "TTree.h"
#include "TFile.h"
#include "TCanvas.h"
#include "TLegend.h"
#include "TMath.h"
#include "TVector3.h"
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


// This function wraps text (so we can output multi-line .comment files for the CI dashboard)
void textWrap(string &in, ostream& out, size_t width) {

   string tmp;
   char cur = '\0';
   char last = '\0';
   size_t i = 0;

   for (size_t idx_in_str=0; idx_in_str < in.size(); idx_in_str++) {
     cur = in.at(idx_in_str);
     if (idx_in_str == in.size()-1){ // Add last word to the file
       out << tmp << cur << '\n';
     }
     if (++i == width) { // If you get to the character limit for a line, add it to the file
       if (isspace(tmp.at(0))){ // Remove leading spaces
	 //tmp = tmp.substr(1,tmp.size()-1);
	 tmp.erase(tmp.begin());
       }
       out << '\n' << tmp;
       i = tmp.length();
       tmp.clear();
     }
     else if (isspace(cur) && !isspace(last)) { // This is the end of a word. Add it to the file
       out << tmp;
       tmp.clear();
     }
     tmp += cur;
     last = cur;
   }
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

      float err = TMath::Sqrt(eff_bc * (1.+eff_bc)/true_bc);

      heff->SetBinContent(ibin, eff_bc);
      heff->SetBinError(ibin, err);
    }
  }
  heff->SetMarkerStyle(20);
  heff->GetYaxis()->SetRangeUser(0,1.5);

  return heff;
}





// ------- Function to make all of the plots -------- //

void FillPlots_MC( TTree* tree, std::vector<TH1D> &hvector, std::string tracking_algorithm, std::string version, std::string short_long, std::vector<std::string> &comments ) {

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
   Float_t         trkpurity[kMaxTracks]; // Track purity based on hit information
   Float_t         trkcompleteness[kMaxTracks]; // Track completeness based on hit information

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
   Int_t           inTPCActive[kMaxGeant];
   Int_t           process_primary[kMaxGeant];

   const int maxtruth = 10;
   Int_t           mcevts_truth;               //number of neutrino interactions in the spill
   Float_t         nuvtxx_truth[maxtruth];    //neutrino vertex x in cm
   Float_t         nuvtxy_truth[maxtruth];    //neutrino vertex y in cm
   Float_t         nuvtxz_truth[maxtruth];    //neutrino vertex z in cm

   const int maxgenie = 70;
   Int_t           genie_no_primaries;
   Int_t           genie_primaries_pdg[maxgenie];
   Int_t           genie_status_code[maxgenie];

   Int_t           no_mctracks; // number of MC tracks in this event

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
   branch_name = "trkpurity_" + tracking_algorithm;
   tree -> SetBranchStatus(branch_name.c_str(),1);
   tree -> SetBranchAddress(branch_name.c_str(), trkpurity);
   branch_name = "trkcompleteness_" + tracking_algorithm;
   tree -> SetBranchStatus(branch_name.c_str(),1);
   tree -> SetBranchAddress(branch_name.c_str(), trkcompleteness);

   tree -> SetBranchStatus("geant_list_size",1);
   tree -> SetBranchAddress("geant_list_size", &geant_list_size);
   tree -> SetBranchStatus("TrackId",1);
   tree -> SetBranchAddress("TrackId", TrackId);
   // Don't use space charge correction
   // Note: this is only really true if you're looking at BNB
   // For cosmics you will want to edit this to use space charge correction
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

     // This is what you would do if you wanted to use space charge correction
     /*std::cout << "Using space charge correction for start/end points and vertices" << std::endl;
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
     tree -> SetBranchAddress(branch_name.c_str(), &nuvtxz);*/

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
   tree -> SetBranchStatus("no_mctracks",1);
   tree -> SetBranchAddress("no_mctracks", &no_mctracks);
   tree -> SetBranchStatus("inTPCActive",1);
   tree -> SetBranchAddress("inTPCActive", &inTPCActive);
   tree -> SetBranchStatus("process_primary",1);
   tree -> SetBranchAddress("process_primary", &process_primary);

   long Size = tree -> GetEntries();
   cout << "Number of events in the tree is: " << Size << endl;

   std::string histoname = "hnreco_" + version;
   TH1D *hnreco = new TH1D(histoname.c_str(), "Number of reco tracks; Number of reco tracks;", 30, 0, 30);
   histoname = "hntrue_" + version;
   TH1D *hntrue = new TH1D(histoname.c_str(), "Number of true tracks; # True tracks;", 50, 0, 50);
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
   histoname = "htrkpurity_" + version;
   TH1D *htrkpurity = new TH1D(histoname.c_str(), "Track Purity based on hit information", 100, 0, 1);
   histoname = "htrkcompleteness_" + version;
   TH1D *htrkcompleteness = new TH1D(histoname.c_str(), "Track Completeness based on hit information", 100, 0, 1);
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
   TH1D *hresstart = new TH1D(histoname.c_str(), "Track start resolution; Track start position (reco) - track start position (true) [cm];", 100, -50, 50);
   histoname = "hresend_" + version;
   TH1D *hresend = new TH1D(histoname.c_str(), "Track end resolution; Track end position (reco) - track end position (true) [cm];", 100, -50, 50);
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
   histoname = "hnmatchedtracks_" + version;
   TH1D *hnmatchedtracks = new TH1D(histoname.c_str(),"Number of reco tracks matched per geant track (#mu^{+/-}, #pi^{+/-}, K^{+/-}, p); Number of reco tracks;", 4, -0.5, 3.5);

   // Define track efficiency truth histograms
   histoname = "htrue_mclen_" + version;
   TH1D *htrue_mclen = new TH1D(histoname.c_str(),"True Length (#mu^{+/-}, #pi^{+/-}, K^{+/-}, p)", 60, 0, 1200);
   histoname = "htrue_mctheta_" + version;
   TH1D *htrue_mctheta = new TH1D(histoname.c_str(),"True Theta (#mu^{+/-}, #pi^{+/-}, K^{+/-}, p)", 20, 0, 180);
   histoname = "htrue_mcphi_" + version;
   TH1D *htrue_mcphi = new TH1D(histoname.c_str(),"True Phi (#mu^{+/-}, #pi^{+/-}, K^{+/-}, p)", 20, -180, 180);
   histoname = "htrue_mcmom_" + version;
   TH1D *htrue_mcmom = new TH1D(histoname.c_str(),"True Momentum (#mu^{+/-}, #pi^{+/-}, K^{+/-}, p)", 20, 0, 2.2);
   histoname = "htrue_muon_mclen_" + version;
   TH1D *htrue_muon_mclen = new TH1D(histoname.c_str(),"True Length (#mu^{+/-} only)", 60, 0, 1200);
   histoname = "htrue_muon_mctheta_" + version;
   TH1D *htrue_muon_mctheta = new TH1D(histoname.c_str(),"True Theta (#mu^{+/-} only)", 20, 0, 180);
   histoname = "htrue_muon_mcphi_" + version;
   TH1D *htrue_muon_mcphi = new TH1D(histoname.c_str(),"True Phi (#mu^{+/-} only)", 20, -180, 180);
   histoname = "htrue_muon_mcmom_" + version;
   TH1D *htrue_muon_mcmom = new TH1D(histoname.c_str(),"True Momentum (#mu^{+/-} only)", 20, 0, 2.2);
   histoname = "htrue_pion_mclen_" + version;
   TH1D *htrue_pion_mclen = new TH1D(histoname.c_str(),"True Length (#pi^{+/-} only)", 60, 0, 1200);
   histoname = "htrue_pion_mctheta_" + version;
   TH1D *htrue_pion_mctheta = new TH1D(histoname.c_str(),"True Theta (#pi^{+/-} only)", 20, 0, 180);
   histoname = "htrue_pion_mcphi_" + version;
   TH1D *htrue_pion_mcphi = new TH1D(histoname.c_str(),"True Phi (#pi^{+/-} only)", 20, -180, 180);
   histoname = "htrue_pion_mcmom_" + version;
   TH1D *htrue_pion_mcmom = new TH1D(histoname.c_str(),"True Momentum (#pi^{+/-} only)", 20, 0, 2.2);
   histoname = "htrue_kaon_mclen_" + version;
   TH1D *htrue_kaon_mclen = new TH1D(histoname.c_str(),"True Length (K^{+/-} only)", 60, 0, 1200);
   histoname = "htrue_kaon_mctheta_" + version;
   TH1D *htrue_kaon_mctheta = new TH1D(histoname.c_str(),"True Theta (K^{+/-} only)", 20, 0, 180);
   histoname = "htrue_kaon_mcphi_" + version;
   TH1D *htrue_kaon_mcphi = new TH1D(histoname.c_str(),"True Phi (K^{+/-} only)", 20, -180, 180);
   histoname = "htrue_kaon_mcmom_" + version;
   TH1D *htrue_kaon_mcmom = new TH1D(histoname.c_str(),"True Momentum (K^{+/-} only)", 20, 0, 2.2);
   histoname = "htrue_proton_mclen_" + version;
   TH1D *htrue_proton_mclen = new TH1D(histoname.c_str(),"True Length (p only)", 60, 0, 1200);
   histoname = "htrue_proton_mctheta_" + version;
   TH1D *htrue_proton_mctheta = new TH1D(histoname.c_str(),"True Theta (p only)", 20, 0, 180);
   histoname = "htrue_proton_mcphi_" + version;
   TH1D *htrue_proton_mcphi = new TH1D(histoname.c_str(),"True Phi (p only)", 20, -180, 180);
   histoname = "htrue_proton_mcmom_" + version;
   TH1D *htrue_proton_mcmom = new TH1D(histoname.c_str(),"True Momentum (p only)", 20, 0, 2.2);

   // Define track efficiency reco histograms
   histoname = "hreco_mclen_" + version;
   TH1D *hreco_mclen = new TH1D(histoname.c_str(),"Reco Length (#mu^{+/-}, #pi^{+/-}, K^{+/-}, p)", 60, 0, 1200);
   histoname = "hreco_mctheta_" + version;
   TH1D *hreco_mctheta = new TH1D(histoname.c_str(),"Reco Theta (#mu^{+/-}, #pi^{+/-}, K^{+/-}, p)", 20, 0, 180);
   histoname = "hreco_mcphi_" + version;
   TH1D *hreco_mcphi = new TH1D(histoname.c_str(),"Reco Phi (#mu^{+/-}, #pi^{+/-}, K^{+/-}, p)", 20, -180, 180);
   histoname = "hreco_mcmom_" + version;
   TH1D *hreco_mcmom = new TH1D(histoname.c_str(),"Reco Momentum (#mu^{+/-}, #pi^{+/-}, K^{+/-}, p)", 20, 0, 2.2);
   histoname = "hreco_muon_mclen_" + version;
   TH1D *hreco_muon_mclen = new TH1D(histoname.c_str(),"True Length (#mu^{+/-} only)", 60, 0, 1200);
   histoname = "hreco_muon_mctheta_" + version;
   TH1D *hreco_muon_mctheta = new TH1D(histoname.c_str(),"True Theta (#mu^{+/-} only)", 20, 0, 180);
   histoname = "hreco_muon_mcphi_" + version;
   TH1D *hreco_muon_mcphi = new TH1D(histoname.c_str(),"True Phi (#mu^{+/-} only)", 20, -180, 180);
   histoname = "hreco_muon_mcmom_" + version;
   TH1D *hreco_muon_mcmom = new TH1D(histoname.c_str(),"True Momentum (#mu^{+/-} only)", 20, 0, 2.2);
   histoname = "hreco_pion_mclen_" + version;
   TH1D *hreco_pion_mclen = new TH1D(histoname.c_str(),"True Length (#pi^{+/-} only)", 60, 0, 1200);
   histoname = "hreco_pion_mctheta_" + version;
   TH1D *hreco_pion_mctheta = new TH1D(histoname.c_str(),"True Theta (#pi^{+/-} only)", 20, 0, 180);
   histoname = "hreco_pion_mcphi_" + version;
   TH1D *hreco_pion_mcphi = new TH1D(histoname.c_str(),"True Phi (#pi^{+/-} only)", 20, -180, 180);
   histoname = "hreco_pion_mcmom_" + version;
   TH1D *hreco_pion_mcmom = new TH1D(histoname.c_str(),"True Momentum (#pi^{+/-} only)", 20, 0, 2.2);
   histoname = "hreco_kaon_mclen_" + version;
   TH1D *hreco_kaon_mclen = new TH1D(histoname.c_str(),"True Length (K^{+/-} only)", 60, 0, 1200);
   histoname = "hreco_kaon_mctheta_" + version;
   TH1D *hreco_kaon_mctheta = new TH1D(histoname.c_str(),"True Theta (K^{+/-} only)", 20, 0, 180);
   histoname = "hreco_kaon_mcphi_" + version;
   TH1D *hreco_kaon_mcphi = new TH1D(histoname.c_str(),"True Phi (K^{+/-} only)", 20, -180, 180);
   histoname = "hreco_kaon_mcmom_" + version;
   TH1D *hreco_kaon_mcmom = new TH1D(histoname.c_str(),"True Momentum (K^{+/-} only)", 20, 0, 2.2);
   histoname = "hreco_proton_mclen_" + version;
   TH1D *hreco_proton_mclen = new TH1D(histoname.c_str(),"True Length (p only)", 60, 0, 1200);
   histoname = "hreco_proton_mctheta_" + version;
   TH1D *hreco_proton_mctheta = new TH1D(histoname.c_str(),"True Theta (p only)", 20, 0, 180);
   histoname = "hreco_proton_mcphi_" + version;
   TH1D *hreco_proton_mcphi = new TH1D(histoname.c_str(),"True Phi (p only)", 20, -180, 180);
   histoname = "hreco_proton_mcmom_" + version;
   TH1D *hreco_proton_mcmom = new TH1D(histoname.c_str(),"True Momentum (p only)", 20, 0, 2.2);

   // Define track efficiency histograms
  TH1D* heff_mclen;
  TH1D* heff_mctheta;
  TH1D* heff_mcphi;
  TH1D* heff_mcmom;
  TH1D* heff_muon_mclen;
  TH1D* heff_muon_mctheta;
  TH1D* heff_muon_mcphi;
  TH1D* heff_muon_mcmom;
  TH1D* heff_pion_mclen;
  TH1D* heff_pion_mctheta;
  TH1D* heff_pion_mcphi;
  TH1D* heff_pion_mcmom;
  TH1D* heff_kaon_mclen;
  TH1D* heff_kaon_mctheta;
  TH1D* heff_kaon_mcphi;
  TH1D* heff_kaon_mcmom;
  TH1D* heff_proton_mclen;
  TH1D* heff_proton_mctheta;
  TH1D* heff_proton_mcphi;
  TH1D* heff_proton_mcmom;

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
   hntrue -> Fill(no_mctracks);

   // reconstructed info
   Int_t nbroken = 0;
   bool is_first = true;
   mutrue = 0;
   Int_t matchedtracks[geant_list_size] = {0};
   for (int recoTracks = 0; recoTracks < ntracks; recoTracks++){

     // Reco-only plots
     hstartx -> Fill(trkstartx[recoTracks]);
     hstarty -> Fill(trkstarty[recoTracks]);
     hstartz -> Fill(trkstartz[recoTracks]);
     hendx -> Fill(trkendx[recoTracks]);
     hendy -> Fill(trkendy[recoTracks]);
     hendz -> Fill(trkendz[recoTracks]);
     htrkpurity -> Fill(trkpurity[recoTracks]);
     htrkcompleteness -> Fill(trkcompleteness[recoTracks]);

     hlreco -> Fill(trklength[recoTracks]);
     d = sqrt( pow(trkstartx[recoTracks] - trkendx[recoTracks],2) + pow(trkstarty[recoTracks] - trkendy[recoTracks],2) + pow(trkstartz[recoTracks] - trkendz[recoTracks],2) );
     hlrange -> Fill(d);
     hldiff -> Fill(trklength[recoTracks] - d);

     // Now move on to plots that include comparison to truth-level variables
     // Need to match to a truth track
     Int_t g4ID = trkg4id[recoTracks];
     Int_t mcID = 99999999;
     bool is_found = false;
     for (Int_t j = 0; j < geant_list_size; j++){
       if (TrackId[j] == g4ID){ // j is the proper index for the MC particle to be used for this track
      	 /*if (is_found){
      	   std::cout << "[ERROR] Tried to match two true particles to one reco track!" << std::endl;
      	   continue;
      	 }*/
         matchedtracks[j]++;
      	 mcID = j;
      	 is_found = true;
           }
         }
         if (mcID == 99999999){
           std::cout << "Track not matched: recoTracks = " << recoTracks << ", trkg4id = " << g4ID << std::endl;
           std::cout << "Skipping track for reco/truth plots" << std::endl;
           continue;
         }

     //calculate MC track range, and fill track range and track length
     dmc = sqrt( pow(StartX[mcID] - EndX[mcID], 2) + pow(StartY[mcID] - EndY[mcID],2) + pow(StartZ[mcID] - EndZ[mcID],2) );
     hlrangemc -> Fill(dmc);
     hlmc -> Fill(pathlen[mcID]);
     hldiffmc -> Fill(pathlen[mcID] - dmc);

     hlres -> Fill(trklength[recoTracks] - pathlen[mcID]);
     hlresrange -> Fill(d - dmc);

     hresostartx -> Fill(trkstartx[recoTracks]-StartX[mcID]);
     hresostarty -> Fill(trkstarty[recoTracks]-StartY[mcID]);
     hresostartz -> Fill(trkstartz[recoTracks]-StartZ[mcID]);
     hresoendx -> Fill(trkendx[recoTracks]-EndX[mcID]);
     hresoendy -> Fill(trkendy[recoTracks]-EndY[mcID]);
     hresoendz -> Fill(trkendz[recoTracks]-EndZ[mcID]);

     //if ( inFV( real_StartX[mcID], real_StartY[mcID], real_StartZ[mcID] ) && inFV( real_EndX[mcID], real_EndY[mcID], real_EndZ[mcID] ) ) { //contained tracks
     if ( inFV( trkstartx[recoTracks], trkstarty[recoTracks], trkstartz[recoTracks] ) && inFV( trkendx[recoTracks], trkendy[recoTracks], trkendz[recoTracks] ) ) { //contained tracks
       hresomom_range-> Fill( trkmomrange[recoTracks] - P[mcID] );
       hresomom_contained_MCSfwd-> Fill( trkmcsfwdmom[recoTracks] - P[mcID] );
       hresomom_contained_MCSbwd-> Fill( trkmcsbwdmom[recoTracks] - P[mcID] );
     }

     hresomom_MCSfwd-> Fill( trkmcsfwdmom[recoTracks] - P[mcID] );
     hresomom_MCSbwd-> Fill( trkmcsbwdmom[recoTracks] - P[mcID] );

     hpidpida_total -> Fill ( trkpidpida[recoTracks][trkpidbestplane[recoTracks]] );
     if ( pdg[mcID] == 13 )
       hpidpida_muon -> Fill ( trkpidpida[recoTracks][trkpidbestplane[recoTracks]] );

     //calculate start point resolution
     d1 = sqrt( pow(StartX[mcID] - trkstartx[recoTracks], 2) + pow(StartY[mcID] - trkstarty[recoTracks],2) + pow(StartZ[mcID] - trkstartz[recoTracks], 2) );
     d2 = sqrt( pow(StartX[mcID] - trkendx[recoTracks], 2) + pow(StartY[mcID] - trkendy[recoTracks], 2) + pow(StartZ[mcID] - trkendz[recoTracks], 2) );

     TVector3 dstartvec(trkstartx[recoTracks] - StartX[mcID],
                       trkstarty[recoTracks] - StartY[mcID],
                       trkstartz[recoTracks] - StartZ[mcID]);
     TVector3 dendvec(trkendx[recoTracks] - EndX[mcID],
                      trkendy[recoTracks] - EndY[mcID],
                      trkendz[recoTracks] - EndZ[mcID]);

     TVector3 dstartvecflipped(trkendx[recoTracks] - StartX[mcID],
                               trkendy[recoTracks] - StartY[mcID],
                               trkendz[recoTracks] - StartZ[mcID]);
     TVector3 dendvecflipped(trkstartx[recoTracks] - EndX[mcID],
                             trkstarty[recoTracks] - EndY[mcID],
                             trkstartz[recoTracks] - EndZ[mcID]);

     TVector3 truevec(EndX[mcID] - StartX[mcID],
                      EndY[mcID] - StartY[mcID],
                      EndZ[mcID] - StartZ[mcID]);

     double dstartvec_mag = dstartvec.Mag();
     double dendvec_mag   = dendvec.Mag();
     double dstartvecflipped_mag = dstartvecflipped.Mag();
     double dendvecflipped_mag   = dendvecflipped.Mag();

     if(dstartvec_mag < dendvec_mag) {
       // Sign(dstartvec_mag,truevec.Dot(dstartvec)) returns dstartvec_mag with the sign of truevec.Dot(dstartvec) -- this gives the magnitude of the difference vector with the sign +ve if it goes along the true track direction and -ve if it goes against it.
       hresstart -> Fill(TMath::Sign(dstartvec_mag,truevec.Dot(dstartvec)));
       hresend -> Fill(TMath::Sign(dendvec_mag,truevec.Dot(dendvec)));
     } else {
       hresstart -> Fill(TMath::Sign(dstartvecflipped_mag,truevec.Dot(dstartvecflipped)));
       hresend -> Fill(TMath::Sign(dendvecflipped_mag,truevec.Dot(dendvecflipped)));
     }

     // Add an entry for this matched reco track to reco histogram
     // Only do this for mu, charged pi, charged K, p
     // Only do this if the true track starts in the FV
     if (inFV(real_StartX[mcID], real_StartY[mcID], real_StartZ[mcID])){
       // To avoid double-counting, skip tracks with completeness < 51% and purity < 51%
       if (trkcompleteness[recoTracks] < 0.51) continue;
       if (trkpurity[recoTracks] < 0.51) continue;

       if (TMath::Abs(pdg[mcID]) == 13 || TMath::Abs(pdg[mcID]) == 211 || TMath::Abs(pdg[mcID]) == 321 || TMath::Abs(pdg[mcID]) == 2212){
      	 hreco_mclen->Fill(pathlen[mcID]);
      	 hreco_mctheta->Fill(theta[mcID]*180/3.142);
      	 hreco_mcphi->Fill(phi[mcID]*180/3.142);
      	 hreco_mcmom->Fill(P[mcID]);
       }
       if (TMath::Abs(pdg[mcID]) == 13){ // Muons only
      	 hreco_muon_mclen->Fill(pathlen[mcID]);
      	 hreco_muon_mctheta->Fill(theta[mcID]*180/3.142);
      	 hreco_muon_mcphi->Fill(phi[mcID]*180/3.142);
      	 hreco_muon_mcmom->Fill(P[mcID]);
       }
       if (TMath::Abs(pdg[mcID]) == 211){ // Charged Pions only
      	 hreco_pion_mclen->Fill(pathlen[mcID]);
      	 hreco_pion_mctheta->Fill(theta[mcID]*180/3.142);
      	 hreco_pion_mcphi->Fill(phi[mcID]*180/3.142);
      	 hreco_pion_mcmom->Fill(P[mcID]);
       }
       if (TMath::Abs(pdg[mcID]) == 321){ // Charged Kaons only
      	 hreco_kaon_mclen->Fill(pathlen[mcID]);
      	 hreco_kaon_mctheta->Fill(theta[mcID]*180/3.142);
      	 hreco_kaon_mcphi->Fill(phi[mcID]*180/3.142);
      	 hreco_kaon_mcmom->Fill(P[mcID]);
       }
       if (TMath::Abs(pdg[mcID]) == 2212){ // Protons only
      	 hreco_proton_mclen->Fill(pathlen[mcID]);
      	 hreco_proton_mctheta->Fill(theta[mcID]*180/3.142);
      	 hreco_proton_mcphi->Fill(phi[mcID]*180/3.142);
      	 hreco_proton_mcmom->Fill(P[mcID]);
       }
     }


   } //end loop on reco tracks


   // Loop over all true geant particles in event and add entries for all particles to true histogram
   for (int igeant=0; igeant<geant_list_size; igeant++){

    // Check if the true start position is in the TPC
    if (!inFV(real_StartX[igeant], real_StartY[igeant], real_StartZ[igeant])){
      //std::cout << "Track start true point not in FV: igeant = " << igeant << std::endl;
      // std::cout << "Skipping track..." << std::endl;
      continue;
    }

    // Fill histogram of number of matched reco tracks per single geant track
    if ((TMath::Abs(pdg[igeant]) == 13 || TMath::Abs(pdg[igeant]) == 211 || TMath::Abs(pdg[igeant]) == 321 || TMath::Abs(pdg[igeant]) == 2212) && inTPCActive[igeant]){
     //std::cout << "matchedtracks[" << igeant << "] = " << matchedtracks[igeant] << ", length " << pathlen[igeant] << ", inTPCActive = " << inTPCActive[igeant] << std::endl;
      hnmatchedtracks->Fill(matchedtracks[igeant]);
    }

     // Only do this for mu, charged pi, charged K, p
     if (TMath::Abs(pdg[igeant]) == 13 || TMath::Abs(pdg[igeant]) == 211 || TMath::Abs(pdg[igeant]) == 321 || TMath::Abs(pdg[igeant]) == 2212){
    	 htrue_mclen->Fill(pathlen[igeant]);
    	 htrue_mctheta->Fill(theta[igeant]*180/3.142);
    	 htrue_mcphi->Fill(phi[igeant]*180/3.142);
    	 htrue_mcmom->Fill(P[igeant]);
     }
     if (TMath::Abs(pdg[igeant]) == 13){ // Muons only
       htrue_muon_mclen->Fill(pathlen[igeant]);
       htrue_muon_mctheta->Fill(theta[igeant]*180/3.142);
       htrue_muon_mcphi->Fill(phi[igeant]*180/3.142);
       htrue_muon_mcmom->Fill(P[igeant]);
     }
     if (TMath::Abs(pdg[igeant]) == 211){ // Charged Pions only
       htrue_pion_mclen->Fill(pathlen[igeant]);
       htrue_pion_mctheta->Fill(theta[igeant]*180/3.142);
       htrue_pion_mcphi->Fill(phi[igeant]*180/3.142);
       htrue_pion_mcmom->Fill(P[igeant]);
     }
     if (TMath::Abs(pdg[igeant]) == 321){ // Charged Kaons only
       htrue_kaon_mclen->Fill(pathlen[igeant]);
       htrue_kaon_mctheta->Fill(theta[igeant]*180/3.142);
       htrue_kaon_mcphi->Fill(phi[igeant]*180/3.142);
       htrue_kaon_mcmom->Fill(P[igeant]);
       }
     if (TMath::Abs(pdg[igeant]) == 2212){ // Protons only
       htrue_proton_mclen->Fill(pathlen[igeant]);
       htrue_proton_mctheta->Fill(theta[igeant]*180/3.142);
       htrue_proton_mcphi->Fill(phi[igeant]*180/3.142);
       htrue_proton_mcmom->Fill(P[igeant]);
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
            dts = sqrt((nuvtxx[i_vtx] - trkstartx[recoTracks])*(nuvtxx[i_vtx] - trkstartx[recoTracks]) + (nuvtxy[i_vtx] - trkstarty[recoTracks])*(nuvtxy[i_vtx] - trkstarty[recoTracks]) + (nuvtxz[i_vtx] - trkstartz[recoTracks])*(nuvtxz[i_vtx] - trkstartz[recoTracks]));     // distance vertex-track start
            dte = sqrt((nuvtxx[i_vtx] - trkendx[recoTracks])*(nuvtxx[i_vtx] - trkendx[recoTracks]) + (nuvtxy[i_vtx] - trkendy[recoTracks])*(nuvtxy[i_vtx] - trkendy[recoTracks]) + (nuvtxz[i_vtx] - trkendz[recoTracks])*(nuvtxz[i_vtx] - trkendz[recoTracks])); // distance vertex-track end
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
   // All charged particle types
   heff_mclen = effcalc(hreco_mclen, htrue_mclen, TString("Tracking Efficiency: #mu^{+/-}, #pi^{+/-}, K^{+/-}, p; True Track Length (cm); Efficiency"));
   heff_mctheta = effcalc(hreco_mctheta, htrue_mctheta, TString("Tracking Efficiency: #mu^{+/-}, #pi^{+/-}, K^{+/-}, p; True #theta (degrees); Efficiency"));
   heff_mcphi = effcalc(hreco_mcphi, htrue_mcphi, TString("Tracking Efficiency: #mu^{+/-}, #pi^{+/-}, K^{+/-}, p; True #phi (degrees); Efficiency"));
   heff_mcmom = effcalc(hreco_mcmom, htrue_mcmom, TString("Tracking Efficiency: #mu^{+/-}, #pi^{+/-}, K^{+/-}, p; True Momentum (GeV); Efficiency"));
   // Muons
   heff_muon_mclen = effcalc(hreco_muon_mclen, htrue_muon_mclen, TString("Tracking Efficiency: #mu^{+/-}; True Track Length (cm); Efficiency"));
   heff_muon_mctheta = effcalc(hreco_muon_mctheta, htrue_muon_mctheta, TString("Tracking Efficiency: #mu^{+/-}; True #theta (degrees); Efficiency"));
   heff_muon_mcphi = effcalc(hreco_muon_mcphi, htrue_muon_mcphi, TString("Tracking Efficiency: #mu^{+/-}; True #phi (degrees); Efficiency"));
   heff_muon_mcmom = effcalc(hreco_muon_mcmom, htrue_muon_mcmom, TString("Tracking Efficiency: #mu^{+/-}; True Momentum (GeV); Efficiency"));
   // Pions
   heff_pion_mclen = effcalc(hreco_pion_mclen, htrue_pion_mclen, TString("Tracking Efficiency: #pi^{+/-}; True Track Length (cm); Efficiency"));
   heff_pion_mctheta = effcalc(hreco_pion_mctheta, htrue_pion_mctheta, TString("Tracking Efficiency: #pi^{+/-}; True #theta (degrees); Efficiency"));
   heff_pion_mcphi = effcalc(hreco_pion_mcphi, htrue_pion_mcphi, TString("Tracking Efficiency: #pi^{+/-}; True #phi (degrees); Efficiency"));
   heff_pion_mcmom = effcalc(hreco_pion_mcmom, htrue_pion_mcmom, TString("Tracking Efficiency: #pi^{+/-}; True Momentum (GeV); Efficiency"));
   // Kaons
   heff_kaon_mclen = effcalc(hreco_kaon_mclen, htrue_kaon_mclen, TString("Tracking Efficiency: K^{+/-}; True Track Length (cm); Efficiency"));
   heff_kaon_mctheta = effcalc(hreco_kaon_mctheta, htrue_kaon_mctheta, TString("Tracking Efficiency: K^{+/-}; True #theta (degrees); Efficiency"));
   heff_kaon_mcphi = effcalc(hreco_kaon_mcphi, htrue_kaon_mcphi, TString("Tracking Efficiency: K^{+/-}; True #phi (degrees); Efficiency"));
   heff_kaon_mcmom = effcalc(hreco_kaon_mcmom, htrue_kaon_mcmom, TString("Tracking Efficiency: K^{+/-}; True Momentum (GeV); Efficiency"));
   // Protons
   heff_proton_mclen = effcalc(hreco_proton_mclen, htrue_proton_mclen, TString("Tracking Efficiency: p; True Track Length (cm); Efficiency"));
   heff_proton_mctheta = effcalc(hreco_proton_mctheta, htrue_proton_mctheta, TString("Tracking Efficiency: p; True #theta (degrees); Efficiency"));
   heff_proton_mcphi = effcalc(hreco_proton_mcphi, htrue_proton_mcphi, TString("Tracking Efficiency: p; True #phi (degrees); Efficiency"));
   heff_proton_mcmom = effcalc(hreco_proton_mcmom, htrue_proton_mcmom, TString("Tracking Efficiency: p; True Momentum (GeV); Efficiency"));



   // ----- Now put the plots into a vector to be saved ---- //

   // Only make reduced set of plots by default ("short" mode)
   // Also save comments for each plot (must be in order and in line with plots vector)
   // These comments will appear on the CI dashboard next to the plot

   hvector.push_back(*hresstart);
   comments.push_back("Distance between true track start position and reco track start position. Should peak at 0. Width tells you about the resolution, sign tells you whether the difference vector from the true start to reco start is aligned with (+ve) or against (-ve) the true track direction.");
   hvector.push_back(*hresend);
   comments.push_back("Distance between true track end position and reco track end position. Should peak at 0. Width tells you about the resolution, sign tells you whether the difference vector from the true start to reco start is aligned with (+ve) or against (-ve) the true track direction.");
   hvector.push_back(*heff_mcmom);
   comments.push_back("Efficiency for reconstruction charged particle tracks in which the true start position is inside a fiducial volume (10 cm from the edge of the TPC active volume in x and z, 20 cm from the edge of the TPC active volume in y), as a function of true particle momentum. Only reco tracks with purity and completeness greater than 51% are considered, to avoid double-counting with broken tracks.");
   hvector.push_back(*htrkpurity);
   comments.push_back("Track purity, constructed from hits. Should peak at 1.");
   hvector.push_back(*htrkcompleteness);
   comments.push_back("Track completeness, constructed from hits. Should peak at 1.");
   TCanvas *c5 = new TCanvas();
   hnmatchedtracks->Draw("colz");
   //c5->SetLogz();
   //c5->Print("hnmatchedtracks2d.png");
   hvector.push_back(*hnmatchedtracks);
   comments.push_back("Number of reco tracks matched to a single geant track, for true charged pions, kaons, muons, and protons. Gives some information about numbers of unmatched/broken tracks.");
   // Note: for now, nuvtxx/nuvtxy/nuvtxz are only available in analysistree from pandoraNu
   // So only make these plots for pandoraNu!
   // Also do pandora for consolidated output (I think this will work...)
   if (tracking_algorithm == "pandoraNu" || tracking_algorithm == "pandora"){
     hvector.push_back(*hvertres);
     comments.push_back("Distance between true vertex position and reconstructed vertex position. In theory should peak at 0, but usually we see the peak is actually in the second bin (0.5-1 cm). This is nothing to worry about. Width tells you about the resolution.");
   }
   if (short_long == "long") { // Long mode = full set of plots
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
     hvector.push_back(*heff_mctheta);
     hvector.push_back(*hreco_mctheta);
     hvector.push_back(*htrue_mctheta);
     hvector.push_back(*heff_mcphi);
     hvector.push_back(*hreco_mcphi);
     hvector.push_back(*htrue_mcphi);
     hvector.push_back(*heff_mclen);
     hvector.push_back(*hreco_mclen);
     hvector.push_back(*htrue_mclen);
     hvector.push_back(*hreco_mcmom);
     hvector.push_back(*htrue_mcmom);
     hvector.push_back(*heff_muon_mctheta);
     hvector.push_back(*hreco_muon_mctheta);
     hvector.push_back(*htrue_muon_mctheta);
     hvector.push_back(*heff_muon_mcphi);
     hvector.push_back(*hreco_muon_mcphi);
     hvector.push_back(*htrue_muon_mcphi);
     hvector.push_back(*heff_muon_mclen);
     hvector.push_back(*hreco_muon_mclen);
     hvector.push_back(*htrue_muon_mclen);
     hvector.push_back(*heff_muon_mcmom);
     hvector.push_back(*hreco_muon_mcmom);
     hvector.push_back(*htrue_muon_mcmom);
     hvector.push_back(*heff_pion_mctheta);
     hvector.push_back(*hreco_pion_mctheta);
     hvector.push_back(*htrue_pion_mctheta);
     hvector.push_back(*heff_pion_mcphi);
     hvector.push_back(*hreco_pion_mcphi);
     hvector.push_back(*htrue_pion_mcphi);
     hvector.push_back(*heff_pion_mclen);
     hvector.push_back(*hreco_pion_mclen);
     hvector.push_back(*htrue_pion_mclen);
     hvector.push_back(*heff_pion_mcmom);
     hvector.push_back(*hreco_pion_mcmom);
     hvector.push_back(*htrue_pion_mcmom);
     hvector.push_back(*heff_kaon_mctheta);
     hvector.push_back(*hreco_kaon_mctheta);
     hvector.push_back(*htrue_kaon_mctheta);
     hvector.push_back(*heff_kaon_mcphi);
     hvector.push_back(*hreco_kaon_mcphi);
     hvector.push_back(*htrue_kaon_mcphi);
     hvector.push_back(*heff_kaon_mclen);
     hvector.push_back(*hreco_kaon_mclen);
     hvector.push_back(*htrue_kaon_mclen);
     hvector.push_back(*heff_kaon_mcmom);
     hvector.push_back(*hreco_kaon_mcmom);
     hvector.push_back(*htrue_kaon_mcmom);
     hvector.push_back(*heff_proton_mctheta);
     hvector.push_back(*hreco_proton_mctheta);
     hvector.push_back(*htrue_proton_mctheta);
     hvector.push_back(*heff_proton_mcphi);
     hvector.push_back(*hreco_proton_mcphi);
     hvector.push_back(*htrue_proton_mcphi);
     hvector.push_back(*heff_proton_mclen);
     hvector.push_back(*hreco_proton_mclen);
     hvector.push_back(*htrue_proton_mclen);
     hvector.push_back(*heff_proton_mcmom);
     hvector.push_back(*hreco_proton_mcmom);
     hvector.push_back(*htrue_proton_mcmom);
     // Note: for now, nuvtxx/nuvtxy/nuvtxz are only available in analysistree from pandoraNu
     // So only make these plots for pandoraNu!
     // Also do pandora for consolidated output (I think this will work...)
     if (tracking_algorithm == "pandoraNu" || tracking_algorithm == "pandora"){
       hvector.push_back(*hvertresx);
       hvector.push_back(*hvertresy);
       hvector.push_back(*hvertresz);
       hvector.push_back(*hvertdist);
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

  for (unsigned i=0; i<hvector.size(); i++) {
    TCanvas c1;
    hvector[i].SetLineWidth(2);
    hvector[i].Sumw2();
    double integral = hvector[i].Integral();
    //hvector[i].Scale(1.0/integral);
    hvector[i].Draw("hist e0");
    outfile.cd();
    hvector[i].Write();

    std::string plotname = string(hvector[i].GetName()).substr(0, string(hvector[i].GetName()).size() - tag.size() -1 );
      std::string outname = string("MCplots_" + plotname + "_" + tag + "_" + algorithm + ".png");
    c1.Print(outname.c_str(),"png");
  }
  outfile.Close();
}

// ------- Function to draw comparison histograms -------- //

void DrawComparison( std::vector<TH1D> vector1, std::vector<TH1D> vector2, std::string tag1, std::string tag2, std::string algorithm, std::vector<std::string> comments ) {

	if (vector1.size() != vector2.size() ) { std::cout << "[ERROR] Different size in vec1 and vec2. " << std::endl; exit(-1); }
	if (vector1.size()+vector2.size() != comments.size() ){ std::cout << "[WARNING] vector1+vector2 size != comments size. Comments files may not line up with plots. " << std::endl
									  << "        vector1 size = " << vector1.size() << ", vector2 size = " << vector2.size() << ", comments size = " << comments.size() << std::endl; }


	std::string outroot = "MCcomparison_" + tag1 + "_" + tag2 + "_" + algorithm + ".root";
	TFile outfile (outroot.c_str(), "recreate");

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
	std::string plotname = string(vector1[i].GetName()).substr(0, string(vector1[i].GetName()).size() - tag1.size() -1 );
	c1.SetName(plotname.c_str());
	c1.SetTitle(plotname.c_str());

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

	// Print all chisq to file
	std::ofstream ChisqFile;
	ChisqFile.open("ChisqValues.txt", std::ios_base::app);
	ChisqFile << c1.GetName() << "_" << algorithm << " " << chisqv/double(nBins) << "\n";
	ChisqFile.close();

	// If chisq is large, print plot name to a different file
	if (chisqv/(double)nBins >= chisqNotifierCut/100.0){
	  std::ofstream highChisqFile;
	  highChisqFile.open("highChisqPlots.txt", std::ios_base::app);
	  highChisqFile << c1.GetName() << " (" << algorithm << "): chisq = " << chisqv/(double)nBins << "\n";
	  highChisqFile.close();

		// If chisq is large, change background colour of canvas to make it really obvious
		c1.SetFillColor(kOrange-2);
	}

	// Make legend
	TLegend *legend = new TLegend(0.55, 0.68, 0.89, 0.89);
        legend->AddEntry( vector1[i].GetName(), tag1.c_str(),"l");
        legend->AddEntry( vector2[i].GetName(), tag2.c_str(),"l");
	legend->AddEntry((TObject*)0, chisq, "");
	legend->AddEntry((TObject*)0, NDF, "");
	legend->AddEntry((TObject*)0, chisqNDFstr, "");
	// legend->SetLineWidth(0);
  legend->SetFillColor(c1.GetFillColor());
	legend->Draw();

	outfile.cd();
	c1.Write();

	std::string outname = string("MCcomparison_" + plotname + "_"  + tag1 + "_" + tag2 + "_" + algorithm + ".png");
	c1.Print(outname.c_str(),"png");

	// Make comments file
	// Actually only uses the comments set for vector1 (they should be identical for vector2)
	if (i < comments.size()){
	  std::ofstream commentsfile;
	  std::string commentsfilename = string("MCcomparison_" + plotname + "_"  + tag1 + "_" + tag2 + "_" + algorithm + ".comment");
	  commentsfile.open(commentsfilename.c_str(), std::ios_base::app);
	  //commentsfile << comments[i] << "\n";
	  textWrap(comments[i],commentsfile,70);
	  commentsfile.close();
	  }
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

	std::vector<std::string> algorithm = { "pandora" };
	if ( short_long == "long" ) {
	        algorithm.push_back ( "pandoraNu" );
	        algorithm.push_back ( "pandoraCosmic" );
		algorithm.push_back ( "pandoraNuKHit" );
		algorithm.push_back ( "pandoraCosmicKHit" );
		algorithm.push_back ( "pandoraNuKalmanTrack" );
		}

	// Vector of strings to save comments for CI dashboard
	// These comments will be displayed alongside plots to give shifters information about the plots
	std::vector<std::string> comments;

	for (unsigned algorithms = 0; algorithms < algorithm.size(); algorithms++) {
	  std::vector<TH1D> vector1;
	  FillPlots_MC ( tree1, vector1, algorithm[ algorithms ], tag1, short_long, comments );


	  // In "long" mode, draw both sets of histograms separately as well as the comparison
	  // Also do this if you're not doing a comparison
	  if (short_long == "long" || !comparison){
	    DrawHistos( vector1, tag1, algorithm[ algorithms ]);
	  }

	  if (!comparison) continue;

	  std::vector<TH1D> vector2;
	  file2->cd();
	  FillPlots_MC ( tree2, vector2, algorithm[ algorithms ], tag2, short_long, comments );
	  // In "long" mode, draw both sets of histograms separately as well as the comparison
	  if (short_long == "long"){
	    DrawHistos( vector2, tag2, algorithm[ algorithms ] );
	  }

	  DrawComparison( vector1, vector2, tag1, tag2, algorithm[ algorithms ], comments );

	}

	return 0;

}
