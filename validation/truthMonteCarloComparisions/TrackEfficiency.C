#include <iostream>
#include <string>
#include <vector>
#include <sstream>

#include <cassert>
#include <algorithm>

#include "TChain.h"
#include "TH1F.h"
#include "TFile.h"
#include "TCanvas.h"
#include "TLegend.h"
#include "TAxis.h"
#include "TStyle.h"
#include "TString.h"
#include "TPad.h"
#include "TMath.h"
#include "TString.h"
#include "TGraph.h"

#include "TrackEfficiency_functions.C"

std::vector<std::string> ParseToStr(std::string str, const char* del) {
  std::istringstream stream(str);
  std::string temp_string;
  std::vector<std::string> vals;

  while (std::getline(stream >> std::ws, temp_string, *del)) {
    if (temp_string.empty()) continue;
    vals.push_back(temp_string);
  }

  return vals;
}

// ---------------------------------------------------------------------------------------------- //

int TrackEfficiency(TString file1name, TString file1_label, TString file2name="", TString file2_label="", TString outDir="./", TString algos=""){

  // Define output
  TString outputFile(outDir+"fOutputTruth_TrackingEfficiency.root");
  TFile *f_output = new TFile(outputFile,"RECREATE");

  // What tracking algorithms do we want to use?
  std::vector< std::string > algoNames;
  if (algos == ""){
    algoNames = {"pandoraNu", "pandoraNuPMA", "pandoraCosmic", "pandoraCosmicKHit", "pandoraNuKHit", "pandoraNuKalmanTrack\
", "pmtrack", "pandoraNuKalmanShower"};
  }
  else {
    algoNames = ParseToStr(algos.Data(),",");
  }

  // Are we doing an MC/MC comparison?
  bool do_comparison = true;
  if (file2name == ""){ do_comparison = false; }
  
  // Now get efficiency plots
  std::vector<TH1F*> eff_hists_file1 = MakeEffPlots(file1name, algoNames);
  std::vector<TH1F*> eff_hists_file2;
  if (do_comparison){
    eff_hists_file2 = MakeEffPlots(file2name, algoNames);
    if (eff_hists_file2.size() != eff_hists_file1.size()){
	std::cerr << "[ERROR] Made " << eff_hists_file1.size() << " histograms for " << file1_label << " and " << eff_hists_file2.size() << " histograms for " << file2_label << std::endl;
	throw;
    }
  }
    

  // Make overlaid plots of both histograms and save
  f_output->cd();
  TCanvas *c1 = new TCanvas("c1", "c1", 500, 500);
  TGraph *dummy_file1 = new TGraph(1);
  TGraph *dummy_file2 = new TGraph(1);
  dummy_file1->SetLineWidth(2);
  dummy_file2->SetLineWidth(2);
  dummy_file1->SetLineColor(kRed);
  dummy_file2->SetLineColor(kBlue);
  TLegend *leg = new TLegend(0.5, 0.8, 0.89, 0.89);
  leg -> AddEntry(dummy_file1, file1_label, "l");
  if (do_comparison) leg -> AddEntry(dummy_file2, file2_label, "l");
  
  for (int i_hist = 0; i_hist < eff_hists_file1.size(); i_hist++){
    // Save individual plots
    TH1F *hist_file1 = eff_hists_file1.at(i_hist);
    hist_file1->Write(TString(file1_label+"_"+hist_file1->GetName()));
    
    TString canvname = TString("Comparison_");
    canvname += TString(hist_file1->GetName());

    // Save overlays
    if (do_comparison){
      TH1F *hist_file2 = eff_hists_file2.at(i_hist);
      hist_file2->Write(TString(file2_label+"_"+hist_file2->GetName()));
      
      hist_file1->SetLineWidth(2);
      hist_file2->SetLineWidth(2);
      hist_file1->SetLineColor(kRed);
      hist_file2->SetLineColor(kBlue);

      hist_file1->Draw("h");
      hist_file2->Draw("hsame");

      leg->Draw("same");

      c1->Write(canvname);
    }
  }

  return 0;
}

// --------------------------------------- Main function --------------------------------------- //
int main(int argc, char const * argv[])
{
  if (argc < 2){
    std::cout << "Usage: TrackEfficiency file1name file1_legend_title [outDir] [tracking_algorithms] [file2name] [file2_legend_title]" << std::endl
	      << "Arguments in square brackets [] are optional" << std::endl;
    return 1;
  }

  std::string file1_s="";
  std::string file1_label="";
  std::string file2_s = "";
  std::string file2_label = "";
  std::string outdir = "./";
  std::string trackers = "";

  if (argc >= 2){
    file1_s = argv[1];
    file1_label = argv[2];
  }
  if (argc >= 3){
    outdir = argv[3];
  }
  if (argc >= 4){
    trackers = argv[4];
  }
  if (argc >= 5){
    file2_s = argv[5];
  }
  if (argc >= 6){
    file2_label = argv[6];
  }

  for (int i=0; i<argc; i++){
    std::cout << i << "  " << argv[i] << std::endl;
  }
  
  TrackEfficiency(file1_s, file1_label, file2_s, file2_label, outdir, trackers);
  
  return 0;
}

