// Exercises get_val() from ../plot_postfit_utils.h.
//
// Run with: root -l -b -q tests/test_plot_postfit_utils.C
// Reached from `python3 -m pytest tests -q` via test_plot_postfit_utils.py, which runs the
// command above as a subprocess - this file is the only piece of plot_postfit.cpp's
// decomposition with a real test, per the plan's decision that the rest is structural and is
// verified by comparing rendered PDFs instead.

#include "../plot_postfit_utils.h"

#include <cassert>
#include <iostream>
#include <string>

void test_plot_postfit_utils() {

  std::string const json =
      "{\"global_Pval\": 0.1234, \"significance\": -1.5e+00, \"MaskMin\": 500, \"other\": 1}";

  assert(get_val(json, "global_Pval") == 0.1234f);
  assert(get_val(json, "significance") == -1.5f);
  assert(get_val(json, "MaskMin") == 500.0f);

  // The absent-key case matters most: plot_postfit.cpp's only warning fires when both
  // global_Pval and significance read back as exactly 0.0f, so this is what makes a renamed or
  // missing key silent instead of caught.
  assert(get_val(json, "NotAKey") == 0.0f);

  std::cout << "test_plot_postfit_utils: OK" << std::endl;

}
