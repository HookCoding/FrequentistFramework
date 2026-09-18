#!/bin/env python

from __future__ import print_function
from distutils.util import strtobool
import math, array, bisect
import sys, argparse
import ROOT

def _configure_root():
    ROOT.Math.MinimizerOptions.SetDefaultMaxFunctionCalls(50000)
    ROOT.gROOT.ProcessLine( "gErrorIgnoreLevel = 6001;")

def _load_histogram(datafile, datahist):
    print("In Prefit. Attempting to read", datafile, "hist", datahist)
    f = ROOT.TFile(datafile, "READ")
    h = f.Get(datahist)
    return f, h

def _prepare_histogram(histogram, xMin, xMax, fitLog):
    bin_low = histogram.GetXaxis().FindBin(xMin)
    bin_high = histogram.GetXaxis().FindBin(xMax)
    nbkg = histogram.Integral(bin_low, bin_high)

    if fitLog:
        # make h logarithmic:
        for i in range(1, histogram.GetNbinsX()+1):
            if histogram.GetBinContent(i) != 0:
                histogram.SetBinError(i, histogram.GetBinError(i)/histogram.GetBinContent(i))
                histogram.SetBinContent(i, ROOT.TMath.Log(histogram.GetBinContent(i)))

    integral = histogram.Integral()
    # h.Scale(1./integral)

    return nbkg, integral

