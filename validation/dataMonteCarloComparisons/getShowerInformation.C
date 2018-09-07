#include <iostream>
#include <fstream>
#include <string>

#include "TChain.h"
#include "TH1.h"
#include "TFile.h"
#include "TCanvas.h"
#include "TLegend.h"
#include "TPaveText.h"
#include "TAxis.h"
#include "TROOT.h"
#include "TStyle.h"

#include "getMax.C"
#include "setStyle.C"
#include "setStyleRatio.C"
#include "setLegend.C"
#include "calculateChiSqDistance.C"
#include "getNBins.C"
#include "textWrap.C"

void getShowerInformation(TString file1name, TString file1_dataormc, TString file1_label, TString file2name, TString file2_dataormc, TString file2_label, TString outDir, int compType, int isCI, float chisqNotifierCut) {

  // define output
  TString outputFile(outDir+"fOutputShowers.root");
  TFile f_output(outputFile,"RECREATE");

  // define input 
  TChain *fChainFile1 = new TChain("analysistree/anatree");
  TChain *fChainFile2 = new TChain("analysistree/anatree");
  fChainFile1->Add(file1name);
  fChainFile2->Add(file2name);

  //
  // shower information
  //

  TCanvas *c1 = new TCanvas("c1", "c1", 500, 500);
  TPad *topPad = new TPad("topPad", "", 0.005, 0.3, 0.995, 0.995);
  TPad *bottomPad = new TPad("bottomPad", "", 0.005, 0.005, 0.995, 0.3);
  topPad->SetBottomMargin(0.02);
  bottomPad->SetTopMargin(0.0);
  bottomPad->SetBottomMargin(0.18);
  bottomPad->SetGridy();
  topPad->Draw();
  bottomPad->Draw();
  topPad->cd();

  std::vector< std::string > algoNames;
  std::vector< std::string > showerPlotNames;
  std::vector< std::vector<double> > showerPlotValues;
  std::vector< std::vector< std::string > > comments;

  if (isCI == 1){

    // define vector of algo names
    algoNames = {"pandora"};

    // and define plots
    showerPlotNames = {
      "nshowers",
      "shwr_theta",
      "shwr_phi"
      //"shwr_startdcosx",
      //"shwr_startdcosy",
      //"shwr_startdcosz"
    };


    showerPlotValues = {
      /*nshowers*/       {30.0, 0, 30.0},
      /*shwr_theta*/     {50.0, 0, 3.3},
      /*shwr_phi*/       {50.0, -3.3, 3.3}
      ///*shwr_startdcosx*/{50, -1, 1},
      ///*shwr_startcosy*/ {50, -1, 1},
      ///*shwr_startcosz*/ {50, -1, 1},
    };

    comments = {
      /*nshowers_pandora*/       {"nshowers_pandora. Number of showers reconstructed by the pandora algorithm.",
      /*shwr_theta_pandora*/      "shwr_theta_pandora. Shower theta angle as reconstructed by pandora. Theta = 0 means the shower is going in the beam direction, Theta = pi means the shower is going in the anti-beam direction.",
      /*shwr_phi_pandora*/        "shwr_phi_pandora. Shower phi angle as reconstructed by pandora. Phi = -pi/2 means the shower is downwards-going, Phi = pi/2 means the shower is upwards-going."}
      ///*shwr_startdcosx_pandora*/ "shwr_startdcosx_pandora",
      ///*shwr_startdcosy_pandora*/ "shwr_startdcosy_pandora",
      ///*shwr_startcosz_pandora*/  ""}
    };

  }
  else {
    // define vector of algo names
    algoNames = {"pandoraCosmic", "pandoraNu", "showerrecopandora","pandora"};

    // and define plots
    showerPlotNames = {
      "nshowers",
      "shwr_length",
      "shwr_theta",
      "shwr_thetaxz",
      "shwr_thetayz",
      "shwr_phi",
      "shwr_startdcosx",
      "shwr_startdcosy",
      "shwr_startdcosz",
      "shwr_startx",
      "shwr_starty",
      "shwr_startz"};


    showerPlotValues = {
      /*nshowers*/       {30.0, 0, 30.0},
      /*shwr_length*/    {50.0, 0, 700.0},
      /*shwr_theta*/     {50.0, 0, 3.3},
      /*shwr_thetaxz*/   {50.0, -3.3, 3.3},
      /*shwr_thetayz*/   {50.0, -3.3, 3.3},
      /*shwr_phi*/       {50.0, -3.3, 3.3},
      /*shwr_startdcosx*/{50, -1, 1},
      /*shwr_startcosy*/ {50, -1, 1},
      /*shwr_startcosz*/ {50, -1, 1},
      /*shwr_startx*/    {50.0, -100.0, 350.0},
      /*shwr_starty*/    {50.0, -130.0, 130.0},
      /*shwr_startz*/    {50.0, -50.0, 1140}};
  }

  for (int i = 0; i < algoNames.size(); i++ ) {

    for (int j = 0; j < showerPlotNames.size(); j++) {

      if ((algoNames[i] == "pandoraCosmic" || algoNames[i] == "pandora") && showerPlotNames[j] == "nshowers"){

        showerPlotValues[j] = {40,0,160};

      }


      // histogram styling
      TString yAxisTitle("# Showers");

      TString fileName(showerPlotNames[j]+"_"+algoNames[i]);

      TH1D *hFile1 = new TH1D(fileName+"_file1", "", (int)showerPlotValues[j][0], showerPlotValues[j][1], showerPlotValues[j][2]); 
      TH1D *hFile2 = new TH1D(fileName+"_file2", "", (int)showerPlotValues[j][0], showerPlotValues[j][1], showerPlotValues[j][2]); 

      TString file1DrawString(fileName+" >> "+fileName+"_file1");
      TString file2DrawString(fileName+" >> "+fileName+"_file2");
      fChainFile1->Draw(file1DrawString);
      fChainFile2->Draw(file2DrawString);


      // Keep error while scaling
      hFile1->Sumw2();
      hFile2->Sumw2();


      // arb units
      if (hFile1->Integral() > 0 && compType == 0) {
        hFile1->Scale(1./(hFile1->Integral()+hFile1->GetBinContent(0)+hFile1->GetBinContent(hFile1->GetNbinsX()+1)));
      }

      if (hFile2->Integral() > 0 && compType == 0) {
        hFile2->Scale(1./(hFile2->Integral()+hFile2->GetBinContent(0)+hFile2->GetBinContent(hFile2->GetNbinsX()+1)));
      }

      // set max extent of histogram
      double maxext = getMax(hFile1, hFile2);
      hFile2->SetMaximum(maxext);

      // here 0 = nominal 

      if (file1_dataormc == "DATA" && file2_dataormc == "MC"){

        setStyle(hFile1, 0, yAxisTitle);
        setStyle(hFile2, 1, yAxisTitle);

        topPad->cd(); 
        // draw MC histo error bars...
        hFile2->Draw("e2");

        // clone, and draw as histogram
        TH1F* hFile2c = (TH1F*)hFile2->Clone("hFile2c");
        hFile2c->SetDirectory(0);
        hFile2c->SetFillColor(0);
        hFile2c->Draw("hist same");

        // and data
        hFile1->Draw("e1same");

        hFile2->GetXaxis()->SetTitle((showerPlotNames[j]).c_str());
        setLegend(hFile1, 0, file1_label, hFile2, 1, file2_label);

        bottomPad->cd();
        TH1D *ratioPlotFile2 = (TH1D*)hFile2->Clone("ratioPlotFile2");
        ratioPlotFile2->Add(hFile2, -1);
        ratioPlotFile2->GetYaxis()->SetRangeUser(-1,1);
        ratioPlotFile2->Divide(hFile2);

        setStyleRatio(ratioPlotFile2, file1_label, file2_label);

        ratioPlotFile2->Draw("hist");
        TH1D* ratioPlotFile2C = (TH1D*)ratioPlotFile2->Clone("ratioPlotFile2C");
        ratioPlotFile2C->SetFillColor(0);
        ratioPlotFile2C->Draw("histsame");

        TH1D *ratioPlotFile1 = (TH1D*)hFile1->Clone("ratioPlotFile1");
        ratioPlotFile1->Add(hFile2, -1);
        ratioPlotFile1->Divide(hFile2);
        ratioPlotFile1->Draw("e1same");

      }
      else if (file1_dataormc == "MC" && file2_dataormc == "MC"){
        setStyle(hFile1, 3, yAxisTitle);
        setStyle(hFile2, 1, yAxisTitle);
        topPad->cd(); 

        // draw MC histo error bars...
        hFile2->Draw("e2");

        // clone, and draw as histogram
        TH1F* hFile2c = (TH1F*)hFile2->Clone("hFile2c");
        hFile2c->SetDirectory(0);
        hFile2c->SetFillColor(0);
        hFile2c->Draw("hist same");

        // and data
        hFile1->Draw("e2same");
        TH1F* hFile1c = (TH1F*)hFile1->Clone("hFile1c");
        hFile1c->SetDirectory(0);
        hFile1c->SetFillColor(0);
        hFile1c->Draw("hist same");

        hFile2->GetXaxis()->SetTitle((showerPlotNames[j]).c_str());
        setLegend(hFile1, 3, file1_label, hFile2, 1, file2_label);

        bottomPad->cd();
        TH1D *ratioPlotFile2 = (TH1D*)hFile2->Clone("ratioPlotFile2");
        ratioPlotFile2->Add(hFile2, -1);
        ratioPlotFile2->Divide(hFile2);
        setStyleRatio(ratioPlotFile2, file1_label, file2_label);
        ratioPlotFile2->GetYaxis()->SetRangeUser(-1,1);
        ratioPlotFile2->Draw("hist");
        TH1D* ratioPlotFile2C = (TH1D*)ratioPlotFile2->Clone("ratioPlotFile2C");
        ratioPlotFile2C->SetFillColor(0);
        ratioPlotFile2C->Draw("histsame");

        TH1D *ratioPlotFile1 = (TH1D*)hFile1->Clone("ratioPlotFile1");
        ratioPlotFile1->Add(hFile2, -1);
        ratioPlotFile1->Divide(hFile2);
        ratioPlotFile1->Draw("e2same");
        TH1D* ratioPlotFile1C = (TH1D*)ratioPlotFile1->Clone("ratioPlotFile1C");
        ratioPlotFile1C->SetFillColor(0);
        ratioPlotFile1C->Draw("histsame");

      }
      else if (file1_dataormc == "DATA" && file2_dataormc == "DATA"){
        setStyle(hFile1, 0, yAxisTitle);
        setStyle(hFile2, 2, yAxisTitle);
        topPad->cd(); 

        hFile2->Draw("e1");
        hFile1->Draw("e1same");

        setLegend(hFile1, 0, file1_label, hFile2, 2, file2_label);

        bottomPad->cd();
        TH1D *ratioPlotFile2 = (TH1D*)hFile2->Clone("ratioPlotFile2");
        ratioPlotFile2->Add(hFile2, -1);
        ratioPlotFile2->Divide(hFile2);
        setStyleRatio(ratioPlotFile2, file1_label, file2_label);
        ratioPlotFile2->GetYaxis()->SetRangeUser(-1,1);
        ratioPlotFile2->Draw("hist");

        TH1D *ratioPlotFile1 = (TH1D*)hFile1->Clone("ratioPlotFile1");
        ratioPlotFile1->Add(hFile2, -1);
        ratioPlotFile1->Divide(hFile2);
        ratioPlotFile1->Draw("e1same");

      }

      double chisqv = calculateChiSqDistance(hFile1, hFile2);
      TString chisq = Form("#chi^{2}: %g", chisqv);
      int nBins = std::max(getNBins(hFile1),getNBins(hFile2)); 
      TString NDF = Form("No. Bins: %i", nBins);
      topPad->cd();
      TPaveText *pt = new TPaveText(0.5, 0.78, 0.9, 0.88, "NDC");
      pt->AddText(chisq);
      pt->AddText(NDF);
      pt->SetFillStyle(0);
      pt->SetBorderSize(0);
      pt->SetTextAlign(31);
      pt->Draw("same");

      double totalEntries1 = hFile1->Integral() + hFile1->GetBinContent(0) + hFile1->GetBinContent(hFile1->GetNbinsX()+1);
      double underflowFrac1 = hFile1->GetBinContent(0)/totalEntries1;
      double overflowFrac1 =  hFile1->GetBinContent(hFile1->GetNbinsX()+1)/totalEntries1;

      double totalEntries2 = hFile2->Integral() + hFile2->GetBinContent(0) + hFile2->GetBinContent(hFile2->GetNbinsX()+1);
      double underflowFrac2 = hFile2->GetBinContent(0)/totalEntries2;
      double overflowFrac2 = hFile2->GetBinContent(hFile2->GetNbinsX()+1)/totalEntries2;

      TString underOver1 = Form("UF: %g  OF: %g", file1_label, underflowFrac1, overflowFrac1);
      TString underOver2 = Form("UF: %g  OF: %g", file2_label, underflowFrac2, overflowFrac2);

      TPaveText *pt_ufofl = new TPaveText(0.5, 0.73, 0.9, 0.78, "NDC");
      pt_ufofl->AddText(file1_label+"/"+underOver1);
      pt_ufofl->SetFillStyle(0);
      pt_ufofl->SetBorderSize(0);
      pt_ufofl->SetTextAlign(31);
      pt_ufofl->Draw("same");

      TPaveText *pt_ufofr = new TPaveText(0.5, 0.68, 0.9, 0.73, "NDC");
      pt_ufofr->AddText(file2_label+"/"+underOver2);
      pt_ufofr->SetFillStyle(0);
      pt_ufofr->SetBorderSize(0);
      pt_ufofr->SetTextAlign(31);
      pt_ufofr->Draw("same");


      TPaveText *pt2 = new TPaveText(0.1, 0.83, 0.5, 0.88, "NDC");
      pt2->AddText(file1_dataormc+"/"+file2_dataormc);
      pt2->SetFillStyle(0);
      pt2->SetBorderSize(0);
      pt2->SetTextAlign(11);
      pt2->Draw("same");

      TString saveString = Form(outDir+"2SHOWER_"+fileName+".png");
      c1->SaveAs(saveString, "png"); 

      hFile1->Write();
      hFile2->Write();

      if (isCI){
        std::ofstream commentsFile;
        commentsFile.open(outDir+"2SHOWER_"+fileName+".comment");
        textWrap(comments.at(i).at(j),commentsFile,70);
        commentsFile.close();
      }

      // Print all chi2 values to a file for tracking over time
      std::ofstream ChisqFile;
      ChisqFile.open(outDir+"ChisqValues.txt", std::ios_base::app);
      ChisqFile << fileName << " " << chisqv << "\n";
      ChisqFile.close();

      // Print names of plots with high chi2 to a separate file
      if (chisqv >= chisqNotifierCut){

        std::ofstream highChisqFile;
        highChisqFile.open(outDir+"highChisqPlots.txt", std::ios_base::app);
        highChisqFile << fileName <<  " " << chisqv << " is larger than "<< chisqNotifierCut << "\n";
        highChisqFile.close();

      }

    }
  }

  f_output.Close();

}

int main(int argc, char* argv[]){

  TString file1name(argv[1]);
  TString file1_dataormc(argv[2]);
  TString file1_label(argv[3]);
  TString file2name(argv[4]);    
  TString file2_dataormc(argv[5]);
  TString file2_label(argv[6]);
  TString outDir(argv[7]);
  int compType = atoi(argv[8]);
  int isCI = atoi(argv[9]);
  float chisqNotifierCut = atof(argv[10]);

  getShowerInformation(file1name, file1_dataormc, file1_label, file2name, file2_dataormc, file2_label, outDir, compType, isCI, chisqNotifierCut);
  return 0;

}
