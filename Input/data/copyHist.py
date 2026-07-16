import ROOT

tfile = ROOT.TFile.Open("hist-TLA_mjj.root","READ")
mjj = tfile.Get("beforeCleaning_online/afterSelection/nominal/h_mjj")

new_mjj = ROOT.TH1F("new_mjj","",450,100,1000)

for i in range(0,1000):
    binContent = mjj.GetBinContent(50+i)
    new_mjj.SetBinContent(i+1, binContent)
outfile = ROOT.TFile.Open("mjj_0p5ifb.root","RECREATE")
outfile.cd()
new_mjj.Write()
outfile.Close()
tfile.Close()
