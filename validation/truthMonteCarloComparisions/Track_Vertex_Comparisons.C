#include <iostream>
#include <fstream>
#include <string>
#include <algorithm>
#include "TH1.h"
#include "TTree.h"
#include "TFile.h"
#include "TCanvas.h"
#include "TLegend.h"
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

void TrackComparisons_MC( TTree* tree, std::vector<TH1D> &hvector, std::string tracking_algorithm, std::string version, std::string short_long ) {

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
   Float_t         trkmommschi2[kMaxTracks];
   Float_t         trkmommsllhd[kMaxTracks];
   Float_t	   trkpidpida[kMaxTracks][3];
   Short_t         trkpidbestplane[kMaxTracks];

   const int kMaxVertices = 100;
   Short_t         nnuvtx;
   Float_t         nuvtxx[kMaxVertices];
   Float_t         nuvtxy[kMaxVertices];
   Float_t         nuvtxz[kMaxVertices];

   const int kMaxGeant = 5000;
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

   const int maxtruth = 10;
   Int_t           mcevts_truth;               //number of neutrino interactions in the spill
   Float_t         nuvtxx_truth[maxtruth];    //neutrino vertex x in cm
   Float_t         nuvtxy_truth[maxtruth];    //neutrino vertex y in cm
   Float_t         nuvtxz_truth[maxtruth];    //neutrino vertex z in cm

   const int maxgenie = 70;
   Int_t           genie_no_primaries; 
   Int_t           genie_primaries_pdg[maxgenie];
   Int_t           genie_status_code[maxgenie];

   std::string branch_name = "ntracks_" + tracking_algorithm;
   tree -> SetBranchAddress(branch_name.c_str(), &ntracks);
   branch_name = "trkstartx_" + tracking_algorithm;
   tree -> SetBranchAddress(branch_name.c_str(), trkstartx);
   branch_name = "trkendx_" + tracking_algorithm;
   tree -> SetBranchAddress(branch_name.c_str(), trkendx);
   branch_name = "trkstarty_" + tracking_algorithm;
   tree -> SetBranchAddress(branch_name.c_str(), trkstarty);
   branch_name = "trkendy_" + tracking_algorithm;
   tree -> SetBranchAddress(branch_name.c_str(), trkendy);
   branch_name = "trkstartz_" + tracking_algorithm;
   tree -> SetBranchAddress(branch_name.c_str(), trkstartz);
   branch_name = "trkendz_" + tracking_algorithm;
   tree -> SetBranchAddress(branch_name.c_str(), trkendz);
   branch_name = "trklen_" + tracking_algorithm;
   tree -> SetBranchAddress(branch_name.c_str(), trklength);
   branch_name = "trkg4id_" + tracking_algorithm;
   tree -> SetBranchAddress(branch_name.c_str(), trkg4id);
   branch_name = "trkmomrange_" + tracking_algorithm;
   tree -> SetBranchAddress(branch_name.c_str(), trkmomrange);
   branch_name = "trkmommschi2_" + tracking_algorithm;
   tree -> SetBranchAddress(branch_name.c_str(), trkmommschi2);
   branch_name = "trkmommsllhd_" + tracking_algorithm;
   tree -> SetBranchAddress(branch_name.c_str(), trkmommsllhd);
   branch_name = "trkpidpida_" + tracking_algorithm;
   tree -> SetBranchAddress(branch_name.c_str(), trkpidpida);
   branch_name = "trkpidbestplane_" + tracking_algorithm;
   tree -> SetBranchAddress(branch_name.c_str(), trkpidbestplane);
   
   tree -> SetBranchAddress("geant_list_size", &geant_list_size);
   tree -> SetBranchAddress("TrackId", TrackId);
   if (version == "mcc7" || version == "MCC7") {
   tree -> SetBranchAddress("StartPointx_tpcAV", StartX);
   tree -> SetBranchAddress("StartPointy_tpcAV", StartY);
   tree -> SetBranchAddress("StartPointz_tpcAV", StartZ);
   tree -> SetBranchAddress("EndPointx_tpcAV", EndX);
   tree -> SetBranchAddress("EndPointy_tpcAV", EndY);
   tree -> SetBranchAddress("EndPointz_tpcAV", EndZ);
   tree -> SetBranchAddress("StartPointx", real_StartX);
   tree -> SetBranchAddress("StartPointx", real_StartX_nosc);
   tree -> SetBranchAddress("StartPointy", real_StartY);
   tree -> SetBranchAddress("StartPointz", real_StartZ);
   tree -> SetBranchAddress("EndPointx", real_EndX);
   tree -> SetBranchAddress("EndPointy", real_EndY);
   tree -> SetBranchAddress("EndPointz", real_EndZ);
   tree -> SetBranchAddress("nuvtxx_truth", nuvtxx_truth);
   tree -> SetBranchAddress("nuvtxy_truth", nuvtxy_truth);
   tree -> SetBranchAddress("nuvtxz_truth", nuvtxz_truth);
   tree -> SetBranchAddress("nnuvtx", &nnuvtx);
   tree -> SetBranchAddress("nuvtxx", nuvtxx);
   tree -> SetBranchAddress("nuvtxy", nuvtxy);
   tree -> SetBranchAddress("nuvtxz", nuvtxz);
   } else {
   tree -> SetBranchAddress("sp_charge_corrected_StartPointx_tpcAV", StartX);
   tree -> SetBranchAddress("sp_charge_corrected_StartPointy_tpcAV", StartY);
   tree -> SetBranchAddress("sp_charge_corrected_StartPointz_tpcAV", StartZ);
   tree -> SetBranchAddress("sp_charge_corrected_EndPointx_tpcAV", EndX);
   tree -> SetBranchAddress("sp_charge_corrected_EndPointy_tpcAV", EndY);
   tree -> SetBranchAddress("sp_charge_corrected_EndPointz_tpcAV", EndZ);
   tree -> SetBranchAddress("sp_charge_corrected_StartPointx", real_StartX);
   tree -> SetBranchAddress("StartPointx", real_StartX_nosc);
   tree -> SetBranchAddress("sp_charge_corrected_StartPointy", real_StartY);
   tree -> SetBranchAddress("sp_charge_corrected_StartPointz", real_StartZ);
   tree -> SetBranchAddress("sp_charge_corrected_EndPointx", real_EndX);
   tree -> SetBranchAddress("sp_charge_corrected_EndPointy", real_EndY);
   tree -> SetBranchAddress("sp_charge_corrected_EndPointz", real_EndZ);
   tree -> SetBranchAddress("sp_charge_corrected_nuvtxx_truth", nuvtxx_truth);
   tree -> SetBranchAddress("sp_charge_corrected_nuvtxy_truth", nuvtxy_truth);
   tree -> SetBranchAddress("sp_charge_corrected_nuvtxz_truth", nuvtxz_truth);
   branch_name = "nnuvtx_" + tracking_algorithm;
   tree -> SetBranchAddress(branch_name.c_str(), &nnuvtx);
   branch_name = "nuvtxx_" + tracking_algorithm;
   tree -> SetBranchAddress(branch_name.c_str(), &nuvtxx);
   branch_name = "nuvtxy_" + tracking_algorithm;
   tree -> SetBranchAddress(branch_name.c_str(), &nuvtxy);
   branch_name = "nuvtxz_" + tracking_algorithm;
   tree -> SetBranchAddress(branch_name.c_str(), &nuvtxz);
   }
   tree -> SetBranchAddress("mcevts_truth", &mcevts_truth);
   tree -> SetBranchAddress("origin", origin);
   tree -> SetBranchAddress("pdg", pdg);
   tree -> SetBranchAddress("pathlen_drifted", pathlen);
   tree -> SetBranchAddress("P", P);
   //tree -> SetBranchAddress("Px", Px);
   //tree -> SetBranchAddress("Py", Py);
   //tree -> SetBranchAddress("Pz", Pz);
   tree -> SetBranchAddress("status", status);
   tree -> SetBranchAddress("Mother", Mother);
   tree -> SetBranchAddress("genie_no_primaries", &genie_no_primaries); 
   tree -> SetBranchAddress("genie_primaries_pdg", genie_primaries_pdg);
   tree -> SetBranchAddress("genie_status_code", genie_status_code);

   long Size = tree -> GetEntries();
   cout << "Number of events in the tree is: " << Size << endl;

   std::string histoname = "hnreco_" + version;
   TH1D *hnreco = new TH1D(histoname.c_str(), "Number of reco tracks; Number of reco tracks;", 20, 0, 20);
   histoname = "hntrue_" + version;
   TH1D *hntrue = new TH1D(histoname.c_str(), "Number of true primary tracks per event; # True tracks;", 50, 0, 50);
   histoname = "hstartx_" + version;
   TH1D *hstartx = new TH1D(histoname.c_str(), "Track start X position; x [cm];", 100, -200, 500);
   histoname = "hstartx_true_" + version;
   TH1D *hstartx_true = new TH1D(histoname.c_str(), "Track start X position (true); x [cm];", 100, -200, 500);
   histoname = "hstartx_true_nosc_" + version;
   TH1D *hstartx_true_nosc = new TH1D(histoname.c_str(), "Track start X position (true, no space charge correction); x [cm];", 100, -200, 500);
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
   TH1D *hlreco = new TH1D(histoname.c_str(), "Track length Reco; l [cm];", 100, 0, 1000);
   histoname = "hlrange_" + version;
   TH1D *hlrange = new TH1D(histoname.c_str(), "Track length Range; l [cm];", 100, 0, 1000);
   histoname = "hlmc_" + version;
   TH1D *hlmc = new TH1D(histoname.c_str(), "Track length True; l [cm];", 100, 0, 1000);
   histoname = "hlrangemc_" + version;
   TH1D *hlrangemc = new TH1D(histoname.c_str(), "Track length Range True; l [cm];", 100, 0, 1000);
   histoname = "hldiff_" + version;
   TH1D *hldiff = new TH1D(histoname.c_str(), "Track length - Track range (Reco); l [cm];", 200, -100, 100);
   histoname = "hldiffmc_" + version;
   TH1D *hldiffmc = new TH1D(histoname.c_str(), "Track length - Track range (True); l [cm];", 200, -100, 100);
   histoname = "hlres_" + version;
   TH1D *hlres = new TH1D(histoname.c_str(), "Track length reco - Track length MC; l [cm];", 100, -50, 50);
   histoname = "hlresrange_" + version;
   TH1D *hlresrange = new TH1D(histoname.c_str(), "Track length range reco - track length range MC; l [cm];", 100, -50, 50);
   histoname = "hresstart_" + version;
   TH1D *hresstart = new TH1D(histoname.c_str(), "Track start resolution; R [cm];", 25, 0, 50);
   histoname = "hresend_" + version;
   TH1D *hresend = new TH1D(histoname.c_str(), "Track end resolution; R [cm];", 25, 0, 50);
   histoname = "hresostartx_" + version;
   TH1D *hresostartx = new TH1D(histoname.c_str(),"Startx reco - Startx MC; R [cm];", 2000, -20, 20); 
   histoname = "hresostarty_" + version;
   TH1D *hresostarty = new TH1D(histoname.c_str(),"Starty reco - Starty MC; R [cm];", 2000, -20, 20); 
   histoname = "hresostartz_" + version;
   TH1D *hresostartz = new TH1D(histoname.c_str(),"Startz reco - Startz MC; R [cm];", 2000, -20, 20); 
   histoname = "hresoendx_" + version;
   TH1D *hresoendx = new TH1D(histoname.c_str(),"Endx reco - Endx MC; R [cm];", 2000, -20, 20); 
   histoname = "hresoendy_" + version;
   TH1D *hresoendy = new TH1D(histoname.c_str(),"Endy reco - Endy MC; R [cm];", 2000, -20, 20); 
   histoname = "hresoendz_" + version;
   TH1D *hresoendz = new TH1D(histoname.c_str(),"Endz reco - endz MC; R [cm];", 2000, -20, 20); 
   histoname = "hresomomentum_range_" + version;
   TH1D *hresomom_range = new TH1D(histoname.c_str(),"Momentum from range - momentum from MC; P [GeV/c];", 2000, -1, 1); 
   histoname = "hresomomentum_chi2_" + version;
   TH1D *hresomom_chi2 = new TH1D(histoname.c_str(),"Momentum from Chi2 MCS - momentum from MC; P [GeV/c];", 2000, -2, 2); 
   histoname = "hresomomentum_llhd_" + version;
   TH1D *hresomom_llhd = new TH1D(histoname.c_str(),"Momentum from LLHD MCS - momentum from MC; P [GeV/c];", 2000, -2, 2); 
   histoname = "hresomomentum_contained_chi2_" + version;
   TH1D *hresomom_contained_chi2 = new TH1D(histoname.c_str(),"Momentum from Chi2 MCS - momentum from MC for contained tracks; P [GeV/c];", 2000, -2, 2); 
   histoname = "hresomomentum__contained_llhd_" + version;
   TH1D *hresomom_contained_llhd = new TH1D(histoname.c_str(),"Momentum from LLHD MCS - momentum from MC for contained tracks; P [GeV/c];", 2000, -2, 2); 
   histoname = "hpidpida_total_" + version;
   TH1D *hpidpida_total = new TH1D(histoname.c_str(),"PIDA for all reco tracks; PIDA;", 100, 0, 30); 
   histoname = "hpidpida_muon_" + version;
   TH1D *hpidpida_muon = new TH1D(histoname.c_str(),"PIDA for all reco muons; PIDA;", 100, 0, 30);  
   histoname = "hvertres_" + version;
   TH1D *hvertres = new TH1D(histoname.c_str(),"Vertex resolution; Vertex position - true vertex (cm);", 50, 0, 20); 
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
       
   int mutrue = 0;
   double d = 0;
   double dmc = 0;
   double d1 = 0;
   double d2 = 0;
  
   for(long i = 0; i < Size; i++) {
   if (i!=0 && i%1000==0) std:: cout << "Processing " << i << "/" << Size << std::endl;
      tree -> GetEntry(i);


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

			if (real_StartX[j]>0 && real_StartX[j]<256.35){
			  hstartx_true -> Fill(real_StartX[j]);
			  hstartx_true_nosc -> Fill(real_StartX_nosc[i]);
			}
		 	
			//if ( inFV( real_StartX[j], real_StartY[j], real_StartZ[j] ) && inFV( real_EndX[j], real_EndY[j], real_EndZ[j] ) ) { //contained tracks
			if ( inFV( trkstartx[recoTracks], trkstarty[recoTracks], trkstartz[recoTracks] ) && inFV( trkendx[recoTracks], trkendy[recoTracks], trkendz[recoTracks] ) ) { //contained tracks
			hresomom_range-> Fill( trkmomrange[recoTracks] - P[j] );
			hresomom_contained_chi2-> Fill( trkmommschi2[recoTracks] - P[j] );
			hresomom_contained_llhd-> Fill( trkmommsllhd[recoTracks] - P[j] );
			}

			hresomom_chi2-> Fill( trkmommschi2[recoTracks] - P[j] );
			hresomom_llhd-> Fill( trkmommsllhd[recoTracks] - P[j] );

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
               	}
               } //end loop on MC particles
      		is_first=false;
            } //end loop on reco tracks
      	hntrue -> Fill(mutrue);

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

   // Only make reduced set of plots for CI
   hvector.push_back(*hresstart);
   hvector.push_back(*hresend);
   hvector.push_back(*hvertres);
   hvector.push_back(*hnprotons);
   if (short_long == "long") { // Full set of plots 
     hvector.push_back(*hnreco);
     hvector.push_back(*hstartx);
     hvector.push_back(*hstartx_true);
     hvector.push_back(*hstartx_true_nosc);
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
     hvector.push_back(*hresomom_chi2);
     hvector.push_back(*hresomom_llhd);
     hvector.push_back(*hresomom_contained_chi2);
     hvector.push_back(*hresomom_contained_llhd);
     hvector.push_back(*hpidpida_total);
     hvector.push_back(*hvertresx);
     hvector.push_back(*hvertresy);
     hvector.push_back(*hvertresz);
     hvector.push_back(*hvertdist);
     hvector.push_back(*hlrange);
     hvector.push_back(*hlresrange);
     hvector.push_back(*hlrangemc);
     hvector.push_back(*hntrue);
     hvector.push_back(*hpidpida_muon);
   }
   
   } //end function

