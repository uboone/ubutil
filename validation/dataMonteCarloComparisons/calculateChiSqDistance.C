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


// ------- Function to calculate something similar to a chi2 for shape comparison only -------- //

double calculateShapeChiSq(TH1D* O, TH1D* E){
    double O_norm = O->Integral();
    double E_norm = E->Integral();

    // std::cout << "O_norm = " << O_norm << ", E_norm = " << E_norm << std::endl;

    double chisq = 0;
    for (int i = 1; i < O->GetNbinsX()+1; i++){

        double O_i = O->GetBinContent(i);
        double E_i = E->GetBinContent(i);

        if ((O_i == 0 && E_i == 0)){
            chisq += 0;
        }
        else{
            chisq += (std::pow((O_i/O_norm)-(E_i/E_norm),2))/((O_i/std::pow(O_norm,2))+(E_i/std::pow(E_norm,2)));
        }
        // std::cout << "bin " << i << ", O_i = " << O_i << ", E_i = " << E_i << ", chisq = " << chisq << std::endl;
    }
    std::cout << chisq << ", " << chisq/((O_norm+E_norm)/2.) << std::endl;
    return chisq;
}


// ------- Function to calculate Pearson's chi2 -------- //

double calculatePearsonChiSq(TH1D* O, TH1D* E){

    double chisq = 0;
    for (int i = 1; i < O->GetNbinsX()+1; i++){

        double O_i = O->GetBinContent(i);
        double E_i = E->GetBinContent(i);

        if (O_i == 0 && E_i == 0){
            chisq += 0;
        }
        else{
            chisq += std::pow(O_i - E_i,2)/((O_i+E_i)/2);
        }

    }

    return chisq;

}
