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

void CompareAlgos(TString rootfile, float chisqNotifierCut)
{
  gStyle->SetOptStat(0);
  // List names of algorithms to compare. Every algorithm in Algos1 will be compared to every algorithm in Algos2
  std::vector<std::string> Algos1 = {"pandora"};
  std::vector<std::string> Algos2 = {"pandoraCosmic"};

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

  // Loop through root file and look at all histograms
  TFile *f = new TFile(rootfile.Data(),"open");
  TKey *key;
  TIter next(f->GetListOfKeys());
  while ((key = (TKey*)next())){
    // Only want 1d histograms
    TClass *cl = gROOT->GetClass(key->GetClassName());
    if (!cl->InheritsFrom("TH1")) continue;

    // Now loop through algorithms in Algos1. For each algorithm, check if this histogram matches that algorithm. If it does, find histograms to match the algorithms in Algos2 and make plots
    for (size_t i_alg1 = 0; i_alg1 < Algos1.size(); i_alg1++){
      std::string algname1 = std::string(std::string("_")+Algos1.at(i_alg1)+std::string("_"));
      TString histname = key->GetName();
      if (!histname.Contains(algname1.c_str())) continue;

      // Only consider "file 1" plots so we don't double-count all the plots
      if (!histname.Contains("file1")) continue;

      // Get histogram from key
      TH1D *h_alg1 = (TH1D*)key->ReadObj();

      // Now we have a histogram with a name that looks like <plotname>_<algorithmname>_file1. We want to find matching histograms using the algorithm names in Algos2.
      std::string removechars = std::string(algname1+std::string("file1"));
      for (int i_char=removechars.size(); i_char>0; i_char--){
        histname.Remove(TString::EStripType::kTrailing,removechars.at(i_char-1));
      }

      // Loop through algos in Algos2 and plot comparisons
      for (size_t i_alg2 = 0; i_alg2 < Algos2.size(); i_alg2++){
        TString histname2 = Form("%s_%s_file1", histname.Data(),Algos2.at(i_alg2).c_str());

        TH1D *h_alg2 = nullptr;
        h_alg2 = (TH1D*)f->Get(histname2.Data());
        if (h_alg2==nullptr) continue;

        // Now make comparison plots!
        setStyle(h_alg1, 3, h_alg1->GetYaxis()->GetTitle());
        setStyle(h_alg2, 1, h_alg2->GetYaxis()->GetTitle());
        topPad->cd();

        // draw MC histo error bars...
        double maxext = getMax(h_alg1, h_alg2);
        h_alg2->Draw("e2");
        h_alg2->GetYaxis()->SetRangeUser(0,maxext);

        // clone, and draw as histogram
        TH1F* h_alg2c = (TH1F*)h_alg2->Clone("h_alg2c");
        h_alg2c->SetDirectory(0);
        h_alg2c->SetFillColor(0);
        h_alg2c->Draw("hist same");

        // and data
        h_alg1->Draw("e2same");
        TH1F* h_alg1c = (TH1F*)h_alg1->Clone("h_alg1c");
        h_alg1c->SetDirectory(0);
        h_alg1c->SetFillColor(0);
        h_alg1c->Draw("hist same");

        setLegend(h_alg1, 3, Algos1.at(i_alg1), h_alg2, 1, Algos2.at(i_alg2));

        bottomPad->cd();
        TH1D *ratioPlotAlg2 = (TH1D*)h_alg2->Clone("ratioPlotAlg2");
        ratioPlotAlg2->Add(h_alg2, -1);
        ratioPlotAlg2->Divide(h_alg2);
        setStyleRatio(ratioPlotAlg2, Algos1.at(i_alg1), Algos2.at(i_alg2));
        ratioPlotAlg2->GetYaxis()->SetRangeUser(-1,1);
        ratioPlotAlg2->Draw("hist");
        TH1D* ratioPlotAlg2C = (TH1D*)ratioPlotAlg2->Clone("ratioPlotAlg2C");
        ratioPlotAlg2C->SetFillColor(0);
        ratioPlotAlg2C->Draw("histsame");

        TH1D *ratioPlotAlg1 = (TH1D*)h_alg1->Clone("ratioPlotAlg1");
        ratioPlotAlg1->Add(h_alg2, -1);
        ratioPlotAlg1->Divide(h_alg2);
        ratioPlotAlg1->Draw("e2same");
        TH1D* ratioPlotAlg1C = (TH1D*)ratioPlotAlg1->Clone("ratioPlotAlg1C");
        ratioPlotAlg1C->SetFillColor(0);
        ratioPlotAlg1C->Draw("histsame");

        // Now calculate chi2 and add over/underflow information to the plot
        double chisqv = calculatePearsonChiSq(h_alg1, h_alg2);
        int nBins = std::max(getNBins(h_alg1),getNBins(h_alg2))-1;
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

        double totalEntries1 = h_alg1->Integral() + h_alg1->GetBinContent(0) + h_alg1->GetBinContent(h_alg1->GetNbinsX()+1);
        double underflowFrac1 = h_alg1->GetBinContent(0)/totalEntries1;
        double overflowFrac1 =  h_alg1->GetBinContent(h_alg1->GetNbinsX()+1)/totalEntries1;

        double totalEntries2 = h_alg2->Integral() + h_alg2->GetBinContent(0) + h_alg2->GetBinContent(h_alg2->GetNbinsX()+1);
        double underflowFrac2 = h_alg2->GetBinContent(0)/totalEntries2;
        double overflowFrac2 = h_alg2->GetBinContent(h_alg2->GetNbinsX()+1)/totalEntries2;

        TString underOver1 = Form("UF: %g  OF: %g", underflowFrac1, overflowFrac1);
        TString underOver2 = Form("UF: %g  OF: %g", underflowFrac2, overflowFrac2);

        TPaveText *pt_ufofl = new TPaveText(0.5, 0.73, 0.9, 0.78, "NDC");
        pt_ufofl->AddText(Algos1.at(i_alg1)+"/"+underOver1);
        pt_ufofl->SetFillStyle(0);
        pt_ufofl->SetBorderSize(0);
        pt_ufofl->SetTextAlign(31);
        pt_ufofl->Draw("same");

        TPaveText *pt_ufofr = new TPaveText(0.5, 0.68, 0.9, 0.73, "NDC");
        pt_ufofr->AddText(Algos2.at(i_alg2)+"/"+underOver2);
        pt_ufofr->SetFillStyle(0);
        pt_ufofr->SetBorderSize(0);
        pt_ufofr->SetTextAlign(31);
        pt_ufofr->Draw("same");

        // If chisq is large, change background colour of canvas to make it really obvious
        if (chisqv/double(nBins) >= chisqNotifierCut){
          c1->SetFillColor(kOrange-2);
          topPad->SetFillColor(kOrange-2);
          bottomPad->SetFillColor(kOrange-2);

        }
        else{ // Canvas background should be white
          c1->SetFillColor(kWhite);
          topPad->SetFillColor(kWhite);
          bottomPad->SetFillColor(kWhite);
        }

        TString saveString = Form("%s_%s_%s.png",histname.Data(),Algos1.at(i_alg1).c_str(),Algos2.at(i_alg2).c_str());
        c1->SaveAs(saveString, "png");

      } // end loop over Algos2
    } // end loop over Algos1

  } // end loop over keys
}