double calculateChiSqDistance(TH1D O, TH1D E){

    double chisq = 0;
    for (int i = 1; i < O.GetNbinsX()+1; i++){

        double O_i = O.GetBinContent(i);
        double E_i = E.GetBinContent(i);
        double O_ierr = O.GetBinError(i);
        double E_ierr = E.GetBinError(i);

        if (O_i == 0 && E_i == 0){
            chisq += 0;
        }
        else{
            chisq += std::pow(O_i - E_i,2)/(std::sqrt(std::pow(O_ierr,2) + std::pow(E_ierr,2)));
        }

    }

    return chisq;

}
   
void DrawHistos ( std::vector<TH1D> hvector , std::string tag, std::string algorithm ) {
  std::string outroot = "MCcomparison_" + tag + "_" + algorithm + ".root";
  TFile outfile (outroot.c_str(), "recreate");

  std::string outname = string("MCplots_" + tag + "_" + algorithm + ".pdf");

  for (unsigned i=0; i<hvector.size(); i++) {
    TCanvas c1;
    hvector[i].SetLineWidth(2);
    hvector[i].Sumw2();
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
	vector1[i].DrawNormalized("hist e0");
	vector2[i].SetLineWidth(2);
	vector2[i].SetLineColor(2);
	vector2[i].SetStats(0);
	vector2[i].Sumw2();
	vector2[i].DrawNormalized("hist e0 same");
	c1.SetName( string(vector1[i].GetName()).substr(0, string(vector1[i].GetName()).size() - tag1.size() -1 ).c_str() );
	c1.SetTitle( string(vector1[i].GetName()).substr(0, string(vector1[i].GetName()).size() - tag1.size() -1).c_str() );

	// Calculate chi2 between two plots and put in format for legend
	double chisqv = calculateChiSqDistance(vector1[i], vector2[i]);
	TString chisq = Form("#chi^{2}: %g", chisqv);
	int nBins = std::max(vector1[i].GetNbinsX(), vector2[i].GetNbinsX());
	TString NDF = Form("No. Bins: %i", nBins);
	double chisqNDF = chisqv/(double)nBins;
	TString chisqNDFstr = Form("#chi^{2}/No. bins: %g", chisqNDF);

	// If chisq is large, print to file
	if (chisqNDF >= chisqNotifierCut/100.0){
	  std::ofstream highChisqFile;
	  highChisqFile.open("highChisqPlots.txt", std::ios_base::app);
	  highChisqFile << c1.GetName() << " (" << algorithm << ")" <<  "\n";
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
		std::cout << "Notifying about any comparison plots with chi2/no. bins > " << chisqNotifierCut/100.0 << std::endl;
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

	std::vector<std::string> algorithm = { "pandoraNu" , "pandoraCosmic" };
	if ( short_long == "long" ) {
		algorithm.push_back ( "pandoraNuKHit" );
		algorithm.push_back ( "pandoraCosmicKHit" );
		algorithm.push_back ( "pandoraNuKalmanTrack" );
	}

	for (unsigned algorithms = 0; algorithms < algorithm.size(); algorithms++) {
	  std::vector<TH1D> vector1;
	  TrackComparisons_MC ( tree1, vector1, algorithm[ algorithms ], tag1, short_long );
	  // In "long" mode, draw both sets of histograms separately as well as the comparison
	  // Also do this if you're not doing a comparison
	  if (short_long == "long" || !comparison){
	    DrawHistos( vector1, tag1, algorithm[ algorithms ]);
	  }
	  
	  if (!comparison) continue;
	  
	  std::vector<TH1D> vector2;
	  file2->cd();
	  TrackComparisons_MC ( tree2, vector2, algorithm[ algorithms ], tag2, short_long );
	  // In "long" mode, draw both sets of histograms separately as well as the comparison
	  if (short_long == "long"){ 
	    DrawHistos( vector2, tag2, algorithm[ algorithms ] );
	  }
	  
	  DrawComparison( vector1, vector2, tag1, tag2, algorithm[ algorithms ] );
	  
	}

	return 0;

}
