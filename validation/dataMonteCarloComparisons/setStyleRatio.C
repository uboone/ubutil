void setStyleRatio(TH1D* h, TString file1_label, TString file2_label){
    h->SetNdivisions(505, "Y");
    h->GetYaxis()->SetTitle("#frac{("+file1_label+")-("+file2_label+")}{("+file2_label+")}");
    h->GetYaxis()->SetTitleOffset(0.57);
    h->GetYaxis()->SetTitleSize(0.07);
    h->GetYaxis()->SetLabelSize(0.075);
    h->GetXaxis()->SetTitleSize(0.09);
    h->GetXaxis()->SetLabelSize(0.075);
}

