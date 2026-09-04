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

struct BumpHunterInfo {
  float global_pval{0.f};
  float significance{0.f};
  float mask_min{0.f};
  float mask_max{0.f};
  // false (not an exception) when bh_log_name could not be opened -
  // matches the original inline code's `bump_hunter = false` fallback.
  bool available{false};
};

// Reads and regex-parses a BumpHunter results JSON log. Moved verbatim
// from plot_postfit()'s own body (see doc/ACTIVITY_LOG.md's Tier 3 Chunk
// 11.B entry) - behavior, including the diagnostic prints, is unchanged.
BumpHunterInfo read_bumphunter_results(string const & bh_log_name) {

  BumpHunterInfo info;

  ifstream bh_log_stream(bh_log_name);

  cout << bh_log_name << endl;

  if (! bh_log_stream.is_open())
    return info;

  info.available = true;

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

  info.global_pval  = get_val("global_Pval");
  info.significance = get_val("significance");
  info.mask_min     = get_val("MaskMin");
  info.mask_max     = get_val("MaskMax");

  if (info.global_pval == 0.0f && info.significance == 0.0f) {
      cout << "WARNING: Could not parse values from " << bh_log_name << ". Check keys." << endl;
  }

  return info;

}

struct PostfitHistograms {
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

// Reads the ten residual/chi2/params histograms out of four input files,
// which must be supplied in pairs. `native` and `masked` may each be null
// - a null one is skipped entirely, matching the original's
// `if (in_file_native)`/`if (in_file_masked)` guards - but `native_params`
// must be non-null whenever `native` is, and `masked_params` whenever
// `masked` is: each params pointer is dereferenced unconditionally inside
// its partner's guard, with no null check of its own, so passing a null
// params pointer alongside a non-null partner crashes. That unconditional
// dereference is pre-existing behavior, moved verbatim from
// plot_postfit()'s own body and deliberately preserved rather than
// "fixed" here - see doc/ACTIVITY_LOG.md's Tier 3 Chunk 11.B entry. The
// paired-pointer requirement is stated explicitly because the earlier
// wording of this comment ("any of which may be null") described a
// contract the function does not actually honor (GitHub Copilot review,
// PR #6).
//
// Decision (Chunk 11's own "record the decision" point): the
// "exit(1) if native histograms missing" check stays inside this
// function, immediately after loading, rather than moving to the
// caller - it validates exactly what this function just built, so
// checking here means load_postfit_histograms() never hands back an
// incomplete result for a caller to separately re-validate.
PostfitHistograms load_postfit_histograms(
  TFile * native, TFile * masked, TFile * native_params, TFile * masked_params
) {

  PostfitHistograms h;

  if (native) {

    h.native = native->Get<TH1D>("Run3TLA_bkgonly/residuals");
    h.native_rebinned = native->Get<TH1D>("Run3TLA_bkgonly_rebinned/residuals");
    h.native_chi2 = native->Get<TH1D>("Run3TLA_bkgonly/chi2");
    h.native_chi2_rebinned = native->Get<TH1D>("Run3TLA_bkgonly_rebinned/chi2");
    h.native_params = native_params->Get<TH1D>("postfit_params");

  }

  if (masked) {

    h.masked = masked->Get<TH1D>("Run3TLA_bkgonly/residuals");
    h.masked_rebinned = masked->Get<TH1D>("Run3TLA_bkgonly_rebinned/residuals");
    h.masked_chi2 = masked->Get<TH1D>("Run3TLA_bkgonly/chi2");
    h.masked_chi2_rebinned = masked->Get<TH1D>("Run3TLA_bkgonly_rebinned/chi2");
    h.masked_params = masked_params->Get<TH1D>("postfit_params");

    h.masked->SetLineColor(kRed);
    h.masked_rebinned->SetLineColor(kRed);
    h.masked_params->SetLineColor(kRed);

  }

  if (! h.native || ! h.native_rebinned || ! h.native_chi2) {

    cout << "ERROR: native histogram missing" << endl;

    exit(1);

  }

  return h;

}

// Which of the three residual panels this call is drawing. The original
// code dispatched on pointer identity against the outer scope's
// h_native_params/h_native/h_native_rebinned variables; draw_residual_panel()
// has no such outer-scope pointers to compare against once extracted, so
// the caller states the kind explicitly instead - a deliberate,
// documented deviation from doc/TIER3_COMPLETION_PLAN.md Chunk 11's
// literal draw_residual_panel() signature, which omits this and the chi2/
// pval fields below entirely: without them, this function could not
// reproduce the per-panel-kind text/axis/legend differences the original
// single function's identity checks encoded. See doc/ACTIVITY_LOG.md's
// Tier 3 Chunk 11.B entry.
enum class ResidualPanelKind { kParams, kNative, kNativeRebinned };

// The chi2/ndof and p-value text this panel displays - computed once in
// plot_postfit() from the loaded histograms (unchanged from the
// original), then passed in per panel call since draw_residual_panel()
// no longer has access to the outer-scope histograms to compute them
// itself.
struct ResidualPanelInfo {
  ResidualPanelKind kind;
  float native_chi2_ndof{0.f};
  float native_pval{0.f};
  float masked_chi2_ndof{0.f};
  float masked_pval{0.f};
};

// Draws one residual panel and calls can->Print(out_file_name) - moved
// verbatim from the body of plot_postfit()'s original for-loop over
// {h_native_params, h_masked_params}/{h_native, h_masked}/
// {h_native_rebinned, h_masked_rebinned}, with every `h.first ==
// h_native_params`-style identity check replaced by `info.kind ==
// ResidualPanelKind::k...` (see the comment above ResidualPanelKind).
void draw_residual_panel(
  TCanvas * can,
  TH1D * first,
  TH1D * second,
  bool bump_hunter,
  BumpHunterInfo const & bh,
  char const * pars_str,
  char const * out_file_name,
  ResidualPanelInfo const & info
) {

  bool const is_params = (info.kind == ResidualPanelKind::kParams);
  bool const is_native = (info.kind == ResidualPanelKind::kNative);
  bool const is_native_rebinned = (info.kind == ResidualPanelKind::kNativeRebinned);

  float const
    range_min = first->GetBinLowEdge(1),
    range_max = first->GetBinLowEdge(first->GetNbinsX() + 1);

  can->Clear();

  if (is_params)
    first->GetYaxis()->SetRangeUser(-10., 50.);
  else {

    first->GetYaxis()->SetRangeUser(-5., 5.);
    first->SetTitle(";m_{jj} [GeV];residuals");

  }

  first->Draw(is_params ? "HIST" : "");

  auto line = make_unique<TLine>(range_min, 0., range_max, 0.);
  line->SetLineStyle(2);
  line->SetLineWidth(2);
  if (! is_params)
    line->Draw("same");

  auto leg = make_unique<TLegend>(0.65, 0.8, 0.95, 0.93);
  leg->SetFillStyle(0);
  leg->SetBorderSize(0);

  leg->AddEntry(first, "native fit", "l");

  auto bh_line_min = make_unique<TLine>(bh.mask_min, -5., bh.mask_min, 5.);
  bh_line_min->SetLineStyle(2);
  bh_line_min->SetLineWidth(2);
  bh_line_min->SetLineColor(kRed);

  auto bh_line_max = make_unique<TLine>(bh.mask_max, -5., bh.mask_max, 5.);
  bh_line_max->SetLineStyle(2);
  bh_line_max->SetLineWidth(2);
  bh_line_max->SetLineColor(kRed);

  if (bump_hunter) {

    second->Draw(is_params ? "same HIST" : "same");

    leg->AddEntry(second, "masked fit", "l");

    if (! is_params) {

      bh_line_min->Draw("same");
      bh_line_max->Draw("same");

      leg->AddEntry(bh_line_min.get(), "masked region", "l");

    }


  }

  leg->Draw("same");

  ATLASLabel(.2, .9, atlas_label.c_str());
  myText(.2, .85, 1, lumi_label.c_str());
  myText(.2, .8, 1, Form("%s parameter fit, bkg only", pars_str));

  if (! is_params)
    myText(.2, .75, 1, Form("range: %.0f - %.0f GeV", range_min, range_max));

  if (is_native_rebinned) {

    myText(.2, .35, 1, "Bump Hunter");

    if (bump_hunter) {

      myText(.2, .3, 1, Form("global p-val: %.4f", bh.global_pval));
      myText(.2, .25, 1, Form("significance: %.2f", bh.significance));
      myText(.2, .2, 1, Form("mask range: %.0f, %.0f GeV", bh.mask_min, bh.mask_max));

      myText(.75, .3, 1, "masked fit");
      myText(.75, .25, 1, Form("#chi^{2}/N_{dof}: %.2f", info.masked_chi2_ndof));
      myText(.75, .2, 1, Form("p-val: %.4f", info.masked_pval));

    } else
      myText(.2, .3, 1, "N/A");

    myText(.57, .3, 1, "native fit");
    myText(.57, .25, 1, Form("#chi^{2}/N_{dof}: %.2f", info.native_chi2_ndof));
    myText(.57, .2, 1, Form("p-val: %.4f", info.native_pval));

  } else if (is_native) {

    if (bump_hunter) {

      myText(.75, .3, 1, "masked fit");
      myText(.75, .25, 1, Form("#chi^{2}/N_{dof}: %.2f", info.masked_chi2_ndof));
      myText(.75, .2, 1, Form("p-val: %.4f", info.masked_pval));

    }

    myText(.57, .3, 1, "native fit");
    myText(.57, .25, 1, Form("#chi^{2}/N_{dof}: %.2f", info.native_chi2_ndof));
    myText(.57, .2, 1, Form("p-val: %.4f", info.native_pval));

  }

  can->Print(out_file_name);

}

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