def _build_candidate_functions(xMin, xMax):
    NParFunction = {}
    LogNParFunction = {}

    NParFunction[1] = ROOT.TF1("1ParFunction", "[0]", xMin, xMax)
    NParFunction[2] = ROOT.TF1("2ParFunction", "[0]*TMath::Power(1-x/13000.,[1])", xMin, xMax)
    NParFunction[3] = ROOT.TF1("3ParFunction", "[0]*TMath::Power(1-x/13000.,[1])*TMath::Power(x/13000., -1*[2])", xMin, xMax)
    NParFunction[4] = ROOT.TF1("4ParFunction", "[0]*TMath::Power(1-x/13000.,[1])*TMath::Power(x/13000., -1*([2] + [3]*TMath::Log(x/13000.)))", xMin, xMax)
    NParFunction[5] = ROOT.TF1("5ParFunction", "[0]*TMath::Power(1-x/13000.,[1])*TMath::Power(x/13000., -1*([2] + [3]*TMath::Log(x/13000.) + [4]*TMath::Power(TMath::Log(x/13000.),2.)))", xMin, xMax)
    NParFunction[6] = ROOT.TF1("6ParFunction", "[0]*TMath::Power(1-x/13000.,[1])*TMath::Power(x/13000., -1*([2] + [3]*TMath::Log(x/13000.) + [4]*TMath::Power(TMath::Log(x/13000.),2.) + [5]*TMath::Power(TMath::Log(x/13000.),3.)))", xMin, xMax)
    NParFunction[7] = ROOT.TF1("7ParFunction", "[0]*TMath::Power(1-x/13000.,[1])*TMath::Power(x/13000., -1*([2] + [3]*TMath::Log(x/13000.) + [4]*TMath::Power(TMath::Log(x/13000.),2.) + [5]*TMath::Power(TMath::Log(x/13000.),3.) + [6]*TMath::Power(TMath::Log(x/13000.),4.)))", xMin, xMax)
    NParFunction[8] = ROOT.TF1("8ParFunction", "[0]*TMath::Power(1-x/13000.,[1])*TMath::Power(x/13000., -1*([2] + [3]*TMath::Log(x/13000.) + [4]*TMath::Power(TMath::Log(x/13000.),2.) + [5]*TMath::Power(TMath::Log(x/13000.),3.) + [6]*TMath::Power(TMath::Log(x/13000.),4.)  + [7]*TMath::Power(TMath::Log(x/13000.),5.)  ))", xMin, xMax)
    NParFunction[9] = ROOT.TF1("9ParFunction", "[0]*TMath::Power(1-x/13000.,[1])*TMath::Power(x/13000., -1*([2] + [3]*TMath::Log(x/13000.) + [4]*TMath::Power(TMath::Log(x/13000.),2.) + [5]*TMath::Power(TMath::Log(x/13000.),3.) + [6]*TMath::Power(TMath::Log(x/13000.),4.)  + [7]*TMath::Power(TMath::Log(x/13000.),5.) + [8]*TMath::Power(TMath::Log(x/13000.),6.)  ))", xMin, xMax)
    NParFunction[10] = ROOT.TF1("10ParFunction", "[0]*TMath::Power(1-x/13000.,[1])*TMath::Power(x/13000., -1*([2] + [3]*TMath::Log(x/13000.) + [4]*TMath::Power(TMath::Log(x/13000.),2.) + [5]*TMath::Power(TMath::Log(x/13000.),3.) + [6]*TMath::Power(TMath::Log(x/13000.),4.)  + [7]*TMath::Power(TMath::Log(x/13000.),5.) + [8]*TMath::Power(TMath::Log(x/13000.),6.) + [9]*TMath::Power(TMath::Log(x/13000.),7.)  ))", xMin, xMax)

    LogNParFunction[1] = ROOT.TF1("Log1ParFunction", "TMath::Log([0])", xMin, xMax)
    LogNParFunction[2] = ROOT.TF1("Log2ParFunction", "TMath::Log([0])+[1]*TMath::Log(1-x/13000.)", xMin, xMax)
    LogNParFunction[3] = ROOT.TF1("Log3ParFunction", "TMath::Log([0])+[1]*TMath::Log(1-x/13000.) - [2]*TMath::Log(x/13000.)", xMin, xMax)
    LogNParFunction[4] = ROOT.TF1("Log4ParFunction", "TMath::Log([0])+[1]*TMath::Log(1-x/13000.) - [2]*TMath::Log(x/13000.) - [3]*TMath::Power(TMath::Log(x/13000.),2.)", xMin, xMax)
    LogNParFunction[5] = ROOT.TF1("Log5ParFunction", "TMath::Log([0])+[1]*TMath::Log(1-x/13000.) - [2]*TMath::Log(x/13000.) - [3]*TMath::Power(TMath::Log(x/13000.),2.) - [4]*TMath::Power(TMath::Log(x/13000.),3.)", xMin, xMax)
    LogNParFunction[6] = ROOT.TF1("Log6ParFunction", "TMath::Log([0])+[1]*TMath::Log(1-x/13000.) - [2]*TMath::Log(x/13000.) - [3]*TMath::Power(TMath::Log(x/13000.),2.) - [4]*TMath::Power(TMath::Log(x/13000.),3.) - [5]*TMath::Power(TMath::Log(x/13000.),4.)", xMin, xMax)
    LogNParFunction[7] = ROOT.TF1("Log7ParFunction", "TMath::Log([0])+[1]*TMath::Log(1-x/13000.) - [2]*TMath::Log(x/13000.) - [3]*TMath::Power(TMath::Log(x/13000.),2.) - [4]*TMath::Power(TMath::Log(x/13000.),3.) - [5]*TMath::Power(TMath::Log(x/13000.),4.) - [6]*TMath::Power(TMath::Log(x/13000.),5.)", xMin, xMax)
    LogNParFunction[8] = ROOT.TF1("Log8ParFunction", "TMath::Log([0])+[1]*TMath::Log(1-x/13000.) - [2]*TMath::Log(x/13000.) - [3]*TMath::Power(TMath::Log(x/13000.),2.) - [4]*TMath::Power(TMath::Log(x/13000.),3.) - [5]*TMath::Power(TMath::Log(x/13000.),4.) - [6]*TMath::Power(TMath::Log(x/13000.),5.)- [7]*TMath::Power(TMath::Log(x/13000.),6.) ", xMin, xMax)
    LogNParFunction[9] = ROOT.TF1("Log9ParFunction", "TMath::Log([0])+[1]*TMath::Log(1-x/13000.) - [2]*TMath::Log(x/13000.) - [3]*TMath::Power(TMath::Log(x/13000.),2.) - [4]*TMath::Power(TMath::Log(x/13000.),3.) - [5]*TMath::Power(TMath::Log(x/13000.),4.) - [6]*TMath::Power(TMath::Log(x/13000.),5.)- [7]*TMath::Power(TMath::Log(x/13000.),6.)- [8]*TMath::Power(TMath::Log(x/13000.),7.) ", xMin, xMax)
    LogNParFunction[10] = ROOT.TF1("Log10ParFunction", "TMath::Log([0])+[1]*TMath::Log(1-x/13000.) - [2]*TMath::Log(x/13000.) - [3]*TMath::Power(TMath::Log(x/13000.),2.) - [4]*TMath::Power(TMath::Log(x/13000.),3.) - [5]*TMath::Power(TMath::Log(x/13000.),4.) - [6]*TMath::Power(TMath::Log(x/13000.),5.)- [7]*TMath::Power(TMath::Log(x/13000.),6.)- [8]*TMath::Power(TMath::Log(x/13000.),7.) - [9]*TMath::Power(TMath::Log(x/13000.),8.) ", xMin, xMax)

    return NParFunction, LogNParFunction

