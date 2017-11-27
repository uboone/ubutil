#include <iostream>
#include <string>
#include <vector>
#include <sstream>
#include <string>
#include <fstream>

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

int chisqNotifierCut = 9999999;


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
double calculateChiSqDistance(TH1F *O, TH1F *E){
    double chisq = 0;
    for (int i = 1; i < O->GetNbinsX()+1; i++){

        double O_i = O->GetBinContent(i);
        double E_i = E->GetBinContent(i);
        double O_ierr = O->GetBinError(i);
        double E_ierr = E->GetBinError(i);

        if (O_i == 0 && E_i == 0){
            chisq += 0;
        }
        else{
            chisq += std::pow(O_i - E_i,2)/(std::sqrt(std::pow(O_ierr,2) + std::pow(E_ierr,2)));
        }
    }
    return chisq;
}

// ---------------------------------------------------------------------------------------------- //

int TrackEfficiency(TString file1name, TString file1_label, TString file2name="", TString file2_label="", TString outDir="./", TString algos="", TString short_long="short"){

  // Define output
  TString outputFile(outDir+"fOutputTruth_TrackingEfficiency.root");
  TFile *f_output = new TFile(outputFile,"RECREATE");

  // What tracking algorithms do we want to use?
  std::vector< std::string > algoNames;
  if (algos == ""){
    algoNames = {"pandoraNu", "pandoraNuPMA", "pandoraCosmic", "pandoraCosmicKHit", "pandoraNuKHit", "pandoraNuKalmanTrack", "pmtrack", "pandoraNuKalmanShower"};
  }
  else {
    algoNames = ParseToStr(algos.Data(),",");
  }

  // Are we doing an MC/MC comparison?
  bool do_comparison = true;
  if (file2name == ""){ do_comparison = false; }
  
  // Now get efficiency plots
  std::vector<TH1F*> eff_hists_file1 = MakeEffPlots(file1name, algoNames, short_long);
  std::vector<TH1F*> eff_hists_file2;
  if (do_comparison){
    eff_hists_file2 = MakeEffPlots(file2name, algoNames, short_long);
    if (eff_hists_file2.size() != eff_hists_file1.size()){
	std::cerr << "[ERROR] Made " << eff_hists_file1.size() << " histograms for " << file1_label << " and " << eff_hists_file2.size() << " histograms for " << file2_label << std::endl;
	throw;
    }
  }

  gStyle->SetOptStat(0);

  // Make overlaid plots of both histograms and save
  f_output->cd();
  TCanvas *c1 = new TCanvas("c1", "c1", 500, 500);
  TGraph *dummy_file1 = new TGraph(1);
  TGraph *dummy_file2 = new TGraph(1);
  dummy_file1->SetLineWidth(2);
  dummy_file2->SetLineWidth(2);
  dummy_file1->SetLineColor(kRed);
  dummy_file2->SetLineColor(kBlue);
  
  for (int i_hist = 0; i_hist < eff_hists_file1.size(); i_hist++){
    
    // Save individual plots
    TH1F *hist_file1 = eff_hists_file1.at(i_hist);
    hist_file1->SetLineWidth(2);
    hist_file1->SetLineColor(kRed);
    
    hist_file1->Write(TString(file1_label+"_"+hist_file1->GetName()));

    hist_file1->Draw("h");
    
    TLegend *leg = new TLegend(0.5, 0.73, 0.89, 0.89);
    leg -> AddEntry(dummy_file1, file1_label, "l");
    leg->Draw();
    
    std::string outname;
    if (eff_hists_file1.size() > 1 && i_hist == 0){
      outname = std::string("MC_trackeff" + file1_label + ".pdf(");
    }
    else if (eff_hists_file1.size() > 1 && i_hist == eff_hists_file1.size()-1){
      outname = std::string("MC_trackeff" + file1_label + ".pdf)");
    }
    else{
      outname = std::string("MC_trackeff" + file1_label + ".pdf");
    }
    c1->Print(outname.c_str(),"pdf");
    
    TString canvname = TString("Comparison_");
    canvname += TString(hist_file1->GetName());

    // Save overlays
    if (do_comparison){
      leg -> AddEntry(dummy_file2, file2_label, "l");
      
      TH1F *hist_file2 = eff_hists_file2.at(i_hist);
      hist_file2->SetLineWidth(2);
      hist_file2->SetLineColor(kBlue);
      
      hist_file2->Write(TString(file2_label+"_"+hist_file2->GetName()));

      hist_file1->Draw("h");
      hist_file2->Draw("hsame");

      // Calculate chi2 between two plots and put in format for legend
      double chisqv = calculateChiSqDistance(hist_file1, hist_file2);
      TString chisq = Form("#chi^{2}: %g", chisqv);
      int nBins = std::max(hist_file1->GetNbinsX(), hist_file2->GetNbinsX());
      TString NDF = Form("No. Bins: %i", nBins);
      double chisqNDF = chisqv/(double)nBins;
      TString chisqNDFstr = Form("#chi^{2}/No. bins: %g", chisqNDF);
      
      // If chisq is large, print to file
      if (chisqNDF >= chisqNotifierCut/100.0){
	std::ofstream highChisqFile;
	highChisqFile.open("highChisqPlots.txt", std::ios_base::app);
	highChisqFile << c1->GetName() <<  "\n";
	highChisqFile.close();
      }
	
      leg->AddEntry((TObject*)0, chisq, "");
      leg->AddEntry((TObject*)0, NDF, "");
      leg->AddEntry((TObject*)0, chisqNDFstr, "");
      leg->Draw("same");

      c1->Write(canvname);

      if (eff_hists_file1.size() > 1 && i_hist == 0){
	outname = std::string("MCcomparison_trackeff" + file1_label + "_" + file2_label + ".pdf(");
      }
      else if (eff_hists_file1.size() > 1 && i_hist == eff_hists_file1.size()-1){
	outname = std::string("MCcomparison_trackeff" + file1_label + "_" + file2_label + ".pdf)");
      }
      else{
	outname = std::string("MCcomparison_trackeff" + file1_label + "_" + file2_label + ".pdf");
      }
      c1->Print(outname.c_str(),"pdf");
      
    }
  }

  return 0;
}

