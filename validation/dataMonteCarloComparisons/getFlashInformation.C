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

void getFlashInformation(TString file1name, TString file1_dataormc, TString file1_label, TString file2name, TString file2_dataormc, TString file2_label, TString outDir, int compType, double PeCut, int isCI, float chisqNotifierCut) {

  // define output
  TString outputFile(outDir+"fOutputFlashes.root");
  TFile f_output(outputFile,"RECREATE");

  // define input
  TChain *fChainFile1 = new TChain("analysistree/anatree");
  TChain *fChainFile2 = new TChain("analysistree/anatree");
  fChainFile1->Add(file1name);
  fChainFile2->Add(file2name);

  //
  // flash information
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
  std::vector< std::string > flashPlotNames;
  std::vector< std::vector< std::vector<double> > > flashPlotValues;
  std::vector< std::vector< std::string > > comments;

  if (isCI == 1){

    // define vector of algo names
    algoNames = {
      "simpleFlashBeam",
      "simpleFlashCosmic",
      "simpleFlashBeamLowPE"
    };

    // and define plots
    flashPlotNames = {
      "nfls",
      "flsTime",
      "flsPe"
    };

    //Outer vectors are for each variable, inner vectors are for each algorithm
    flashPlotValues = {
      /*nfls*/              {{10, 0, 10}, {75, 0, 75}},
      /*flsTime*/           {{50, 0, 25}, {160, -3200, 4800}},
      /*flsPe*/             {{100, 20, 4000}, {100, 30, 4000}}
    };

    comments = {
      /*nfls_simpleFlashBeam*/      {"nfls_simpleFlashBeam. Each entry in the histogram is the number of flashes for a single event, as reconstructed with the simpleFlashBeam algorithm.",
      /*flsTime_simpleFlashBeam*/    "flsTime_simpleFlashBeam. Peak time of each flash, as reconstructed with the simpleFlashBeam algorithm.",
      /*flsPe_simpleFlashBeam*/      "flsPe_simpleFlashBeam. The number of photoelectrons produced by each flash, as reconstructed with the simpleFlashBeam algorithm. If there are any entries in the underflow bin, email the experts."},
      /*nfls_simpleFlashCosmic*/    {"nfls_simpleFlashCosmic. Each entry in the histogram is the number of flashes for a single event, as reconstructed with the simpleFlashCosmic algorithm.",
      /*flsTime_simpleFlashCosmic*/  "flsTime_simpleFlashCosmic. Peak time of each flash, as reconstructed with the simpleFlashCosmic algorithm.",
      /*flsPe_simpleFlashCosmic*/    "flsPe_simpleFlashCosmic. The number of photoelectrons produced by each flash, as as reconstructed with the simpleFlashCosmic algorithm. If there are any entries in the underflow bin, email the experts."}
    };

  }
  else {
    // define vector of algo names
    algoNames = {
      "simpleFlashBeam",
      "simpleFlashCosmic",
      "simpleFlashBeamLowPE"};

    // and define plots
    flashPlotNames = {
      "nfls",
      "flsTime",
      "flsPe",
      "flsZcenter",
      "flsYcenter",
      "flsZwidth",
      "flsYwidth"};


    //Outer vectors are for each variable, inner vectors are for each algorithm
    flashPlotValues = {
      /*nfls*/              {{10, 0, 10}, {150, 0, 150}, {10, 0, 10}, {75, 0, 75}},
      /*flsTime*/           {{100, 0, 25}, {160, -3200, 4800}, {100, 0, 25}, {160, -3200, 4800}},
      /*flsPe*/             {{50, 0, 200}, {50, 0, 200},{50, 0, 200}, {50, 0, 200}},
      /*flsZcenter*/        {{50, -100, 1100}, {50, -100, 1100}, {50, -100, 1100}, {50, -100, 1100}},
      /*flsYcenter*/        {{50, -100, 100}, {50, -100, 100}, {50, -100, 100}, {50, -100, 100}},
      /*flsZwidth*/         {{50, 0, 500}, {50, 0, 200}, {50, 0, 300}, {50, 0, 200}},
      /*flsYwidth*/         {{50, 0, 100}, {50, 0, 100}, {50, 0, 100}, {50, 0, 100}}};
  }

  for (int i = 0; i < algoNames.size(); i++) {

    for (int j = 0; j < flashPlotNames.size(); j++) {

      TString fileName(flashPlotNames[j]+"_"+algoNames[i]);

      TH1D *hFile1 = new TH1D(fileName+"_file1", "", (int)flashPlotValues[j][i][0], flashPlotValues[j][i][1], flashPlotValues[j][i][2]);
      TH1D *hFile2 = new TH1D(fileName+"_file2", "", (int)flashPlotValues[j][i][0], flashPlotValues[j][i][1], flashPlotValues[j][i][2]);

      TString file1DrawString(fileName+" >> "+fileName+"_file1");
      TString file2DrawString(fileName+" >> "+fileName+"_file2");

      if (PeCut < 0) {
        fChainFile1->Draw(file1DrawString);
        fChainFile2->Draw(file2DrawString);
      }
      else {
        TString cutString = TString::Format("flsPe_%s > %f", algoNames[i].c_str(), PeCut);
        fChainFile1->Draw(file1DrawString, cutString);
        fChainFile2->Draw(file2DrawString, cutString);
      }

      c1->cd();

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

      // histogram styling
      TString yAxisTitle("# Flashes [arb]");

      // here 0 = nominal

      if (file1_dataormc == "DATA" && file2_dataormc == "MC"){

        setStyle(hFile1, 0, yAxisTitle);
        setStyle(hFile2, 1, yAxisTitle);

        topPad->cd();
        // draw MC histo error bars...
        hFile2->Draw("e2");
        hFile2->GetYaxis()->SetRangeUser(0,maxext);

        // clone, and draw as histogram
        TH1F* hFile2c = (TH1F*)hFile2->Clone("hFile2c");
        hFile2c->SetDirectory(0);
        hFile2c->SetFillColor(0);
        hFile2c->Draw("hist same");

        // and data
        hFile1->Draw("e1same");

        hFile2->GetXaxis()->SetTitle((flashPlotNames[j]).c_str());
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
        hFile2->GetYaxis()->SetRangeUser(0,maxext);

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

        hFile2->GetXaxis()->SetTitle((flashPlotNames[j]).c_str());
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
        hFile2->GetYaxis()->SetRangeUser(0,maxext);
        hFile1->Draw("e1same");

        setLegend(hFile1, 0, file1_label, hFile2, 2, file2_label);

        bottomPad->cd();
        TH1D *ratioPlotFile2 = (TH1D*)hFile2->Clone("ratioPlotFile2");
        ratioPlotFile2->Add(hFile2, -1);
        ratioPlotFile2->Divide(hFile2);
        setStyleRatio(ratioPlotFile2, file1_label, file2_label);
        ratioPlotFile2->Draw("hist");

        TH1D *ratioPlotFile1 = (TH1D*)hFile1->Clone("ratioPlotFile1");
        ratioPlotFile1->Add(hFile2, -1);
        ratioPlotFile1->Divide(hFile2);
        ratioPlotFile1->Draw("e1same");

      }

      double chisqv = calculatePearsonChiSq(hFile1, hFile2);
      int nBins = std::max(getNBins(hFile1),getNBins(hFile2))-1;
      TString chisq = Form("Shape #chi^{2}/No. Bins - 1: %g / %i", chisqv,nBins);
      TString chisqNDF = Form("= %g",chisqv/nBins);
      topPad->cd();
      TPaveText *pt = new TPaveText(0.4, 0.78, 0.9, 0.88, "NDC");
      pt->AddText(chisq);
      pt->AddText(chisqNDF);
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

      if (isCI){
        std::ofstream commentsFile;
        commentsFile.open(outDir+"5FLASH_"+fileName+".comment");
        textWrap(comments.at(i).at(j),commentsFile,70);
        commentsFile.close();
      }

      // Print all chi2 values to a file for tracking over time
      std::ofstream ChisqFile;
      ChisqFile.open(outDir+"ChisqValues.txt", std::ios_base::app);
      ChisqFile << fileName << " " << chisqv/(double)nBins << "\n";
      ChisqFile.close();

      // Print names of plots with high chi2 to a separate file
      if (chisqv/(double)nBins >= chisqNotifierCut){

        std::ofstream highChisqFile;
        highChisqFile.open(outDir+"highChisqPlots.txt", std::ios_base::app);
        highChisqFile << fileName << " " << chisqv/(double)nBins << " is larger than "<< chisqNotifierCut << "\n";
        highChisqFile.close();

        // If chisq is large, change background colour of canvas to make it really obvious
        c1->SetFillColor(kOrange-2);
    		topPad->SetFillColor(kOrange-2);
    		bottomPad->SetFillColor(kOrange-2);

      }
      else{ // Canvas background should be white
        c1->SetFillColor(kWhite);
    		topPad->SetFillColor(kWhite);
    		bottomPad->SetFillColor(kWhite);
      }


      TString saveString = Form(outDir+"5FLASH_"+fileName+".png");
      c1->SaveAs(saveString, "png");

      hFile1->Write();
      hFile2->Write();
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
  double PeCut = atof(argv[9]);
  int isCI = atoi(argv[10]);
  float chisqNotifierCut = atof(argv[11]);

  getFlashInformation(file1name, file1_dataormc, file1_label, file2name, file2_dataormc, file2_label, outDir, compType, PeCut, isCI, chisqNotifierCut);
  return 0;

}
