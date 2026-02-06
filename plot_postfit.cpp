/*
makes plots:
  plots/puresidual.pdf

useage:
  root -l -q plot_puresidual.cpp
*/

#include <RVersion.h>

#include "atlasstyle-00-04-02/AtlasStyle.C"
#include "atlasstyle-00-04-02/AtlasLabels.C"
#include "atlasstyle-00-04-02/AtlasUtils.C"

#include <TROOT.h>
#include <TCanvas.h>
#include <TLegend.h>
#include <TFile.h>
#include <TLine.h>
#include <TH1D.h>

#include <nlohmann/json.hpp>
using json = nlohmann::json;

string const 
  atlas_label = "Work in progress",
  lumi_label = "#sqrt{s} = 13 TeV, 25 fb^{-1}";

void plot_postfit(char const * in_dir, char const * pars_str) {

  char const 
    * in_file_name_native = Form("%s/PostFit_anaFit_%sPar_bkgOnly.root", in_dir, pars_str),
    * in_file_name_masked = Form("%s/PostFit_anaFit_%sPar_bkgOnly_masked.root", in_dir, pars_str),
    * out_file_name = Form("%s/post_fit.pdf", in_dir),
    * bh_log_name = Form("%s/BHresults.json", in_dir);

	unique_ptr<TFile> in_file_native {TFile::Open(in_file_name_native, "READ")};
	unique_ptr<TFile> in_file_masked {TFile::Open(in_file_name_masked, "READ")};

  TH1D 
    * h_native{nullptr}, 
    * h_native_rebinned{nullptr}, 
    * h_native_chi2{nullptr}, 
    * h_native_chi2_rebinned{nullptr}, 
    * h_masked{nullptr},
    * h_masked_rebinned{nullptr},
    * h_masked_chi2{nullptr},
    * h_masked_chi2_rebinned{nullptr};

  if (in_file_native) {

    h_native = in_file_native->Get<TH1D>("Run3TLA_bkgonly/residuals");
    h_native_rebinned = in_file_native->Get<TH1D>("Run3TLA_bkgonly_rebinned/residuals");
    h_native_chi2 = in_file_native->Get<TH1D>("Run3TLA_bkgonly/chi2");
    h_native_chi2_rebinned = in_file_native->Get<TH1D>("Run3TLA_bkgonly_rebinned/chi2");

  }

  if (in_file_masked) {

    h_masked = in_file_masked->Get<TH1D>("Run3TLA_bkgonly/residuals");
    h_masked_rebinned = in_file_masked->Get<TH1D>("Run3TLA_bkgonly_rebinned/residuals");
    h_masked_chi2 = in_file_masked->Get<TH1D>("Run3TLA_bkgonly/chi2");
    h_masked_chi2_rebinned = in_file_masked->Get<TH1D>("Run3TLA_bkgonly_rebinned/chi2");

    h_masked->SetLineColor(kRed);
    h_masked_rebinned->SetLineColor(kRed);

  }

  if (! h_native || ! h_native_rebinned || ! h_native_chi2) {

    cout << "ERROR: native histogram missing" << endl;

    exit(1);

  }

  ifstream bh_log_stream(bh_log_name);
  json bh_log;
  bh_log_stream >> bh_log;

  float const
    bh_global_pval = bh_log.at("pyBHresult").at("global_Pval").get<float>(),
    bh_significance = bh_log.at("pyBHresult").at("significance").get<float>(),
    bh_mask_min = bh_log.at("MaskMin").get<float>(),
    bh_mask_max = bh_log.at("MaskMax").get<float>();

  float
    native_chi2_ndof{0.},
    masked_chi2_ndof{0.},
    native_pval{0.},
    masked_pval{0.},
    native_chi2_ndof_rebinned{0.},
    masked_chi2_ndof_rebinned{0.},
    native_pval_rebinned{0.},
    masked_pval_rebinned{0.};

  native_chi2_ndof = h_native_chi2->GetBinContent(2);
  native_pval = h_native_chi2->GetBinContent(6);

  native_chi2_ndof_rebinned = h_native_chi2_rebinned->GetBinContent(2);
  native_pval_rebinned = h_native_chi2_rebinned->GetBinContent(6);

  if (h_masked_chi2) {

    masked_chi2_ndof = h_masked_chi2->GetBinContent(2);
    masked_pval = h_masked_chi2->GetBinContent(6);

    masked_chi2_ndof_rebinned = h_masked_chi2_rebinned->GetBinContent(2);
    masked_pval_rebinned = h_masked_chi2_rebinned->GetBinContent(6);

  }

  gROOT->SetBatch(kTRUE);

  SetAtlasStyle();

  auto can = make_unique<TCanvas>("can", "", 0., 0., 800, 600);

  can->Print(Form("%s[", out_file_name));

  bool is_rebinned{false};

  for (pair<TH1D *, TH1D *> h : vector<pair<TH1D *, TH1D *>>{{h_native, h_masked}, {h_native_rebinned, h_masked_rebinned}}) {

    float const
      range_min = h.first->GetBinLowEdge(1),
      range_max = h.first->GetBinLowEdge(h.first->GetNbinsX() + 1);

    can->Clear();

    auto leg = make_unique<TLegend>(0.65, 0.8, 0.95, 0.93);
    leg->SetFillStyle(0);
    leg->SetBorderSize(0);

    h.first->GetYaxis()->SetRangeUser(-5., 5.);
    h.first->SetTitle(";m_{jj} [GeV];residuals");

    h.first->Draw();

    auto line = make_unique<TLine>(range_min, 0., range_max, 0.);
    line->SetLineStyle(2);
    line->SetLineWidth(2);
    line->Draw("same");
    
    auto bh_line_min = make_unique<TLine>(bh_mask_min, -5., bh_mask_min, 5.);
    bh_line_min->SetLineStyle(2);
    bh_line_min->SetLineWidth(2);
    bh_line_min->SetLineColor(kRed);
    bh_line_min->Draw("same");

    auto bh_line_max = make_unique<TLine>(bh_mask_max, -5., bh_mask_max, 5.);
    bh_line_max->SetLineStyle(2);
    bh_line_max->SetLineWidth(2);
    bh_line_max->SetLineColor(kRed);
    bh_line_max->Draw("same");

    if (h_masked) {

      leg->AddEntry(h.first, "native fit", "l");
      leg->AddEntry(h.second, "masked fit", "l");
      leg->AddEntry(bh_line_min.get(), "masked region", "l");

      h.second->Draw("same");

    }

    leg->Draw("same");

    ATLASLabel(.2, .9, atlas_label.c_str());
    myText(.2, .85, 1, lumi_label.c_str());
    myText(.2, .8, 1, Form("%s parameter fit, bkg only", pars_str));
    myText(.2, .75, 1, Form("range: %.0f - %.0f GeV", range_min, range_max));

    if (is_rebinned) {

      myText(.57, .3, 1, "native fit");
      myText(.57, .25, 1, Form("#chi^{2}/N_{dof}: %.2f", native_chi2_ndof_rebinned));
      myText(.57, .2, 1, Form("p-val: %.4f", native_pval_rebinned));

      myText(.75, .3, 1, "masked fit");
      myText(.75, .25, 1, Form("#chi^{2}/N_{dof}: %.2f", masked_chi2_ndof_rebinned));
      myText(.75, .2, 1, Form("p-val: %.4f", masked_pval_rebinned));


    } else {

      myText(.2, .35, 1, "Bump Hunter");
      myText(.2, .3, 1, Form("global p-val: %.4f", bh_global_pval));
      myText(.2, .25, 1, Form("significance: %.2f", bh_significance));
      myText(.2, .2, 1, Form("mask range: %.0f, %.0f GeV", bh_mask_min, bh_mask_max));

      myText(.57, .3, 1, "native fit");
      myText(.57, .25, 1, Form("#chi^{2}/N_{dof}: %.2f", native_chi2_ndof));
      myText(.57, .2, 1, Form("p-val: %.4f", native_pval));

      myText(.75, .3, 1, "masked fit");
      myText(.75, .25, 1, Form("#chi^{2}/N_{dof}: %.2f", masked_chi2_ndof));
      myText(.75, .2, 1, Form("p-val: %.4f", masked_pval));

    }

    can->Print(out_file_name);

    is_rebinned = true;

  }
  
  can->Print(Form("%s]", out_file_name));

}