// --------------------------------------- Main function --------------------------------------- //
int main(int argc, char const * argv[])
{
  if (argc < 2){
    std::cout << "Usage: TrackEfficiency file1name file1_legend_title [short/long] [file2name] [file2_legend_title] [chi2cut*100] [outDir] [tracking_algorithms] " << std::endl
	      << "Arguments in square brackets [] are optional" << std::endl
	      << "--- if outDir is not given, will default to current directory" << std::endl
	      << "--- if short/long is not given, will default to short (CI validation mode)" << std::endl
	      << "\"long\" will produce and save more (redundant) histograms for deeper analysis." << std::endl
	      << "--- if tracking_algorithms is not given, will default to producing plots for all of the following tracking algorithms currently available in analysistree: pandoraNu, pandoraNuPMA, pandoraCosmic, pandoraCosmicKHit, pandoraNuKHit, pandoraNuKalmanTrack, pmtrack, pandoraNuKalmanShower" << std::endl
	      << "\"chi2cut*100\" defines a 'bad' chi2 -- any comparison plots with chi2/nbins>(chi2cut*100)/100 will have their names written to file to remind you to check them. Eg. use chi2cut*100=300 to print out a list of all plots with chi2/nbins>3." << std::endl;
    return 1;
  }

  std::string file1_s="";
  std::string file1_label="";
  std::string file2_s = "";
  std::string file2_label = "";
  std::string outdir = "./";
  std::string trackers = "";
  std::string short_long = "short";
  std::string chisqNotifierCut_str;

  if (argc >= 2){
    file1_s = argv[1];
    file1_label = argv[2];
  }
  if (argc >= 3){
    short_long = argv[3];
  }
  if (argc >= 4){
    file2_s = argv[4];
  }
  if (argc >= 5){
    file2_label = argv[5];
  }
  if (argc >= 6){
    chisqNotifierCut_str = argv[6];
    chisqNotifierCut = std::atoi(chisqNotifierCut_str.c_str());
    std::cout << "Notifying about any comparison plots with chi2/no. bins > " << chisqNotifierCut/100.0 << std::endl;
  }
  if (argc >= 7){
    outdir = argv[7];
  }
  if (argc >= 8){
    trackers = argv[8];
  }
  
  TrackEfficiency(file1_s, file1_label, file2_s, file2_label, outdir, trackers, short_long);
  
  return 0;
}