  PostfitHistograms const h = load_postfit_histograms(
    in_file_native.get(), in_file_masked.get(), in_file_native_params.get(), in_file_masked_params.get()
  );

  BumpHunterInfo const bh_info = read_bumphunter_results(bh_log_name);
  bool const bump_hunter = plot_masked && bh_info.available;

  float
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

  native_chi2_ndof = h.native_chi2->GetBinContent(2);
  native_pval = h.native_chi2->GetBinContent(6);

  if (h.native_params) {
    native_nbkg = h.native_params->GetBinContent(1);
    h.native_params->GetXaxis()->SetRangeUser(1, h.native_params->GetNbinsX());
  }

  if (h.masked_params)
    masked_nbkg = h.masked_params->GetBinContent(1);

  native_chi2_ndof_rebinned = h.native_chi2_rebinned->GetBinContent(2);
  native_pval_rebinned = h.native_chi2_rebinned->GetBinContent(6);

  if (h.masked_chi2) {

    masked_chi2_ndof = h.masked_chi2->GetBinContent(2);
    masked_pval = h.masked_chi2->GetBinContent(6);

    masked_chi2_ndof_rebinned = h.masked_chi2_rebinned->GetBinContent(2);
    masked_pval_rebinned = h.masked_chi2_rebinned->GetBinContent(6);

  }

