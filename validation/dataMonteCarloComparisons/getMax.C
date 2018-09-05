double getMax(TH1* hData, TH1* hMC) {

    double datamax = hData->GetMaximum() * 1.25;
    double mcmax = hMC->GetMaximum() * 1.25;

    if (datamax > mcmax) return datamax;
    else if (mcmax > datamax) return mcmax;
    else return datamax;

}
