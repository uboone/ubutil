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


// ------- Function to calculate something similar to a chi2 for shape comparison only -------- //

double calculateShapeChiSq(TH1D O, TH1D E){

    double O_norm = O.Integral();
    double E_norm = E.Integral();

    double chisq = 0;
    for (int i = 1; i < O.GetNbinsX()+1; i++){

        double O_i = O.GetBinContent(i);
        double E_i = E.GetBinContent(i);

        if ((O_i == 0 && E_i == 0)){
            chisq += 0;
        }
        else{
            chisq += (std::pow((O_i/O_norm)-(E_i/E_norm),2))/((O_i/std::pow(O_norm,2))+(E_i/std::pow(E_norm,2)));
        }
    }

    return chisq;

}

void CompareAlgos(TString rootfile1, TString algoname1, TString rootfile2, TString algoname2, float chisqNotifierCut)
{
  gStyle->SetOptStat(0);

  // Loop through root file 1 and look at all histograms
  // For each histogram, assume there is an equivalent one in root file 2 with the same name
  TFile *f1 = new TFile(rootfile1.Data(),"open");
  TFile *f2 = new TFile(rootfile2.Data(),"open");

  TCanvas *c1 = new TCanvas();

  TKey *key;
  TIter next(f1->GetListOfKeys());
  while ((key = (TKey*)next())){
    // Only want 1d histograms
    TClass *cl = gROOT->GetClass(key->GetClassName());
    if (!cl->InheritsFrom("TH1")) continue;

    // Now get this histogram
    TH1D *h_alg1 = (TH1D*)key->ReadObj();

    // And get the same histogram from file 2
    TString histname = key->GetName();
    TH1D *h_alg2 = (TH1D*)f2->Get(histname.Data());

    if (!h_alg2){
      std::cout << "Error: could not find " << histname << " in file " << rootfile2 << ". Not making this comparison plot." << std::endl;
    }

    h_alg1->SetLineWidth(2);
    h_alg1->SetStats(0);
    h_alg1->Sumw2();
    h_alg2->SetLineWidth(2);
    h_alg2->SetLineColor(2);
    h_alg2->SetStats(0);
    h_alg2->Sumw2();
    h_alg1->DrawNormalized("hist e0");
    h_alg2->DrawNormalized("hist e0 same");

  	// Resize y axis to show both histograms
  	double maxval = h_alg1->GetMaximum();
  	if (h_alg2->GetMaximum() > maxval){ maxval = h_alg2->GetMaximum(); }
  	h_alg1->GetYaxis()->SetRangeUser(0,maxval*1.3);

  	// Calculate chi2 between two plots and put in format for legend
  	// double chisqv = calculateChiSqDistance(vector1, vector2);
  	double chisqv = calculateShapeChiSq((*h_alg1), (*h_alg2));
  	TString chisq = Form("Shape #chi^{2}: %g", chisqv);
  	int nBins = std::max(h_alg1->GetNbinsX(), h_alg2->GetNbinsX());
  	TString NDF = Form("No. Bins: %i", nBins);
  	double chisqNDF = chisqv/(double)(nBins-1);
  	TString chisqNDFstr = Form("Shape #chi^{2}/(No. bins - 1): %g", chisqNDF);

		// If chisq is large, change background colour of canvas to make it really obvious
  	if (chisqNDF >= chisqNotifierCut/100.0){
  		c1->SetFillColor(kOrange-2);
  	}
    else{
      c1->SetFillColor(kWhite);
    }

  	// Make legend
  	TLegend *legend = new TLegend(0.55, 0.68, 0.89, 0.89);
          legend->AddEntry(h_alg1, algoname1.Data(),"l");
          legend->AddEntry(h_alg2, algoname2.Data(),"l");
  	legend->AddEntry((TObject*)0, chisq, "");
  	legend->AddEntry((TObject*)0, NDF, "");
  	legend->AddEntry((TObject*)0, chisqNDFstr, "");
  	// legend->SetLineWidth(0);
    legend->SetFillColor(c1->GetFillColor());
  	legend->Draw();

    TString saveString = Form("%s_%s_%s.png",histname.Data(),algoname1.Data(),algoname2.Data());
    c1->SaveAs(saveString, "png");

  } // end loop over keys
}
