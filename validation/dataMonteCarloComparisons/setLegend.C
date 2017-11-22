void setLegend(TH1* hfile1, int file1_dmc, TString file1_label, TH1* hfile2, int file2_dmc, TString file2_label)
{

    TPaveText *pt2 = new TPaveText(.15, .78, .25, .85, "NDC");
    pt2->AddText("U Plane");
    pt2->SetShadowColor(0);
    pt2->SetFillStyle(0);
    pt2->SetLineColor(0);
    pt2->SetBorderSize(0);
    TPaveText *pt3 = new TPaveText(.15, .78, .25, .85, "NDC");
    pt3->AddText("V Plane");
    pt3->SetShadowColor(0);
    pt3->SetFillStyle(0);
    pt3->SetLineColor(0);
    pt3->SetBorderSize(0);
    TPaveText *pt4 = new TPaveText(.15, .78, .25, .85, "NDC");
    pt4->AddText("Y Plane");
    pt4->SetShadowColor(0);
    pt4->SetFillStyle(0);
    pt4->SetLineColor(0);
    pt4->SetBorderSize(0);

    if (file1_dmc == 0 && file2_dmc == 1){
        TLegend* legfile1 = new TLegend(0.11, 0.91, 0.5, 1.0);
        legfile1->AddEntry(hfile1, file1_label, "lep");
        legfile1->SetBorderSize(0);
        legfile1->SetTextAlign(12);
        legfile1->SetTextSize(0.05);
        legfile1->Draw("same");

        TLegend* legfile2 = new TLegend(0.5, 0.91, 0.89, 1.0);
        legfile2->AddEntry(hfile2, file2_label);
        legfile2->SetTextAlign(12);
        legfile2->SetTextSize(0.05);
        legfile2->SetBorderSize(0);
        legfile2->Draw("same");
    }

    if (file1_dmc == 3 && file2_dmc == 1){
        TLegend* legfile1 = new TLegend(0.11, 0.91, 0.5, 1.0);
        legfile1->AddEntry(hfile1, file1_label);
        legfile1->SetBorderSize(0);
        legfile1->SetTextAlign(12);
        legfile1->SetTextSize(0.05);
        legfile1->Draw("same");

        TLegend* legfile2 = new TLegend(0.50, 0.91, 0.89, 1.0);
        legfile2->AddEntry(hfile2, file2_label);
        legfile2->SetTextAlign(12);
        legfile2->SetTextSize(0.05);
        legfile2->SetBorderSize(0);
        legfile2->Draw("same");
    }

    if (file1_dmc == 0 && file2_dmc == 2){
        TLegend* legfile1 = new TLegend(0.11, 0.91, 0.5, 1.0);
        legfile1->AddEntry(hfile1, file1_label, "lep");
        legfile1->SetBorderSize(0);
        legfile1->SetTextAlign(12);
        legfile1->SetTextSize(0.05);
        legfile1->Draw("same");

        TLegend* legfile2 = new TLegend(0.5, 0.91, 0.89, 1.0);
        legfile2->AddEntry(hfile2, file2_label, "lep");
        legfile2->SetTextAlign(12);
        legfile2->SetTextSize(0.05);
        legfile2->SetBorderSize(0);
        legfile2->Draw("same");
    }



}