def _select_fit_function(normal_functions, log_functions, fitLog, nPars, parRangeLow, parRangeHigh):
    if fitLog:
        fitFunction = log_functions[nPars]
    else:
        fitFunction = normal_functions[nPars]

    for i in range(fitFunction.GetNpar()):
        fitFunction.SetParLimits(i, parRangeLow[i], parRangeHigh[i])

    return fitFunction

def _fit_best_candidates(histogram, fit_function, candidates, nRetries2, xMin, xMax):
    w = ROOT.TStopwatch()
    w.Start()

    print("Starting fit of %d best samples" % nRetries2)

    bestChi2 = float("inf")
    bestPars = array.array('d', [0]*fit_function.GetNpar())

    for  i in range(nRetries2):
        fit_function.SetParameters(candidates[i][1])
        print("integral",histogram.Integral())
        fR = histogram.Fit(fit_function, "R0QS", "", xMin, xMax)

        thisFitChi2 = fR.Chi2()
        if (thisFitChi2 < bestChi2):
            bestChi2 = thisFitChi2
            fit_function.GetParameters(bestPars)

        print("trial %2d: chi2=%.4f" % (i, thisFitChi2))

    print("==================")
    print("Finished fitting")
    w.Stop()
    w.Print()

    return bestChi2, bestPars

def _report_fit_result(best_chi2, best_parameters, npar):
    print("Best Total:")

    print("chi2 =", best_chi2)
    for k in range(npar):
        print("p%d = %.8f" % (k+1, best_parameters[k]))

    print("==================")

