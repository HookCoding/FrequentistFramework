void test() {

  //for (string f_name : vector<string>{"../tomas/FitResult_anaFit_tenPar_bkgOnly.root", "/eos/home-t/tofitsch/tlafits/run_135_1000_tenPar/FitResult_anaFit_tenPar_bkgOnly.root"}) {
  for (string f_name : vector<string>{"/eos/home-t/tofitsch/tlafits/run_135_1000_tenPar/FitResult_anaFit_tenPar_bkgOnly.root", "/eos/home-t/tofitsch/tlafits/run_135_1000_tenPar/FitResult_anaFit_tenPar_bkgOnly_masked.root"}) {

    cout << f_name << endl;

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
    //const RooArgList &pars = fr->floatParsFinal();

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

    RooWorkspace *ws = nullptr;
    f->GetObject("combWS", ws);
    if (!ws) {
        cerr << "Workspace not found!\n";
        return;
    }

    ws->Print();
    
    // Get the PDF
    RooAbsPdf *pdf = ws->pdf("CombinedPdf");
    if (!pdf) {
        cerr << "CombinedPdf not found!\n";
        return;
    }
    
    // Get the dataset (returns RooAbsData*)
    RooAbsData *absData = ws->data("combData");
    if (!absData) {
        cerr << "Dataset combData not found!\n";
        return;
    }
    
    // Cast to RooDataSet (or check for RooDataHist)
    RooDataSet *data = dynamic_cast<RooDataSet*>(absData);
    if (!data) {
        cerr << "Dataset is not RooDataSet (maybe binned?)\n";
        return;
    }
    
    // Compute unbinned NLL
    RooNLLVar nll("nll", "negative log-likelihood", *pdf, *data);
    cout << "-2 ln L = " << 2*nll.getVal() << endl;

    // Compute chi2
    if (pdf && data) {

      RooDataHist *dataHist = data->binnedClone();
      RooChi2Var chi2_obj("chi2", "chi2", *pdf, *dataHist);

      float const
        chi2 = chi2_obj.getVal(),
        ndof = dataHist->numEntries() - pars.getSize();

      cout << "Chi2 / ndf = " <<  chi2 << " / " << ndof << " = " << chi2 / ndof << endl;
      delete dataHist;
    }

    f->Close();

  }
}