  gROOT->SetBatch(kTRUE);

  SetAtlasStyle();

  auto can = make_unique<TCanvas>("can", "", 0., 0., 800, 600);

  can->Print(Form("%s[", out_file_name));

  struct PanelCall {
    TH1D * first;
    TH1D * second;
    ResidualPanelInfo info;
  };

  vector<PanelCall> const panels{
    {
      h.native_params, h.masked_params,
      ResidualPanelInfo{ResidualPanelKind::kParams, native_chi2_ndof, native_pval, masked_chi2_ndof, masked_pval}
    },
    {
      h.native, h.masked,
      ResidualPanelInfo{ResidualPanelKind::kNative, native_chi2_ndof, native_pval, masked_chi2_ndof, masked_pval}
    },
    {
      h.native_rebinned, h.masked_rebinned,
      ResidualPanelInfo{
        ResidualPanelKind::kNativeRebinned,
        native_chi2_ndof_rebinned, native_pval_rebinned,
        masked_chi2_ndof_rebinned, masked_pval_rebinned
      }
    },
  };

  for (PanelCall const & panel : panels)
    draw_residual_panel(can.get(), panel.first, panel.second, bump_hunter, bh_info, pars_str, out_file_name, panel.info);

  can->Print(Form("%s]", out_file_name));

}
