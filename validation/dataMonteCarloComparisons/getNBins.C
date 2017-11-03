int getNBins(TH1D *h){

    int nBins = 0;
    for (int i = 0; i < h->GetNbinsX(); i++){

        if (h->GetBinContent(i) !=0)
            nBins++;

    }

    return nBins;

}
