void setStyle(TH1* h, int dhc, TString histoYAxis) {

    gStyle->SetOptStat(0);
    h->GetYaxis()->SetTitleOffset(1.4);
    // nom data
    if ( dhc == 0 ) {

        h->SetLineColor(kBlack);
        h->SetMarkerStyle(20);
        h->SetMarkerColor(kBlack);
        h->SetMarkerSize(0.7);
        h->GetYaxis()->SetTitle(histoYAxis);
        h->SetLineWidth(2);
        h->GetXaxis()->SetTitleSize(0);
        h->GetXaxis()->SetLabelSize(0);
    }

    // nom mc
    else if ( dhc == 1 ) {

        h->SetLineColor(kOrange+10);
        h->GetYaxis()->SetTitle(histoYAxis);
        h->SetFillColorAlpha(kOrange+6, 0.5);
        h->SetMarkerColor(2);
        h->SetLineWidth(2);
        h->GetXaxis()->SetTitleSize(0);
        h->GetXaxis()->SetLabelSize(0);

    }

    // alt data
    else if ( dhc == 2 ) {

        h->SetLineColor(kOrange+10);
        h->SetMarkerStyle(20);
        h->SetMarkerColor(kOrange+10);
        h->SetMarkerSize(0.7);
        h->GetYaxis()->SetTitle(histoYAxis);
        h->SetLineWidth(2);
        h->GetXaxis()->SetTitleSize(0);
        h->GetXaxis()->SetLabelSize(0);

    }

    // alt mc
    else if ( dhc == 3 ) {

        h->SetLineColor(kBlack);
        h->GetYaxis()->SetTitle(histoYAxis);
        h->SetFillColorAlpha(kAzure+6, 0.5);
        h->SetMarkerColor(2);
        h->SetLineWidth(2);
        h->GetXaxis()->SetTitleSize(0);
        h->GetXaxis()->SetLabelSize(0);

    }

}

