#!/bin/env python

from __future__ import print_function

import argparse
import array
import bisect
import sys
from distutils.util import strtobool

import ROOT


class PreFitter:
    def __init__(
        self,
        datafile,
        datahist,
        xMin,
        xMax,
        nRetries1=100000,
        nRetries2=10,
        nPars=5,
        fitLog=True,
        parRangeLow=[1, -30, -30, -10, -1, -1, -0.1],
        parRangeHigh=[1, 30, 30, 10, 1, 1, 0.1],
        seed=42,
    ):

        self.datafile = datafile
        self.datahist = datahist
        self.xMin = xMin
        self.xMax = xMax
        self.nRetries1 = nRetries1
        self.nRetries2 = nRetries2
        self.nPars = nPars
        self.fitLog = fitLog
        self.seed = seed
        self.parRangeLow = parRangeLow
        self.parRangeHigh = parRangeHigh

        ROOT.Math.MinimizerOptions.SetDefaultMaxFunctionCalls(50000)
        self.rnd = ROOT.TRandom3(self.seed)
        ROOT.gROOT.ProcessLine("gErrorIgnoreLevel = 6001;")

    def RandomizeParameters(self, function):
        for i in range(function.GetNpar()):
            function.SetParameter(i, self.rnd.Uniform(self.parRangeLow[i], self.parRangeHigh[i]))

    def _build_candidate_functions(self):
        """Build the 10 linear-mode and 10 log-mode candidate TF1s
        (NParFunction[1..10], LogNParFunction[1..10]). Moved out of Fit()
        as a named block - the formulas and hardcoded ranges are
        unchanged."""
        NParFunction = {}
        LogNParFunction = {}

        NParFunction[1] = ROOT.TF1("1ParFunction", "[0]", self.xMin, self.xMax)
        NParFunction[2] = ROOT.TF1(
            "2ParFunction", "[0]*TMath::Power(1-x/13000.,[1])", self.xMin, self.xMax
        )
        NParFunction[3] = ROOT.TF1(
            "3ParFunction",
            "[0]*TMath::Power(1-x/13000.,[1])*TMath::Power(x/13000., -1*[2])",
            self.xMin,
            self.xMax,
        )
        NParFunction[4] = ROOT.TF1(
            "4ParFunction",
            "[0]*TMath::Power(1-x/13000.,[1])*TMath::Power(x/13000., -1*([2] + [3]*TMath::Log(x/13000.)))",  # noqa: E501
            self.xMin,
            self.xMax,
        )
        NParFunction[5] = ROOT.TF1(
            "5ParFunction",
            "[0]*TMath::Power(1-x/13000.,[1])*TMath::Power(x/13000., -1*([2] + [3]*TMath::Log(x/13000.) + [4]*TMath::Power(TMath::Log(x/13000.),2.)))",  # noqa: E501
            self.xMin,
            self.xMax,
        )
        NParFunction[6] = ROOT.TF1(
            "6ParFunction",
            "[0]*TMath::Power(1-x/13000.,[1])*TMath::Power(x/13000., -1*([2] + [3]*TMath::Log(x/13000.) + [4]*TMath::Power(TMath::Log(x/13000.),2.) + [5]*TMath::Power(TMath::Log(x/13000.),3.)))",  # noqa: E501
            self.xMin,
            self.xMax,
        )
        NParFunction[7] = ROOT.TF1(
            "7ParFunction",
            "[0]*TMath::Power(1-x/13000.,[1])*TMath::Power(x/13000., -1*([2] + [3]*TMath::Log(x/13000.) + [4]*TMath::Power(TMath::Log(x/13000.),2.) + [5]*TMath::Power(TMath::Log(x/13000.),3.) + [6]*TMath::Power(TMath::Log(x/13000.),4.)))",  # noqa: E501
            self.xMin,
            self.xMax,
        )
        NParFunction[8] = ROOT.TF1(
            "8ParFunction",
            "[0]*TMath::Power(1-x/13000.,[1])*TMath::Power(x/13000., -1*([2] + [3]*TMath::Log(x/13000.) + [4]*TMath::Power(TMath::Log(x/13000.),2.) + [5]*TMath::Power(TMath::Log(x/13000.),3.) + [6]*TMath::Power(TMath::Log(x/13000.),4.)  + [7]*TMath::Power(TMath::Log(x/13000.),5.)  ))",  # noqa: E501
            self.xMin,
            self.xMax,
        )
        NParFunction[9] = ROOT.TF1(
            "9ParFunction",
            "[0]*TMath::Power(1-x/13000.,[1])*TMath::Power(x/13000., -1*([2] + [3]*TMath::Log(x/13000.) + [4]*TMath::Power(TMath::Log(x/13000.),2.) + [5]*TMath::Power(TMath::Log(x/13000.),3.) + [6]*TMath::Power(TMath::Log(x/13000.),4.)  + [7]*TMath::Power(TMath::Log(x/13000.),5.) + [8]*TMath::Power(TMath::Log(x/13000.),6.)  ))",  # noqa: E501
            self.xMin,
            self.xMax,
        )
        NParFunction[10] = ROOT.TF1(
            "10ParFunction",
            "[0]*TMath::Power(1-x/13000.,[1])*TMath::Power(x/13000., -1*([2] + [3]*TMath::Log(x/13000.) + [4]*TMath::Power(TMath::Log(x/13000.),2.) + [5]*TMath::Power(TMath::Log(x/13000.),3.) + [6]*TMath::Power(TMath::Log(x/13000.),4.)  + [7]*TMath::Power(TMath::Log(x/13000.),5.) + [8]*TMath::Power(TMath::Log(x/13000.),6.) + [9]*TMath::Power(TMath::Log(x/13000.),7.)  ))",  # noqa: E501
            self.xMin,
            self.xMax,
        )

        LogNParFunction[1] = ROOT.TF1("Log1ParFunction", "TMath::Log([0])", self.xMin, self.xMax)
        LogNParFunction[2] = ROOT.TF1(
            "Log2ParFunction", "TMath::Log([0])+[1]*TMath::Log(1-x/13000.)", self.xMin, self.xMax
        )
        LogNParFunction[3] = ROOT.TF1(
            "Log3ParFunction",
            "TMath::Log([0])+[1]*TMath::Log(1-x/13000.) - [2]*TMath::Log(x/13000.)",
            self.xMin,
            self.xMax,
        )
        LogNParFunction[4] = ROOT.TF1(
            "Log4ParFunction",
            "TMath::Log([0])+[1]*TMath::Log(1-x/13000.) - [2]*TMath::Log(x/13000.) - [3]*TMath::Power(TMath::Log(x/13000.),2.)",  # noqa: E501
            self.xMin,
            self.xMax,
        )
        LogNParFunction[5] = ROOT.TF1(
            "Log5ParFunction",
            "TMath::Log([0])+[1]*TMath::Log(1-x/13000.) - [2]*TMath::Log(x/13000.) - [3]*TMath::Power(TMath::Log(x/13000.),2.) - [4]*TMath::Power(TMath::Log(x/13000.),3.)",  # noqa: E501
            self.xMin,
            self.xMax,
        )
        LogNParFunction[6] = ROOT.TF1(
            "Log6ParFunction",
            "TMath::Log([0])+[1]*TMath::Log(1-x/13000.) - [2]*TMath::Log(x/13000.) - [3]*TMath::Power(TMath::Log(x/13000.),2.) - [4]*TMath::Power(TMath::Log(x/13000.),3.) - [5]*TMath::Power(TMath::Log(x/13000.),4.)",  # noqa: E501
            self.xMin,
            self.xMax,
        )
        LogNParFunction[7] = ROOT.TF1(
            "Log7ParFunction",
            "TMath::Log([0])+[1]*TMath::Log(1-x/13000.) - [2]*TMath::Log(x/13000.) - [3]*TMath::Power(TMath::Log(x/13000.),2.) - [4]*TMath::Power(TMath::Log(x/13000.),3.) - [5]*TMath::Power(TMath::Log(x/13000.),4.) - [6]*TMath::Power(TMath::Log(x/13000.),5.)",  # noqa: E501
            self.xMin,
            self.xMax,
        )
        LogNParFunction[8] = ROOT.TF1(
            "Log8ParFunction",
            "TMath::Log([0])+[1]*TMath::Log(1-x/13000.) - [2]*TMath::Log(x/13000.) - [3]*TMath::Power(TMath::Log(x/13000.),2.) - [4]*TMath::Power(TMath::Log(x/13000.),3.) - [5]*TMath::Power(TMath::Log(x/13000.),4.) - [6]*TMath::Power(TMath::Log(x/13000.),5.)- [7]*TMath::Power(TMath::Log(x/13000.),6.) ",  # noqa: E501
            self.xMin,
            self.xMax,
        )
        LogNParFunction[9] = ROOT.TF1(
            "Log9ParFunction",
            "TMath::Log([0])+[1]*TMath::Log(1-x/13000.) - [2]*TMath::Log(x/13000.) - [3]*TMath::Power(TMath::Log(x/13000.),2.) - [4]*TMath::Power(TMath::Log(x/13000.),3.) - [5]*TMath::Power(TMath::Log(x/13000.),4.) - [6]*TMath::Power(TMath::Log(x/13000.),5.)- [7]*TMath::Power(TMath::Log(x/13000.),6.)- [8]*TMath::Power(TMath::Log(x/13000.),7.) ",  # noqa: E501
            self.xMin,
            self.xMax,
        )
        LogNParFunction[10] = ROOT.TF1(
            "Log10ParFunction",
            "TMath::Log([0])+[1]*TMath::Log(1-x/13000.) - [2]*TMath::Log(x/13000.) - [3]*TMath::Power(TMath::Log(x/13000.),2.) - [4]*TMath::Power(TMath::Log(x/13000.),3.) - [5]*TMath::Power(TMath::Log(x/13000.),4.) - [6]*TMath::Power(TMath::Log(x/13000.),5.)- [7]*TMath::Power(TMath::Log(x/13000.),6.)- [8]*TMath::Power(TMath::Log(x/13000.),7.) - [9]*TMath::Power(TMath::Log(x/13000.),8.) ",  # noqa: E501
            self.xMin,
            self.xMax,
        )

        return NParFunction, LogNParFunction

    def _select_best_parameter_sets(self, fitFunction, integral, score_fn, nRetries1, nRetries2):
        """Randomize fitFunction's parameters nRetries1 times, score each
        trial with score_fn(fitFunction), and keep the ranked best
        nRetries2 parameter sets by ascending chi2. Isolates the
        array/bisect bookkeeping that used to live directly inside
        Fit()'s own sampling loop; no ROOT calls of its own beyond
        scoring the candidate function it's handed (score_fn is the
        caller's h.Chisquare(...) closure, so this method never touches
        the data histogram directly)."""
        best_chi2Pars = [(float("inf"), [])]

        print("==================")
        print("Rolling %d samples:" % nRetries1)
        w = ROOT.TStopwatch()
        w.Start()

        for i in range(nRetries1):
            if i % 5000 == 0:
                print(i)

            self.RandomizeParameters(fitFunction)

            # don't need default 1e-12 precision here. it also throws errors
            p0 = ROOT.TMath.Exp(integral / fitFunction.Integral(self.xMin, self.xMax, 1e-10))
            fitFunction.SetParameter(0, p0)
            fitFunction.SetParameter(1, 80)
            fitFunction.SetParameter(2, 10)
            fitFunction.SetParameter(3, 10)
            fitFunction.SetParameter(4, 2)
            fitFunction.SetParameter(5, 0)
            fitFunction.SetParameter(6, 0)
            fitFunction.SetParameter(7, 0)
            fitFunction.SetParameter(8, 0)
            fitFunction.SetParameter(9, 0)

            if self.fitLog:
                fitFunction.SetParLimits(0, 0, p0 + ROOT.TMath.Log(10))
            else:
                fitFunction.SetParLimits(0, 0, 10 * p0)

            chi2 = score_fn(fitFunction)
            if chi2 < best_chi2Pars[-1][0]:
                pars = array.array("d", [0] * fitFunction.GetNpar())
                fitFunction.GetParameters(pars)
                bisect.insort(best_chi2Pars, (chi2, pars))
                if len(best_chi2Pars) > nRetries2:
                    best_chi2Pars.pop()

        print("==================")
        print("Finished sampling")
        w.Stop()
        w.Print()

        return best_chi2Pars

    def Fit(self):
        print("In Prefit. Attempting to read", self.datafile, "hist", self.datahist)
        f = ROOT.TFile(self.datafile, "READ")
        h = f.Get(self.datahist)

        bin_low = h.GetXaxis().FindBin(self.xMin)
        bin_high = h.GetXaxis().FindBin(self.xMax)
        nbkg = h.Integral(bin_low, bin_high)

        if self.fitLog:
            # make h logarithmic:
            for i in range(1, h.GetNbinsX() + 1):
                if h.GetBinContent(i) != 0:
                    h.SetBinError(i, h.GetBinError(i) / h.GetBinContent(i))
                    h.SetBinContent(i, ROOT.TMath.Log(h.GetBinContent(i)))

        integral = h.Integral()
        # h.Scale(1./integral)

        NParFunction, LogNParFunction = self._build_candidate_functions()

        if self.fitLog:
            fitFunction = LogNParFunction[self.nPars]
        else:
            fitFunction = NParFunction[self.nPars]

        for i in range(fitFunction.GetNpar()):
            fitFunction.SetParLimits(i, self.parRangeLow[i], self.parRangeHigh[i])

        best_chi2Pars = self._select_best_parameter_sets(
            fitFunction, integral, lambda fn: h.Chisquare(fn), self.nRetries1, self.nRetries2
        )

        print("==================")
        print("Starting fit of %d best samples" % self.nRetries2)

        bestChi2 = float("inf")
        bestPars = array.array("d", [0] * fitFunction.GetNpar())

        w = ROOT.TStopwatch()
        w.Start()

        for i in range(self.nRetries2):
            fitFunction.SetParameters(best_chi2Pars[i][1])
            print("integral", h.Integral())
            fR = h.Fit(fitFunction, "R0QS", "", self.xMin, self.xMax)

            thisFitChi2 = fR.Chi2()
            if thisFitChi2 < bestChi2:
                bestChi2 = thisFitChi2
                fitFunction.GetParameters(bestPars)

            print("trial %2d: chi2=%.4f" % (i, thisFitChi2))

        print("==================")
        print("Finished fitting")
        w.Stop()
        w.Print()

        print("Best Total:")

        print("chi2 =", bestChi2)
        for k in range(fitFunction.GetNpar()):
            print("p%d = %.8f" % (k + 1, bestPars[k]))

        print("==================")

        f.Close()

        return bestPars, nbkg


