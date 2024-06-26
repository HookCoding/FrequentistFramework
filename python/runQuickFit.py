from ExtractPostfitFromWS import PostfitExtractor
from ExtractFitParameters import FitParameterExtractor
import sys, os, subprocess
import ROOT
_range = ""

masses = list(range(150,250,25))
widths = [5, 10]
datafile = "../run/postfit.root"
datahist = "mjj"
wsfile = "../run/dijetisrTLA_combWS_fourPar.root"
maskmin = -1
maskmax = -1
rangelow = 150

def execute(cmd):  
    print("\n EXECUTE:", cmd)
    sys.stdout.flush() # keeps print and subprocess output in sync
    rtv = subprocess.call(cmd, shell=True)
    return rtv

for sigmean in masses:
    for sigwidth in widths:

        _poi = f"-p nsig_mean{sigmean}_width{sigwidth}"
        fitresultfile = f"../run/FitResult_anaFit_mean{sigmean}_width{sigwidth}.root"
        rtv=execute("quickFit -f %s -d combData %s --checkWS 1 --hesse 1 --savefitresult 1 --saveWS 1 --saveNP 1 --saveErrors 1 --minStrat 2 --nllOffset 0 --optConst 2 --GKIntegrator 1 --minTolerance 1E-10 %s -o %s" % (wsfile, _poi, _range, fitresultfile))

        # postfitfile=fitresultfile.replace("FitResult","PostFit")
        parameterfile=fitresultfile.replace("FitResult","FitParameters")

        f=ROOT.TFile(datafile)
        d=f.Get(datahist)
        datafirstbin=d.FindBin(rangelow)-1
        f.Close()
        
        fpe = FitParameterExtractor(wsfile=fitresultfile)
        print(parameterfile)
        fpe.WriteRoot(parameterfile)