// Shared by plot_postfit.cpp and tests/test_plot_postfit_utils.C.
#pragma once

#include <regex>
#include <string>

// Scrapes one numeric value out of a flat-ish JSON blob by key. Returns 0.0f when the key is
// absent - callers that warn on an all-zero read (plot_postfit.cpp's "global_Pval and
// significance both zero" check) rely on that, so a renamed or missing key is silent rather than
// an error.
inline float get_val(std::string const & json_str, std::string const & key) {
  std::regex re("\"" + key + "\"\\s*:\\s*([-+]?[0-9]*\\.?[0-9]+(?:[eE][-+]?[0-9]+)?)");
  std::smatch match;
  if (std::regex_search(json_str, match, re) && match.size() > 1) {
    return std::stof(match.str(1));
  }
  return 0.0f;
}
