import ROOT
from array import array

bins = [95 ,109, 122, 137, 152, 168, 185, 202, 221, 240, 260, 281, 302, 324, 346, 370, 
394, 419 ,446, 473, 501, 531, 560, 590, 621, 652, 683, 716, 750, 786, 824, 862, 901, 
941  ,982 , 1023, 1066, 1110, 1155, 1201, 1247, 1294, 1342, 1391, 1442, 1493, 1544, 1597, 1651 ,
1706 ,1762, 1820, 1878, 1938, 1998]
bin_edges = array("f", bins)
tfile = ROOT.TFile.Open("mjjBinning.root","RECREATE")

h = ROOT.TH1F("mjjBinning","", len(bins)-1, bin_edges)
# Fill it so it can be viewed easily 
for b in range(h.GetNbinsX()+1):
    h.SetBinContent(b, b)

tfile.cd()
h.Write()
tfile.Close()