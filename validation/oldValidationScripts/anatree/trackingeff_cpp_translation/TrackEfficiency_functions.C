// This file contains functions used in main TrackEfficiency code






// ------- Function to generate efficiency histograms from reco/true histograms -------- //

TH1F* effcalc(TH1F* hreco, TH1F* htrue, TString label){
  // Check that reco and true histograms have the same binning (well - same number of bins...)
  assert(hreco->GetNbinsX() == htrue->GetNbinsX());

  // Make a new histogram to store efficiencies
  TH1F *heff = (TH1F*)(hreco->Clone());
  heff->Reset();
  heff->SetTitle(label);

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














// ------------- Function to generate efficiecny histograms for a single tree --------------- //

std::vector<TH1F*> MakeEffPlots(TString infile, std::vector< std::string > algoNames, TString short_long)
{
  TChain *fChain = new TChain("analysistree/anatree");
  fChain->Add(infile);

  // Understand which algorithms we want to make plots for
  const int kMaxAlgos = 8; // For defining arrays to read out tree
  int n_algos = algoNames.size();
  if (n_algos > kMaxAlgos){
	std::cerr << "[ERROR] n_algos = " << n_algos << ", greater than kMaxAlgos (" << kMaxAlgos << "). Fix this and run again!" << std::endl;
	throw;
  }

  std::cout << "Computing tracking efficiencies for: " << std::endl;
  for (int i=0; i<n_algos; i++){
    std::cout << algoNames[i] << std::endl;
  }


  // Define variables to read from tree
  const int kMaxGeantList = 10000;
  
  int geant_list_size;
  int pdg[kMaxGeantList];
  int inTPCActive[kMaxGeantList];
  float Eng[kMaxGeantList];
  float Mass[kMaxGeantList];
  float pathlen[kMaxGeantList];
  float theta[kMaxGeantList];
  float phi[kMaxGeantList];
  float theta_xz[kMaxGeantList];
  float theta_yz[kMaxGeantList];
  float P[kMaxGeantList];
  float Px[kMaxGeantList];
  float Py[kMaxGeantList];
  float Pz[kMaxGeantList];
  float StartPointx_tpcAV[kMaxGeantList];
  float StartPointy_tpcAV[kMaxGeantList];
  float StartPointz_tpcAV[kMaxGeantList];
  float EndPointx_tpcAV[kMaxGeantList];
  float EndPointy_tpcAV[kMaxGeantList];
  float EndPointz_tpcAV[kMaxGeantList];

  const int kMaxTracks = 5000;
  
  int ntracks_array[kMaxAlgos];
  float trkstartx_array[kMaxAlgos][kMaxTracks];
  float trkstarty_array[kMaxAlgos][kMaxTracks];
  float trkstartz_array[kMaxAlgos][kMaxTracks];
  float trkendx_array[kMaxAlgos][kMaxTracks];
  float trkendy_array[kMaxAlgos][kMaxTracks];
  float trkendz_array[kMaxAlgos][kMaxTracks];
  float trkstartdcosx_array[kMaxAlgos][kMaxTracks];
  float trkstartdcosy_array[kMaxAlgos][kMaxTracks];
  float trkstartdcosz_array[kMaxAlgos][kMaxTracks];
  float trkenddcosx_array[kMaxAlgos][kMaxTracks];
  float trkenddcosy_array[kMaxAlgos][kMaxTracks];
  float trkenddcosz_array[kMaxAlgos][kMaxTracks];
  float trklen_array[kMaxAlgos][kMaxTracks];
  
  // Now set which branches of the TChain we want to read out
  fChain->SetBranchStatus("*",0);
  fChain->SetBranchStatus("geant_list_size",1); 
  fChain->SetBranchStatus("pdg",1);   
  fChain->SetBranchStatus("inTPCActive",1);
  fChain->SetBranchStatus("Eng",1);
  fChain->SetBranchStatus("StartPoint*",1);
  fChain->SetBranchStatus("EndPoint*",1);
  fChain->SetBranchStatus("thet*",1);
  fChain->SetBranchStatus("phi",1);
  fChain->SetBranchStatus("pathlen",1);
  fChain->SetBranchStatus("P",1);
  fChain->SetBranchStatus("Mass",1);
  fChain->SetBranchStatus("Px",1);
  fChain->SetBranchStatus("Py",1);
  fChain->SetBranchStatus("Pz",1);
  fChain->SetBranchStatus("ntracks_*",1);
  fChain->SetBranchStatus("trkstart*",1);
  fChain->SetBranchStatus("trkend*",1);
  fChain->SetBranchStatus("trklen*",1);

  // Set branch addresses
  fChain->SetBranchAddress("geant_list_size",&geant_list_size);  
  fChain->SetBranchAddress("pdg",&pdg);
  fChain->SetBranchAddress("inTPCActive",&inTPCActive);
  fChain->SetBranchAddress("Eng",&Eng);
  fChain->SetBranchAddress("Mass",&Mass);
  fChain->SetBranchAddress("pathlen",&pathlen);
  fChain->SetBranchAddress("theta",&theta);
  fChain->SetBranchAddress("phi",&phi);
  fChain->SetBranchAddress("theta_xz",&theta_xz);
  fChain->SetBranchAddress("theta_yz",&theta_yz);
  fChain->SetBranchAddress("P",&P);
  fChain->SetBranchAddress("Px",&Px);
  fChain->SetBranchAddress("Py",&Py);
  fChain->SetBranchAddress("Pz",&Pz);
  fChain->SetBranchAddress("StartPointx_tpcAV",&StartPointx_tpcAV);
  fChain->SetBranchAddress("StartPointy_tpcAV",&StartPointy_tpcAV);
  fChain->SetBranchAddress("StartPointz_tpcAV",&StartPointz_tpcAV);
  fChain->SetBranchAddress("EndPointx_tpcAV",&EndPointx_tpcAV);
  fChain->SetBranchAddress("EndPointy_tpcAV",&EndPointy_tpcAV);
  fChain->SetBranchAddress("EndPointz_tpcAV",&EndPointz_tpcAV);
  
  for (int i_alg=0; i_alg<n_algos; i_alg++){
    fChain->SetBranchAddress(TString("ntracks_"+algoNames[i_alg]),&ntracks_array[i_alg]);
    fChain->SetBranchAddress(TString("trkstartx_"+algoNames[i_alg]),&trkstartx_array[i_alg]);
    fChain->SetBranchAddress(TString("trkstarty_"+algoNames[i_alg]),&trkstarty_array[i_alg]);
    fChain->SetBranchAddress(TString("trkstartz_"+algoNames[i_alg]),&trkstartz_array[i_alg]);
    fChain->SetBranchAddress(TString("trkendx_"+algoNames[i_alg]),&trkendx_array[i_alg]);
    fChain->SetBranchAddress(TString("trkendy_"+algoNames[i_alg]),&trkendy_array[i_alg]);
    fChain->SetBranchAddress(TString("trkendz_"+algoNames[i_alg]),&trkendz_array[i_alg]);
    fChain->SetBranchAddress(TString("trkstartdcosx_"+algoNames[i_alg]),&trkstartdcosx_array[i_alg]);
    fChain->SetBranchAddress(TString("trkstartdcosy_"+algoNames[i_alg]),&trkstartdcosy_array[i_alg]);
    fChain->SetBranchAddress(TString("trkstartdcosz_"+algoNames[i_alg]),&trkstartdcosz_array[i_alg]);
    fChain->SetBranchAddress(TString("trkenddcosx_"+algoNames[i_alg]),&trkenddcosx_array[i_alg]);
    fChain->SetBranchAddress(TString("trkenddcosy_"+algoNames[i_alg]),&trkenddcosy_array[i_alg]);
    fChain->SetBranchAddress(TString("trkenddcosz_"+algoNames[i_alg]),&trkenddcosz_array[i_alg]);
    fChain->SetBranchAddress(TString("trklen_"+algoNames[i_alg]),&trklen_array[i_alg]);
    }

  // Define truth histograms
  TH1F *mclen_true = new TH1F("TrueLength","",60,0,1200);
  TH1F *mcpdg_true = new TH1F("TruePDG","",20,0,5000);
  TH1F *mctheta_true = new TH1F("TrueTheta","",20,0,180);
  TH1F *mcphi_true = new TH1F("TruePhi","",20,-180,180);
  TH1F *mcthetaxz_true = new TH1F("TrueThetaXZ","",20,-180,180);
  TH1F *mcthetayz_true = new TH1F("TrueThetaYZ","",20,-180,180);
  TH1F *mcmom_true = new TH1F("TrueMom","",20,0,2.2);

  // Define reco histograms
  TH1F* mclen_reco[n_algos];
  TH1F* mcpdg_reco[n_algos];
  TH1F* mctheta_reco[n_algos];
  TH1F* mcphi_reco[n_algos];
  TH1F* mcthetaxz_reco[n_algos];
  TH1F* mcthetayz_reco[n_algos];
  TH1F* mcmom_reco[n_algos];

  // Define reco histograms for each algorithm
  for (int i_alg = 0; i_alg < n_algos; i_alg++){
    mclen_reco[i_alg] = new TH1F(TString("recomclen_"+algoNames[i_alg]),"",60,0,1200);
    mcpdg_reco[i_alg] = new TH1F(TString("recomcpdg_"+algoNames[i_alg]),"",20,0,500);
    mctheta_reco[i_alg] = new TH1F(TString("recomctheta_"+algoNames[i_alg]),"",20,0,180);
    mcphi_reco[i_alg] = new TH1F(TString("recomcphi_"+algoNames[i_alg]),"",20,-180,180);
    mcthetaxz_reco[i_alg] = new TH1F(TString("recomcthetaxz_"+algoNames[i_alg]),"",20,-180,180);
    mcthetayz_reco[i_alg] = new TH1F(TString("recomcthetayz_"+algoNames[i_alg]),"",20,-180,180);
    mcmom_reco[i_alg] = new TH1F(TString("recomcmom_"+algoNames[i_alg]),"",20,0,2.2);
  }
  
  // Define efficiency histograms
  TH1F* mclen_eff[n_algos];
  TH1F* mcpdg_eff[n_algos];
  TH1F* mctheta_eff[n_algos];
  TH1F* mcphi_eff[n_algos];
  TH1F* mcthetaxz_eff[n_algos];
  TH1F* mcthetayz_eff[n_algos];
  TH1F* mcmom_eff[n_algos];



  // ----------- Now read out events from tree ------------ //
  
  // Loop over entries in tree
  int n_entries = fChain->GetEntries();
  for (int jentry = 0; jentry < n_entries; jentry++){

      // Print out where you are
      if (jentry%1000 == 0) std::cout << jentry << " / " << n_entries << std::endl;

      // Copy next entry into memory and verify
      int nb = fChain->GetEntry(jentry);
      if (nb <= 0){ continue;}

      // If there are more GEANT particles than kMaxGeantList -- complain!
      if (geant_list_size > kMaxGeantList){
	std::cerr << "[ERROR] geant_list_size = " << geant_list_size << ", greater than kMaxGeantList (" << kMaxGeantList << "). Fix this and run again!" << std::endl;
	throw;
      }
      
      // Fill truth histograms (for certain particle types)
      double minKE = 0.05;

      for (int igeant=0; igeant<geant_list_size; igeant++){
	int apdg = abs(pdg[igeant]);
	if (inTPCActive[igeant] == 1){
	  if (apdg == 13 || apdg == 211 || apdg == 321 || apdg == 2212){ // If mu, pi, K+/-, or p
	    if (Eng[igeant]>=0.001*Mass[igeant]+minKE){ // Cuts out small scatter particles, only look at particles that have a decent amount of energy and go a decent length

	      mclen_true->Fill(pathlen[igeant]);
	      mcpdg_true->Fill(pdg[igeant]);
	      mctheta_true->Fill(theta[igeant]*180/3.142);
	      mcphi_true->Fill(phi[igeant]*180/3.142);
	      mcthetaxz_true->Fill(theta_xz[igeant]*180/3.142);
	      mcthetayz_true->Fill(theta_yz[igeant]*180/3.142);
	      mcmom_true->Fill(P[igeant]);
	      
	    }
	  }
	}
      }// Loop over geant particles (igeant)

      // Now loop through reconstruction algorithms and fill reco histograms
      for (int i_alg=0; i_alg<n_algos; i_alg++)
	{
	  int ntracks = (int)ntracks_array[i_alg];

	  // If there are more reconstructed tracks than kMaxTracks -- complain!
	  if (ntracks > kMaxTracks){
	    std::cerr << "[ERROR] ntracks = " << ntracks << ", greater than kMaxTracks (" << kMaxTracks << "). Fix this and run again!" << std::endl;
	    throw;
	  }
	  
	  // Limit at 1000 reconstructed tracks per event
	  if (ntracks > 1000){ ntracks = 1000; }

	  // Loop through reconstructed tracks in the event
	  for (int itrack = 0; itrack < ntracks; itrack++){

	    // Loop through true particles in the track
	    for (int igeant=0; igeant < geant_list_size; igeant++){
	      int apdg = abs(pdg[igeant]);
	      if (inTPCActive[igeant] == 1){
		if (apdg == 13 || apdg == 211 || apdg == 321 || apdg == 2212){ // If mu, pi, K+/-, or p
		  if (Eng[igeant]>=0.001*Mass[igeant]+minKE){ // Cuts out all the small scatter particles etc, only look at particles that have a decent amount of energy and go a decent length

		    // Calculate angle between true and reco track at start and end
		    double num = ((trkstartdcosx_array[i_alg][itrack]*Px[igeant])+(trkstartdcosy_array[i_alg][itrack]*Py[igeant])+(trkstartdcosz_array[i_alg][itrack]*Pz[igeant]));
		    double cosangle = num/P[igeant];
		    if (cosangle > 1){ cosangle = 1.; }
		    if (cosangle < -1){ cosangle = -1; }
		    double angle = TMath::ACos(cosangle)*180.0/TMath::Pi();

		    double onum = ((trkenddcosx_array[i_alg][itrack]*Px[igeant])+(trkenddcosy_array[i_alg][itrack]*Py[igeant])+(trkenddcosz_array[i_alg][itrack]*Pz[igeant]));
		    double cosoangle = onum/P[igeant];
		    if (cosoangle > 1){ cosoangle = 1.; }
		    if (cosoangle < -1){ cosoangle = -1.; }
		    double oangle = TMath::ACos(cosoangle)*180.0/TMath::Pi();

		    if ((abs(angle)<=10) || (abs(180-angle)<=10) || (abs(oangle)<=10) || (abs(180-oangle)<=10)){ // If small angles -- confirms you've got the right track
		      // Do start point matching
		      double mcstartx = StartPointx_tpcAV[igeant];
		      double mcstarty = StartPointy_tpcAV[igeant];
		      double mcstartz = StartPointz_tpcAV[igeant];
		      double mcendx = EndPointx_tpcAV[igeant];
		      double mcendy = EndPointy_tpcAV[igeant];
		      double mcendz = EndPointz_tpcAV[igeant];
		      double trkstartx = trkstartx_array[i_alg][itrack];
		      double trkstarty = trkstarty_array[i_alg][itrack];
		      double trkstartz = trkstartz_array[i_alg][itrack];
		      double trkendx = trkendx_array[i_alg][itrack];
		      double trkendy = trkendy_array[i_alg][itrack];
		      double trkendz = trkendz_array[i_alg][itrack];
		      
		      double pmatch1 = TMath::Sqrt(pow(mcstartx-trkstartx,2)+pow(mcstarty-trkstarty,2)+pow(mcstartz-trkstartz,2));
		      double pmatch2 = TMath::Sqrt(pow(mcstartx-trkendx,2)+pow(mcstarty-trkendy,2)+pow(mcstartz-trkendz,2));
		      double minstart = std::min(pmatch1, pmatch2);

		      if (minstart <= 5) { // If reco track starts or ends within 5cm of true start/end -- confirms you've got the right track
			//if (trklen_array[i_alg][itrack] >= 0.5*pathlen[igeant]){ // Cut out broken tracks (not entirely sure we want this - removes tracks from numerator (reco) but not denominator (truth))
			  // Fill reco histograms
			  mclen_reco[i_alg]->Fill(pathlen[igeant]);
			  mcpdg_reco[i_alg]->Fill(pdg[igeant]);
			  mctheta_reco[i_alg]->Fill(theta[igeant]*180.0/TMath::Pi());
			  mcphi_reco[i_alg]->Fill(phi[igeant]*180.0/TMath::Pi());
			  mcthetaxz_reco[i_alg]->Fill(theta_xz[igeant]*180.0/TMath::Pi());
			  mcthetayz_reco[i_alg]->Fill(theta_yz[igeant]*180.0/TMath::Pi());
			  mcmom_reco[i_alg]->Fill(P[igeant]);
			  //}
		      }
		    }
		    
		  }
		}
	      }
	      
	    } // Loop over geant particles in track (igeant)
	    
	  } // Loop over reconstructed tracks in event (itrack)
	} // Loop over reconstruction algorithms (i_alg)
      
    }// Loop over entries in tree (jentry)
  

  // Now all our histograms have been filled, make efficiency histograms!
  for (int i_alg=0; i_alg < n_algos; i_alg++){
    mclen_eff[i_alg] = effcalc(mclen_reco[i_alg], mclen_true, TString("Tracking Efficiency: "+algoNames[i_alg]+"; Track Length (cm); Efficiency"));
    mcpdg_eff[i_alg] = effcalc(mcpdg_reco[i_alg], mcpdg_true, TString("Tracking Efficiency: "+algoNames[i_alg]+"; PDG Code; Efficiency"));
    mctheta_eff[i_alg] = effcalc(mctheta_reco[i_alg], mctheta_true, TString("Tracking Efficiency: "+algoNames[i_alg]+"; #theta (degrees); Efficiency"));
    mcphi_eff[i_alg] = effcalc(mcphi_reco[i_alg], mcphi_true, TString("Tracking Efficiency: "+algoNames[i_alg]+"; #phi (degrees); Efficiency"));
    mcthetaxz_eff[i_alg] = effcalc(mcthetaxz_reco[i_alg], mcthetaxz_true, TString("Tracking Efficiency: "+algoNames[i_alg]+"; #theta_{xz} (degrees); Efficiency"));
    mcthetayz_eff[i_alg] = effcalc(mcthetayz_reco[i_alg], mcthetayz_true, TString("Tracking Efficiency: "+algoNames[i_alg]+"; #theta_{yz} (degrees); Efficiency"));
    mcmom_eff[i_alg] = effcalc(mcmom_reco[i_alg], mcmom_true, TString("Tracking Efficiency: "+algoNames[i_alg]+"; Momentum (GeV); Efficiency"));

    mclen_eff[i_alg]->SetName(TString("mclen_eff_"+algoNames[i_alg]));
    mcpdg_eff[i_alg]->SetName(TString("mcpdg_eff_"+algoNames[i_alg]));
    mctheta_eff[i_alg]->SetName(TString("mctheta_eff_"+algoNames[i_alg]));
    mcphi_eff[i_alg]->SetName(TString("mcphi_eff_"+algoNames[i_alg]));
    mcthetaxz_eff[i_alg]->SetName(TString("mcthetaxz_eff_"+algoNames[i_alg]));
    mcthetayz_eff[i_alg]->SetName(TString("mcthetayz_eff_"+algoNames[i_alg]));
    mcmom_eff[i_alg]->SetName(TString("mcmom_eff_"+algoNames[i_alg]));
  } // Loop over reconstruction algorithms (i_alg)


  // ------ Finally, return efficiency histograms ------- //
  std::vector<TH1F*> eff_hists;
  for (int i_alg=0; i_alg < n_algos; i_alg++){
    // Only make reduced set of plots for CI
    eff_hists.push_back(mclen_eff[i_alg]);
    if (short_long == "long"){ // Full set of plots
      eff_hists.push_back(mcpdg_eff[i_alg]);
      eff_hists.push_back(mctheta_eff[i_alg]);
      eff_hists.push_back(mcphi_eff[i_alg]);
      eff_hists.push_back(mcthetaxz_eff[i_alg]);
      eff_hists.push_back(mcthetayz_eff[i_alg]);
      eff_hists.push_back(mcmom_eff[i_alg]);
    }
  }// Loop over reconstruction algorithms (i_alg)

  return eff_hists;
}
