double calculateChiSqDistance(TH1D* O, TH1D* E){

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
