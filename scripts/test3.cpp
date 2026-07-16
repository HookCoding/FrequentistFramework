{
/*

  this is an example to demonstrate that the chi2 calculation of roofit over ranges 
  (e.g. for masked fits) changed between the root versions root-v6-26-08 and root-v6-28-00

  a uniform pdf on the range 0. to 1. with integral 11. is created and compared with
  a uniform histogram with 10 bins, also on the range 0. to 1. but with integral 11.

  chi2 is calculated using Poisson errors first without specifying a range
  and then with the ranges
  full (0. to 1.)
  lo (0. to .5)
  hi (.5 to 1.)
  and the union lo,hi (0. to 1.)

  output with root-v6-26-08:
  > chi2()      = 0.0189114
  > chi2(full)  = 0.0189114
  > chi2(lo)    = 1.36162
  > chi2(hi)    = 1.36162
  > chi2(lo,hi) = 2.72324

  Note: chi2(lo,hi) / chi2() = 144 (exactly) = 12^2 (12: number of bins including under- and overflow)

  output with root-v6-28-00:
  > chi2()      = 0.0189114
  > chi2(full)  = 0.0189114
  > chi2(lo)    = 4.60108
  > chi2(hi)    = 4.60108
  > chi2(lo,hi) = 9.20217

  Note: chi2(lo,hi) / chi2() = 486.59 (not an integer)
  chi2(lo), chi2(hi), chi2(lo,hi) all differ by a factor of 3.38 from the root-v6-26-08 results

  to recreate run on lxplus with:
  root -l -q test.cpp

  after setup once with
  lsetup "views LCG_102a x86_64-centos9-gcc11-opt" # root v6-26-08

  and once with
  lsetup "views LCG_103 x86_64-centos9-gcc11-opt" # root v6-28-00

*/

  using namespace RooFit;

  RooRealVar x("x", "x", 0., 1.);
  x.setRange("lo", 0., .5);
  x.setRange("hi", .5, 1.);
  x.setRange("full", 0., 1.);

  RooUniform uniform("uniform", "", x);
  RooRealVar nbkg("nbkg", "", 11.);
  RooExtendPdf pdf("pdf", "", uniform, nbkg);

  TH1D h("h", "h", 10, 0., 1.);

  for (int i = 1; i <= 10; ++i) 
    h.SetBinContent(i, 1.);

  // histogram integral: 10. (slightly off from nbkg = 11. so that chi2 is not 0.)

  RooDataHist dh("dh", "dh", x, &h);

  for (string range : {"", "full", "lo", "hi", "lo,hi"}) {

    auto chi2 = unique_ptr<RooAbsReal> (
      range == ""
      ? pdf.createChi2 (
         dh,
         Extended(true),
         DataError(RooAbsData::Poisson)
       )
      : pdf.createChi2 (
         dh,
         Extended(true),
         DataError(RooAbsData::Poisson),
         Range(range.c_str())
       )
    );

    cout << "chi2(" << range << ")  = " << chi2->getVal() << endl;

  }

}