class PreFitter:
    def __init__(self,
                 datafile,
                 datahist,
                 xMin,
                 xMax,
                 nRetries1 = 100000,
                 nRetries2 = 10,
                 nPars=5,
                 fitLog=True,
                 parRangeLow = [1, -30, -30, -10, -1, -1, -0.1],
                 parRangeHigh = [1, 30, 30, 10, 1, 1, 0.1],
                 seed=42):

        self.datafile = datafile
        self.datahist = datahist
        self.xMin = xMin
        self.xMax = xMax
        self.nRetries1 = nRetries1
        self.nRetries2 = nRetries2
        self.nPars = nPars
        self.fitLog = fitLog
        self.seed = seed
        self.parRangeLow  = parRangeLow
        self.parRangeHigh = parRangeHigh

        self.rnd = ROOT.TRandom3(self.seed)

    def RandomizeParameters(self, function):
        for i in range(function.GetNpar()):
            function.SetParameter(i, self.rnd.Uniform(self.parRangeLow[i], self.parRangeHigh[i]))

    def _find_best_parameter_sets(self, fit_function, integral, score_function, nRetries1, nRetries2,
                                   fitLog, xMin, xMax):
        best_chi2Pars = [(float("inf"),[])]

        print("==================")
        print("Rolling %d samples:" % nRetries1)
        w = ROOT.TStopwatch()
        w.Start()

        for i in range(nRetries1):
            if (i%5000 == 0):
                print(i)

            self.RandomizeParameters(fit_function)

            # don't need default 1e-12 precision here. it also throws errors
            p0 = ROOT.TMath.Exp(integral/fit_function.Integral(xMin, xMax, 1e-10))
            fit_function.SetParameter(0, p0)
            fit_function.SetParameter(1, 80)
            fit_function.SetParameter(2, 10)
            fit_function.SetParameter(3, 10)
            fit_function.SetParameter(4, 2)
            fit_function.SetParameter(5, 0)
            fit_function.SetParameter(6, 0)
            fit_function.SetParameter(7, 0)
            fit_function.SetParameter(8, 0)
            fit_function.SetParameter(9, 0)

            if fitLog:
                fit_function.SetParLimits(0, 0, p0+ROOT.TMath.Log(10))
            else:
                fit_function.SetParLimits(0, 0, 10*p0)

            chi2 = score_function(fit_function)
            if (chi2 < best_chi2Pars[-1][0]):
                pars = array.array('d', [0]*fit_function.GetNpar())
                fit_function.GetParameters(pars)
                bisect.insort(best_chi2Pars, (chi2, pars))
                if len(best_chi2Pars) > nRetries2:
                    best_chi2Pars.pop()

        print("==================")
        print("Finished sampling")
        w.Stop()
        w.Print()

        return best_chi2Pars

    def Fit(self):
        _configure_root()

        f, h = _load_histogram(self.datafile, self.datahist)

        nbkg, integral = _prepare_histogram(h, self.xMin, self.xMax, self.fitLog)

        NParFunction, LogNParFunction = _build_candidate_functions(self.xMin, self.xMax)

        fitFunction = _select_fit_function(NParFunction, LogNParFunction, self.fitLog, self.nPars,
                                            self.parRangeLow, self.parRangeHigh)

        best_chi2Pars = self._find_best_parameter_sets(fitFunction, integral, h.Chisquare,
                                                         self.nRetries1, self.nRetries2, self.fitLog,
                                                         self.xMin, self.xMax)

        bestChi2, bestPars = _fit_best_candidates(h, fitFunction, best_chi2Pars, self.nRetries2,
                                                    self.xMin, self.xMax)

        _report_fit_result(bestChi2, bestPars, fitFunction.GetNpar())

        f.Close()

        return bestPars,nbkg

def main(args):
    parser = argparse.ArgumentParser(description='%prog [options]')
    parser.add_argument('--datafile', dest='datafile', type=str, required=True, help='data file name')
    parser.add_argument('--datahist', dest='datahist', type=str, default="data", help='data hist name')
    parser.add_argument('--xMin', dest='xMin', type=float, required=True, help='Start of fit range')
    parser.add_argument('--xMax', dest='xMax', type=float, required=True, help='End of fit range')
    parser.add_argument('--nPars', dest='nPars', type=int, default=5, help='Number of fit parameters')
    parser.add_argument('--nRetries1', dest='nRetries1', type=int, default=10000, help='Number of trials for initial sampling')
    parser.add_argument('--nRetries2', dest='nRetries2', type=int, default=10, help='Number of tried fits')
    parser.add_argument('--fitLog', dest='fitLog', type=strtobool, default=1, help='Perform the fit after a logarithmic transformation')
    parser.add_argument('--parRangeLow', dest='parRangeLow', nargs='+', type=float, default=[1, -30, -30, -10, -1, -1, -0.1], help='Lower limits of allow parameters ranges')
    parser.add_argument('--parRangeHigh', dest='parRangeHigh', nargs='+', type=float, default=[1, 30, 30, 10, 1, 1, 0.1], help='Upper limits of allow parameters ranges')
    parser.add_argument('--seed', dest='seed', type=int, default=42, help='Seed for random number generator')

    args = parser.parse_args(args)

    pf = PreFitter(
        datafile = args.datafile,
        datahist = args.datahist,
        xMin = args.xMin,
        xMax = args.xMax,
        nPars = args.nPars,
        nRetries1 = args.nRetries1,
        nRetries2 = args.nRetries2,
        fitLog = args.fitLog,
        parRangeLow = args.parRangeLow,
        parRangeHigh = args.parRangeHigh,
        seed = args.seed,
    )

    print(pf.Fit())

if __name__ == "__main__":
   sys.exit(main(sys.argv[1:]))
