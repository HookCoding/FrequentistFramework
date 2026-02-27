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

#include <regex>

bool const
  plot_masked{true};

string const 
  atlas_label = "Work in progress",
  lumi_label = "#sqrt{s} = 13 TeV, 25 fb^{-1}";

void plot_postfit(char const * in_dir, char const * pars_str) {

  char const 
    * in_file_name_native = Form("%s/PostFit_anaFit_%sPar_bkgOnly.root", in_dir, pars_str),
    * in_file_name_masked = Form("%s/PostFit_anaFit_%sPar_bkgOnly_masked.root", in_dir, pars_str),
    * in_file_name_native_params = Form("%s/FitParameters_anaFit_%sPar_bkgOnly.root", in_dir, pars_str),
    * in_file_name_masked_params = Form("%s/FitParameters_anaFit_%sPar_bkgOnly_masked.root", in_dir, pars_str),
    * out_file_name = Form("%s/post_fit.pdf", in_dir),
    * bh_log_name = Form("%s/BHresults.json", in_dir);

	unique_ptr<TFile> in_file_native {TFile::Open(in_file_name_native, "READ")};
	unique_ptr<TFile> in_file_masked {TFile::Open(in_file_name_masked, "READ")};
	unique_ptr<TFile> in_file_native_params {TFile::Open(in_file_name_native_params, "READ")};
	unique_ptr<TFile> in_file_masked_params {TFile::Open(in_file_name_masked_params, "READ")};

  TH1D 
    * h_native{nullptr}, 
    * h_native_rebinned{nullptr}, 
    * h_native_chi2{nullptr}, 
    * h_native_chi2_rebinned{nullptr}, 
    * h_masked{nullptr},
    * h_masked_rebinned{nullptr},
    * h_masked_chi2{nullptr},
    * h_masked_chi2_rebinned{nullptr},
    * h_native_params{nullptr},
    * h_masked_params{nullptr}; 

  if (in_file_native) {

    h_native = in_file_native->Get<TH1D>("Run3TLA_bkgonly/residuals");
    h_native_rebinned = in_file_native->Get<TH1D>("Run3TLA_bkgonly_rebinned/residuals");
    h_native_chi2 = in_file_native->Get<TH1D>("Run3TLA_bkgonly/chi2");
    h_native_chi2_rebinned = in_file_native->Get<TH1D>("Run3TLA_bkgonly_rebinned/chi2");
    h_native_params = in_file_native_params->Get<TH1D>("postfit_params");

  }

  if (in_file_masked) {

    h_masked = in_file_masked->Get<TH1D>("Run3TLA_bkgonly/residuals");
    h_masked_rebinned = in_file_masked->Get<TH1D>("Run3TLA_bkgonly_rebinned/residuals");
    h_masked_chi2 = in_file_masked->Get<TH1D>("Run3TLA_bkgonly/chi2");
    h_masked_chi2_rebinned = in_file_masked->Get<TH1D>("Run3TLA_bkgonly_rebinned/chi2");
    h_masked_params = in_file_masked_params->Get<TH1D>("postfit_params");

    h_masked->SetLineColor(kRed);
    h_masked_rebinned->SetLineColor(kRed);
    h_masked_params->SetLineColor(kRed);

  }

  if (! h_native || ! h_native_rebinned || ! h_native_chi2) {

    cout << "ERROR: native histogram missing" << endl;

    exit(1);

  }

  float
    bh_global_pval{0.},
    bh_significance{0.},
    bh_mask_min{0.},
    bh_mask_max{0.},
    native_chi2_ndof{0.},
    masked_chi2_ndof{0.},
    native_pval{0.},
    masked_pval{0.},
    native_chi2_ndof_rebinned{0.},
    masked_chi2_ndof_rebinned{0.},
    native_pval_rebinned{0.},
    masked_pval_rebinned{0.},
    native_nbkg{0.},
    masked_nbkg{0.};

  ifstream bh_log_stream(bh_log_name);

  cout << bh_log_name << endl;

  bool bump_hunter{plot_masked};

  if (bh_log_stream.is_open()) {

    stringstream buffer;
    buffer << bh_log_stream.rdbuf();
    string json_str = buffer.str();

    auto get_val = [&](string key) {
      regex re("\"" + key + "\"\\s*:\\s*([-+]?[0-9]*\\.?[0-9]+(?:[eE][-+]?[0-9]+)?)");
      smatch match;
      if (regex_search(json_str, match, re) && match.size() > 1) {
        return stof(match.str(1));
      }
      return 0.0f;
    };

    bh_global_pval  = get_val("global_Pval");
    bh_significance = get_val("significance");
    bh_mask_min     = get_val("MaskMin");
    bh_mask_max     = get_val("MaskMax");

    if (bh_global_pval == 0.0f && bh_significance == 0.0f) {
        cout << "WARNING: Could not parse values from " << bh_log_name << ". Check keys." << endl;
    }


  } else
    bump_hunter = false;

  native_chi2_ndof = h_native_chi2->GetBinContent(2);
  native_pval = h_native_chi2->GetBinContent(6);

  if (h_native_params) {
    native_nbkg = h_native_params->GetBinContent(1);
    h_native_params->GetXaxis()->SetRangeUser(1, h_native_params->GetNbinsX());
  }

  if (h_masked_params)
    masked_nbkg = h_masked_params->GetBinContent(1);

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

  for (pair<TH1D *, TH1D *> h : vector<pair<TH1D *, TH1D *>>{{h_native_params, h_masked_params}, {h_native, h_masked}, {h_native_rebinned, h_masked_rebinned}}) {

    float const
      range_min = h.first->GetBinLowEdge(1),
      range_max = h.first->GetBinLowEdge(h.first->GetNbinsX() + 1);

    can->Clear();


    if (h.first == h_native_params)
      h.first->GetYaxis()->SetRangeUser(-10., 50.);
    else {

      h.first->GetYaxis()->SetRangeUser(-5., 5.);
      h.first->SetTitle(";m_{jj} [GeV];residuals");

    }


    h.first->Draw(h.first == h_native_params ? "HIST" : "");

    auto line = make_unique<TLine>(range_min, 0., range_max, 0.);
    line->SetLineStyle(2);
    line->SetLineWidth(2);
    if (h.first != h_native_params)
      line->Draw("same");

    auto leg = make_unique<TLegend>(0.65, 0.8, 0.95, 0.93);
    leg->SetFillStyle(0);
    leg->SetBorderSize(0);

    leg->AddEntry(h.first, "native fit", "l");

    auto bh_line_min = make_unique<TLine>(bh_mask_min, -5., bh_mask_min, 5.);
    bh_line_min->SetLineStyle(2);
    bh_line_min->SetLineWidth(2);
    bh_line_min->SetLineColor(kRed);

    auto bh_line_max = make_unique<TLine>(bh_mask_max, -5., bh_mask_max, 5.);
    bh_line_max->SetLineStyle(2);
    bh_line_max->SetLineWidth(2);
    bh_line_max->SetLineColor(kRed);

    if (bump_hunter) {

      h.second->Draw(h.first == h_native_params ? "same HIST" : "same");

      leg->AddEntry(h.second, "masked fit", "l");

      if (h.first != h_native_params) {

        bh_line_min->Draw("same");
        bh_line_max->Draw("same");

        leg->AddEntry(bh_line_min.get(), "masked region", "l");

      }


    }

    leg->Draw("same");

    ATLASLabel(.2, .9, atlas_label.c_str());
    myText(.2, .85, 1, lumi_label.c_str());
    myText(.2, .8, 1, Form("%s parameter fit, bkg only", pars_str));
    
    if (h.first != h_native_params)
      myText(.2, .75, 1, Form("range: %.0f - %.0f GeV", range_min, range_max));

    if (h.first == h_native_rebinned) {

      myText(.2, .35, 1, "Bump Hunter");

      if (bump_hunter) {

        myText(.2, .3, 1, Form("global p-val: %.4f", bh_global_pval));
        myText(.2, .25, 1, Form("significance: %.2f", bh_significance));
        myText(.2, .2, 1, Form("mask range: %.0f, %.0f GeV", bh_mask_min, bh_mask_max));

        myText(.75, .3, 1, "masked fit");
        myText(.75, .25, 1, Form("#chi^{2}/N_{dof}: %.2f", masked_chi2_ndof_rebinned));
        myText(.75, .2, 1, Form("p-val: %.4f", masked_pval_rebinned));

      } else
        myText(.2, .3, 1, "N/A");

      myText(.57, .3, 1, "native fit");
      myText(.57, .25, 1, Form("#chi^{2}/N_{dof}: %.2f", native_chi2_ndof_rebinned));
      myText(.57, .2, 1, Form("p-val: %.4f", native_pval_rebinned));

    } else if (h.first == h_native) {

      if (bump_hunter) {

        myText(.75, .3, 1, "masked fit");
        myText(.75, .25, 1, Form("#chi^{2}/N_{dof}: %.2f", masked_chi2_ndof));
        myText(.75, .2, 1, Form("p-val: %.4f", masked_pval));

      }

      myText(.57, .3, 1, "native fit");
      myText(.57, .25, 1, Form("#chi^{2}/N_{dof}: %.2f", native_chi2_ndof));
      myText(.57, .2, 1, Form("p-val: %.4f", native_pval));

    }

    can->Print(out_file_name);

  }
  
  can->Print(Form("%s]", out_file_name));

}
