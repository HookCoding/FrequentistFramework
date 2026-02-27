void test2() {

  string const 
    f_name{"/eos/home-t/tofitsch/tlafits/run_135_1000_sevenPar/dijetisrTLA_combWS_sevenPar_masked.root"};

  TFile *f = TFile::Open(f_name.c_str());

  if (!f || f->IsZombie()) {
    std::cerr << "Could not open file\n";
    return;
  }

  RooWorkspace *ws = nullptr;
  f->GetObject("combWS", ws);
  if (!ws) {
      cerr << "Workspace not found!\n";
      return;
  }

//  ws->Print();

  RooRealVar* x = ws->var("obs_x_channel");

//  cout<<"SBLo"<< endl;
//  x->getBinning("SBLo").Print();
//  cout<<"SBHi"<< endl;
//  x->getBinning("SBHi").Print();
  
//  x->setRange("x", 150, 160);

  for (std::string const range_name : {"SBLo", "SBHi", "SBLo_Run3TLA", "SBHi_Run3TLA"})
    cout << range_name << ": "<< x->getRange(range_name.c_str()).first << " - " << x->getRange(range_name.c_str()).second << endl;

  f->Close();

  
}
