void test() {

  for (string f_name : vector<string>{"../tomas/FitResult_anaFit_tenPar_bkgOnly.root", "/eos/home-t/tofitsch/tlafits/run_135_1000_tenPar/FitResult_anaFit_tenPar_bkgOnly.root"}) {

    TFile *f = TFile::Open(f_name.c_str());

    if (!f || f->IsZombie()) {
      std::cerr << "Could not open file\n";
      return;
    }

    RooFitResult *fr = nullptr;
    f->GetObject("fitResult", fr);  // <-- replace with actual object name

    if (!fr) {
      std::cerr << "Could not find RooFitResult\n";
      return;
    }

    // Initial parameters are stored here
    const RooArgList &pars = fr->floatParsInit();

    std::cout << "Number of parameters: "
              << pars.getSize() << std::endl;

    // Print up to 10 of them
    for (int i = 0; i < std::min(10, pars.getSize()); ++i) {
      const RooRealVar *v =
        dynamic_cast<const RooRealVar*>(&pars[i]);
      if (!v) continue;

      std::cout
        << i << ": "
        << v->GetName()
        << " = " << v->getVal()
        << "  [" << v->getMin()
        << ", " << v->getMax()
        << "]"
        << std::endl;
    }

    f->Close();

  }
}
