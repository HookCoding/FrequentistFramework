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

#include "plot_postfit_utils.h"

#include <TROOT.h>
#include <TCanvas.h>
#include <TLegend.h>
#include <TFile.h>
#include <TLine.h>
#include <TH1D.h>

bool const
  plot_masked{true};

string const
  atlas_label = "Work in progress",
  lumi_label = "#sqrt{s} = 13 TeV, 25 fb^{-1}";

// Owns the four input files for the whole call: every histogram load_histograms() below returns
// is workspace/file-owned and dies the moment its TFile is destroyed, so this struct - not its
// contents - is what plot_postfit() must keep alive until the last can->Print().
struct PostFitInputs {
  unique_ptr<TFile> native, masked, native_params, masked_params;
  string out_file_name, bh_log_name;
};

PostFitInputs open_inputs(char const * in_dir, char const * pars_str) {

  PostFitInputs inputs;

  inputs.native = unique_ptr<TFile>{TFile::Open(Form("%s/PostFit_anaFit_%sPar_bkgOnly.root", in_dir, pars_str), "READ")};
  inputs.masked = unique_ptr<TFile>{TFile::Open(Form("%s/PostFit_anaFit_%sPar_bkgOnly_masked.root", in_dir, pars_str), "READ")};
  inputs.native_params = unique_ptr<TFile>{TFile::Open(Form("%s/FitParameters_anaFit_%sPar_bkgOnly.root", in_dir, pars_str), "READ")};
  inputs.masked_params = unique_ptr<TFile>{TFile::Open(Form("%s/FitParameters_anaFit_%sPar_bkgOnly_masked.root", in_dir, pars_str), "READ")};

  inputs.out_file_name = Form("%s/post_fit.pdf", in_dir);
  inputs.bh_log_name = Form("%s/BHresults.json", in_dir);

  return inputs;

}

// The ten histograms this macro draws, non-owning: they live as long as the PostFitInputs above
// stays alive. h_native_params has no counterpart to the exit(1) guard in plot_postfit() that
// covers native/native_rebinned/native_chi2 - see KNOWN_ISSUES.md issue 56.
struct PostFitHistograms {
  TH1D
    * native{nullptr},
    * native_rebinned{nullptr},
    * native_chi2{nullptr},
    * native_chi2_rebinned{nullptr},
    * masked{nullptr},
    * masked_rebinned{nullptr},
    * masked_chi2{nullptr},
    * masked_chi2_rebinned{nullptr},
    * native_params{nullptr},
    * masked_params{nullptr};
};

PostFitHistograms load_histograms(PostFitInputs const & inputs, char const * chan) {

  PostFitHistograms h;

  if (inputs.native) {

    h.native = inputs.native->Get<TH1D>(Form("%s_bkgonly/residuals", chan));
    h.native_rebinned = inputs.native->Get<TH1D>(Form("%s_bkgonly_rebinned/residuals", chan));
    h.native_chi2 = inputs.native->Get<TH1D>(Form("%s_bkgonly/chi2", chan));
    h.native_chi2_rebinned = inputs.native->Get<TH1D>(Form("%s_bkgonly_rebinned/chi2", chan));
    h.native_params = inputs.native_params->Get<TH1D>("postfit_params");

  }

  if (inputs.masked) {

    h.masked = inputs.masked->Get<TH1D>(Form("%s_bkgonly/residuals", chan));
    h.masked_rebinned = inputs.masked->Get<TH1D>(Form("%s_bkgonly_rebinned/residuals", chan));
    h.masked_chi2 = inputs.masked->Get<TH1D>(Form("%s_bkgonly/chi2", chan));
    h.masked_chi2_rebinned = inputs.masked->Get<TH1D>(Form("%s_bkgonly_rebinned/chi2", chan));
    h.masked_params = inputs.masked_params->Get<TH1D>("postfit_params");

    h.masked->SetLineColor(kRed);
    h.masked_rebinned->SetLineColor(kRed);
    h.masked_params->SetLineColor(kRed);

  }

  return h;

}

// chi2/ndof, p-value and background yield off the summary histograms bins 2, 6 and 1
// respectively - each field zero-filled when its source histogram is null, so the same function
// serves the native block (chi2 always present, chi2_rebinned unguarded upstream, params
// independently guarded) and the masked block (all three independently absent when there is no
// masked fit) without the caller re-deriving three different null contracts.
struct FitSummary {
  float chi2_ndof{0.}, pval{0.}, chi2_ndof_rebinned{0.}, pval_rebinned{0.}, nbkg{0.};
};

