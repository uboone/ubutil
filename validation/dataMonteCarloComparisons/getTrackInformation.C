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

void getTrackInformation(TString file1name, TString file1_dataormc, TString file1_label, TString file2name, TString file2_dataormc, TString file2_label, TString outDir, int compType, int isCI, float chisqNotifierCut, float trackLengthCut) {

  // define output
  TString outputFile(outDir+"fOutputTracks.root");
  TFile f_output(outputFile,"RECREATE");

  // define input
  TChain *fChainFile1 = new TChain("analysistree/anatree");
  TChain *fChainFile2 = new TChain("analysistree/anatree");
  fChainFile1->Add(file1name);
  fChainFile2->Add(file2name);

  //
  // track and vertex information
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
  std::vector< std::string > trackPlotNames;
  std::vector< std::vector< double > > trackPlotValues;
  std::vector< std::vector< std::string > > comments;

  if (isCI == true){

    algoNames = {"pandora"};

    trackPlotNames = {
      "ntracks",
      "trktheta",
      "trkphi",
      "trkntraj"
    };

    trackPlotValues = {
      /*ntracks*/     {30.0, 0.0, 30.0},
      /*trktheta*/  {50.0, 0.0, 3.3},
      /*trkphi*/  {50.0, -3.3, 3.3},
      /*trkntraj*/ {150,0.0,3000}
    };

    comments = {
      /*ntracks_pandora*/ {"ntracks_pandora. Number of tracks reconstructed by the pandora algorithm.",
      /*trktheta_pandora*/ "trktheta_pandora. Track theta angle for tracks greater than 5 cm in length, as reconstructed by pandora. Theta = 0 means the track is going in the beam direction, Theta  = pi means the track is going in the anti-beam direction.",
      /*trkphi_pandora*/ "trkphi_pandora. Track phi angle for tracks greater than 5 cm in length, as reconstructed by pandora. Phi = -pi/2 means the track is downwards-going, Phi = pi/2 means the track is upwards-going. ",
      /*trkntraj_pandora*/ "trkntraj_pandora. Number of trajectory points per track in the pandora algorithm. There is a one-to-one correspondence between trajectory points and hits so this also represents the number of hits per track."}
    };

  }

  else{
    // define vector of algo names
    algoNames = {"pandoraNu", "pandoraNuPMA", "pandoraCosmic", "pandoraCosmicKHit","pandoraCosmicKalmanTrack", "pandoraNuKHit", "pandoraNuKalmanTrack", "pmtrack", "pandoraNuKalmanShower","pandora"};

    // and define plots
    trackPlotNames = {
      "ntracks",
      "trkstartx",
      "trkendx",
      "trkstarty",
      "trkendy",
      "trkstartz",
      "trkendz",
      "trklen",
      "trkntraj",
      "trktheta",
      "trkthetaxz",
      "trkthetayz",
      "trkphi",
      "nvtx",
      "vtxx",
      "vtxy",
      "vtxz"};


    trackPlotValues = {
      /*ntracks*/     {30.0, 0, 30.0},
      /*trkstartx*/   {50.0, -100.0, 350.0},
      /*trkendx*/     {50.0, -100.0, 350.0},
      /*trkstarty*/   {50.0, -130.0, 130.0},
      /*trkendy*/     {50.0, -130.0, 130.0},
      /*trkstartz*/   {50.0, -50.0, 1100.0},
      /*trkendz*/     {50.0, -50.0, 1100.0},
      /*trklen*/      {50.0, 0.0, 700.0},
      /*trkntraj*/    {150,  0.0, 3000},
      /*trktheta*/    {50.0, 0.0, 3.3},
      /*trkthetaxz*/  {50.0, -3.3, 3.3},
      /*trkthetayz*/  {50.0, -3.3, 3.3},
      /*trkphi*/      {50.0, -3.3, 3.3},
      /*nvtx*/        {100.0, 0, 100.0},
      /*vtxx*/        {50, -100.0, 350.0},
      /*vtxy*/        {50, -130.0, 130.0},
      /*vtxz*/        {50, -50.0, 1100.0}};
  }

  for (int i = 0; i < algoNames.size(); i++ ) {

    for (int j = 0; j < trackPlotNames.size(); j++) {
      // histogram styling
      TString yAxisTitle("# Tracks");

      if (((trackPlotNames[j] == "nvtx") | (trackPlotNames[j] == "vtxx") | (trackPlotNames[j] == "vtxy") | (trackPlotNames[j] == "vtxz"))){

        yAxisTitle = "# Vertices [arb]";

        if (algoNames[i] == "pandoraNuPMA"){
          algoNames[i] = "pmtrack";

          if (trackPlotNames[j] == "nvtxx"){

            trackPlotValues[i] = {100, 0, 500.0};

          }
        }
      }

      if ((algoNames[i] == "pandoraCosmic" || algoNames[i] == "pandora") && trackPlotNames[j] == "nvtx"){

        trackPlotValues[j] = {100,0,300};

      }

      if ((algoNames[i] == "pandoraCosmic" || algoNames[i] == "pandoraCosmicKalmanTrack" || algoNames[i] == "pandoraCosmicKHit" || algoNames[i] == "pmtrack" || algoNames[i] == "pandora") && trackPlotNames[j] == "ntracks"){

        trackPlotValues[j] = {50.0, 0, 100.0};

      }

      TString fileName(trackPlotNames[j]+"_"+algoNames[i]);

      TH1D *hFile1 = new TH1D(fileName+"_file1", "", (int)trackPlotValues[j][0], trackPlotValues[j][1], trackPlotValues[j][2]);
      TH1D *hFile2 = new TH1D(fileName+"_file2", "", (int)trackPlotValues[j][0], trackPlotValues[j][1], trackPlotValues[j][2]);

      TString file1DrawString(fileName+" >> "+fileName+"_file1");
      TString file2DrawString(fileName+" >> "+fileName+"_file2");
      TString cutValue = Form("%g", trackLengthCut);
      TString lengthCutString("trklen_"+algoNames[i]+" > "+cutValue);

      if (trackPlotNames[j] == "ntracks"){
        fChainFile1->Draw(file1DrawString);
        fChainFile2->Draw(file2DrawString);
      }
      else{
        fChainFile1->Draw(file1DrawString, lengthCutString);
        fChainFile2->Draw(file2DrawString, lengthCutString);
      }

      // Keep error while scaling
      hFile1->Sumw2();
      hFile2->Sumw2();

      // arb units, make sure to include underflow and overflow
      if (hFile1->Integral() > 0 && compType == 0) {
        hFile1->Scale(1./(hFile1->Integral()+hFile1->GetBinContent(0)+hFile1->GetBinContent(hFile1->GetNbinsX()+1)));
      }

      if (hFile2->Integral() > 0 && compType == 0) {
        hFile2->Scale(1./(hFile2->Integral()+hFile2->GetBinContent(0)+hFile2->GetBinContent(hFile2->GetNbinsX()+1)));
      }

      // set max extent of histogram
      double maxext = getMax(hFile1, hFile2);

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

        hFile2->GetXaxis()->SetTitle((trackPlotNames[j]).c_str());
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

        hFile2->GetXaxis()->SetTitle((trackPlotNames[j]).c_str());
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
        ratioPlotFile2->GetYaxis()->SetRangeUser(-1,1);
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
        commentsFile.open(outDir+"1TRACK_"+fileName+".comment");
        textWrap(comments.at(i).at(j),commentsFile,70) ;
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
        highChisqFile << fileName <<  " " << chisqv/(double)nBins << " is larger than "<< chisqNotifierCut << "\n";
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

      TString saveString = Form(outDir+"1TRACK_"+fileName+".png");
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
  int isCI = atoi(argv[9]);
  float chisqNotifierCut = atof(argv[10]);
  float trackLengthCut = atof(argv[11]);

  getTrackInformation(file1name, file1_dataormc, file1_label, file2name, file2_dataormc, file2_label, outDir, compType, isCI, chisqNotifierCut, trackLengthCut);
  return 0;

}