def main(args):
    parser = argparse.ArgumentParser(description="%prog [options]")
    parser.add_argument(
        "--datafile", dest="datafile", type=str, required=True, help="data file name"
    )
    parser.add_argument(
        "--datahist", dest="datahist", type=str, default="data", help="data hist name"
    )
    parser.add_argument("--xMin", dest="xMin", type=float, required=True, help="Start of fit range")
    parser.add_argument("--xMax", dest="xMax", type=float, required=True, help="End of fit range")
    parser.add_argument(
        "--nPars", dest="nPars", type=int, default=5, help="Number of fit parameters"
    )
    parser.add_argument(
        "--nRetries1",
        dest="nRetries1",
        type=int,
        default=10000,
        help="Number of trials for initial sampling",
    )
    parser.add_argument(
        "--nRetries2", dest="nRetries2", type=int, default=10, help="Number of tried fits"
    )
    parser.add_argument(
        "--fitLog",
        dest="fitLog",
        type=strtobool,
        default=1,
        help="Perform the fit after a logarithmic transformation",
    )
    parser.add_argument(
        "--parRangeLow",
        dest="parRangeLow",
        nargs="+",
        type=float,
        default=[1, -30, -30, -10, -1, -1, -0.1],
        help="Lower limits of allow parameters ranges",
    )
    parser.add_argument(
        "--parRangeHigh",
        dest="parRangeHigh",
        nargs="+",
        type=float,
        default=[1, 30, 30, 10, 1, 1, 0.1],
        help="Upper limits of allow parameters ranges",
    )
    parser.add_argument(
        "--seed", dest="seed", type=int, default=42, help="Seed for random number generator"
    )

    args = parser.parse_args(args)

    pf = PreFitter(
        datafile=args.datafile,
        datahist=args.datahist,
        xMin=args.xMin,
        xMax=args.xMax,
        nPars=args.nPars,
        nRetries1=args.nRetries1,
        nRetries2=args.nRetries2,
        fitLog=args.fitLog,
        parRangeLow=args.parRangeLow,
        parRangeHigh=args.parRangeHigh,
        seed=args.seed,
    )

    print(pf.Fit())


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