FitSummary read_fit_summary(TH1D * h_chi2, TH1D * h_chi2_rebinned, TH1D * h_params) {

  FitSummary s;

  if (h_chi2) {
    s.chi2_ndof = h_chi2->GetBinContent(2);
    s.pval = h_chi2->GetBinContent(6);
  }

  if (h_chi2_rebinned) {
    s.chi2_ndof_rebinned = h_chi2_rebinned->GetBinContent(2);
    s.pval_rebinned = h_chi2_rebinned->GetBinContent(6);
  }

  if (h_params)
    s.nbkg = h_params->GetBinContent(1);

  return s;

}

// Which of the three pages being drawn this is, replacing repeated `h.first == h_native_params`
// / `h.first == h_native` pointer comparisons in both draw_panel() and draw_labels().
enum class PanelKind { Params, Native, Rebinned };

// The TLine/TLegend objects a page needs stay alive here, owned by the caller's loop variable,
// until after can->Print() - a helper that owned and returned void would destroy them the moment
// it returned, and the canvas would print with dangling pointers.
struct PanelArtifacts {
  unique_ptr<TLine> line, bh_line_min, bh_line_max;
  unique_ptr<TLegend> leg;
};

PanelArtifacts draw_panel(TH1D * h_first, TH1D * h_second, PanelKind kind, bool bump_hunter,
                           float bh_mask_min, float bh_mask_max, char const * pars_str,
                           float & range_min, float & range_max) {

  bool const is_params_panel = (kind == PanelKind::Params);

  PanelArtifacts a;

  range_min = h_first->GetBinLowEdge(1);
  range_max = h_first->GetBinLowEdge(h_first->GetNbinsX() + 1);

  if (is_params_panel)
    h_first->GetYaxis()->SetRangeUser(-10., 50.);
  else {

    h_first->GetYaxis()->SetRangeUser(-5., 5.);
    h_first->SetTitle(";m_{jj} [GeV];residuals");

  }

  h_first->Draw(is_params_panel ? "HIST" : "");

  a.line = make_unique<TLine>(range_min, 0., range_max, 0.);
  a.line->SetLineStyle(2);
  a.line->SetLineWidth(2);
  if (! is_params_panel)
    a.line->Draw("same");

  a.leg = make_unique<TLegend>(0.65, 0.8, 0.95, 0.93);
  a.leg->SetFillStyle(0);
  a.leg->SetBorderSize(0);

  a.leg->AddEntry(h_first, "native fit", "l");

  a.bh_line_min = make_unique<TLine>(bh_mask_min, -5., bh_mask_min, 5.);
  a.bh_line_min->SetLineStyle(2);
  a.bh_line_min->SetLineWidth(2);
  a.bh_line_min->SetLineColor(kRed);

  a.bh_line_max = make_unique<TLine>(bh_mask_max, -5., bh_mask_max, 5.);
  a.bh_line_max->SetLineStyle(2);
  a.bh_line_max->SetLineWidth(2);
  a.bh_line_max->SetLineColor(kRed);

  if (bump_hunter) {

    // h_second is drawn on the strength of bump_hunter alone, i.e. of BHresults.json existing -
    // not on whether the masked PostFit/FitParameters files themselves opened. See
    // KNOWN_ISSUES.md issue 57.
    h_second->Draw(is_params_panel ? "same HIST" : "same");

    a.leg->AddEntry(h_second, "masked fit", "l");

    if (! is_params_panel) {

      a.bh_line_min->Draw("same");
      a.bh_line_max->Draw("same");

      a.leg->AddEntry(a.bh_line_min.get(), "masked region", "l");

    }


  }

  a.leg->Draw("same");

  ATLASLabel(.2, .9, atlas_label.c_str());
  myText(.2, .85, 1, lumi_label.c_str());
  myText(.2, .8, 1, Form("%s parameter fit, bkg only", pars_str));

  if (! is_params_panel)
    myText(.2, .75, 1, Form("range: %.0f - %.0f GeV", range_min, range_max));

  return a;

}

