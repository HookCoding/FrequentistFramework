// First-ever ROOT-macro unit test in this repository (see
// doc/TIER3_COMPLETION_PLAN.md Chunk 11 / doc/ACTIVITY_LOG.md's Tier 3
// Chunk 11.B entry): exercises read_bumphunter_results() in isolation,
// since it needs no TCanvas/graphics at all, against a small fixture
// BHresults.json (tests/root_macros/BHresults_sample.json - this
// repository's own J100 canonical run has none, since it is unmasked)
// plus a missing-file case. Invoked the same way plot_postfit.cpp's own
// macro-level test is: `root -l -b -q
// "tests/root_macros/test_read_bumphunter_results.cpp(\"<fixture>\")"`,
// from a thin Python/pytest wrapper
// (tests/test_read_bumphunter_results.py) matching the wrapper pattern
// already used for tests/test_plot_postfit_macro.py.

#include "../../plot_postfit.cpp"

void test_read_bumphunter_results(char const * bh_log_fixture) {

  bool ok{true};

  auto check_float = [&](char const * name, float actual, float expected) {
    if (fabs(actual - expected) > 1e-4f) {
      cout << "FAIL: " << name << " = " << actual << ", expected " << expected << endl;
      ok = false;
    }
  };

  BumpHunterInfo const info = read_bumphunter_results(bh_log_fixture);

  if (! info.available) {
    cout << "FAIL: expected available == true for existing fixture " << bh_log_fixture << endl;
    ok = false;
  }

  check_float("global_pval", info.global_pval, 0.1234f);
  check_float("significance", info.significance, 2.5f);
  check_float("mask_min", info.mask_min, 500.0f);
  check_float("mask_max", info.mask_max, 700.0f);

  string const missing_path = string(bh_log_fixture) + ".does_not_exist";
  BumpHunterInfo const missing_info = read_bumphunter_results(missing_path);

  if (missing_info.available) {
    cout << "FAIL: expected available == false for missing file " << missing_path << endl;
    ok = false;
  }

  check_float("missing global_pval", missing_info.global_pval, 0.0f);
  check_float("missing significance", missing_info.significance, 0.0f);
  check_float("missing mask_min", missing_info.mask_min, 0.0f);
  check_float("missing mask_max", missing_info.mask_max, 0.0f);

  if (! ok) {
    cout << "TEST_READ_BUMPHUNTER_RESULTS_FAILED" << endl;
    exit(1);
  }

  cout << "TEST_READ_BUMPHUNTER_RESULTS_OK" << endl;

}