// The chi2/pval/Bump Hunter summary boxes, specific to which of the three pages this is - a
// no-op for PanelKind::Params, matching neither branch being taken there today.
void draw_labels(PanelKind kind, bool bump_hunter, FitSummary const & native_summary,
                  FitSummary const & masked_summary, float bh_global_pval, float bh_significance,
                  float bh_mask_min, float bh_mask_max) {

  if (kind == PanelKind::Rebinned) {

    myText(.2, .35, 1, "Bump Hunter");

    if (bump_hunter) {

      myText(.2, .3, 1, Form("global p-val: %.4f", bh_global_pval));
      myText(.2, .25, 1, Form("significance: %.2f", bh_significance));
      myText(.2, .2, 1, Form("mask range: %.0f, %.0f GeV", bh_mask_min, bh_mask_max));

      myText(.75, .3, 1, "masked fit");
      myText(.75, .25, 1, Form("#chi^{2}/N_{dof}: %.2f", masked_summary.chi2_ndof_rebinned));
      myText(.75, .2, 1, Form("p-val: %.4f", masked_summary.pval_rebinned));

    } else
      myText(.2, .3, 1, "N/A");

    myText(.57, .3, 1, "native fit");
    myText(.57, .25, 1, Form("#chi^{2}/N_{dof}: %.2f", native_summary.chi2_ndof_rebinned));
    myText(.57, .2, 1, Form("p-val: %.4f", native_summary.pval_rebinned));

  } else if (kind == PanelKind::Native) {

    if (bump_hunter) {

      myText(.75, .3, 1, "masked fit");
      myText(.75, .25, 1, Form("#chi^{2}/N_{dof}: %.2f", masked_summary.chi2_ndof));
      myText(.75, .2, 1, Form("p-val: %.4f", masked_summary.pval));

    }

    myText(.57, .3, 1, "native fit");
    myText(.57, .25, 1, Form("#chi^{2}/N_{dof}: %.2f", native_summary.chi2_ndof));
    myText(.57, .2, 1, Form("p-val: %.4f", native_summary.pval));

  }

}

void plot_postfit(char const * in_dir, char const * pars_str, char const * chan = "Run3TLA") {

  PostFitInputs inputs = open_inputs(in_dir, pars_str);
  PostFitHistograms h = load_histograms(inputs, chan);

  if (! h.native || ! h.native_rebinned || ! h.native_chi2) {

    cout << "ERROR: native histogram missing" << endl;

    exit(1);

  }

  float
    bh_global_pval{0.},
    bh_significance{0.},
    bh_mask_min{0.},
    bh_mask_max{0.};

  ifstream bh_log_stream(inputs.bh_log_name);

  cout << inputs.bh_log_name << endl;

  bool bump_hunter{plot_masked};

  if (bh_log_stream.is_open()) {

    stringstream buffer;
    buffer << bh_log_stream.rdbuf();
    string json_str = buffer.str();

    bh_global_pval  = get_val(json_str, "global_Pval");
    bh_significance = get_val(json_str, "significance");
    bh_mask_min     = get_val(json_str, "MaskMin");
    bh_mask_max     = get_val(json_str, "MaskMax");

    if (bh_global_pval == 0.0f && bh_significance == 0.0f) {
        cout << "WARNING: Could not parse values from " << inputs.bh_log_name << ". Check keys." << endl;
    }


  } else
    bump_hunter = false;

  if (h.native_params)
    h.native_params->GetXaxis()->SetRangeUser(1, h.native_params->GetNbinsX());

  FitSummary const native_summary = read_fit_summary(h.native_chi2, h.native_chi2_rebinned, h.native_params);
  FitSummary const masked_summary = read_fit_summary(h.masked_chi2, h.masked_chi2_rebinned, h.masked_params);

  gROOT->SetBatch(kTRUE);

  SetAtlasStyle();

  auto can = make_unique<TCanvas>("can", "", 0., 0., 800, 600);

  can->Print(Form("%s[", inputs.out_file_name.c_str()));

  for (pair<TH1D *, TH1D *> h_pair : vector<pair<TH1D *, TH1D *>>{{h.native_params, h.masked_params}, {h.native, h.masked}, {h.native_rebinned, h.masked_rebinned}}) {

    can->Clear();

    PanelKind const kind = h_pair.first == h.native_params ? PanelKind::Params
                          : h_pair.first == h.native        ? PanelKind::Native
                          :                                    PanelKind::Rebinned;

    float range_min{0.}, range_max{0.};

    PanelArtifacts artifacts = draw_panel(h_pair.first, h_pair.second, kind, bump_hunter,
                                           bh_mask_min, bh_mask_max, pars_str, range_min, range_max);

    draw_labels(kind, bump_hunter, native_summary, masked_summary,
                bh_global_pval, bh_significance, bh_mask_min, bh_mask_max);

    can->Print(inputs.out_file_name.c_str());

  }

  can->Print(Form("%s]", inputs.out_file_name.c_str()));

}
