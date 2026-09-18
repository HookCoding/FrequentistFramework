#!/usr/bin/env python
import ROOT
import sys, re, os, math, argparse
from ROOT import *


def _read_fit_result(wsfile):
    f_in = ROOT.TFile(wsfile, "READ")
    r = f_in.Get("fitResult")

    # r.Print()

    mat_cov = r.covarianceMatrix()
    mat_cor = r.correlationMatrix()

    argset = r.floatParsFinal()

    # Everything is converted to plain Python values before the file closes: argset, mat_cov and
    # mat_cor are all owned by the file, so returning them would hand back objects that die here.
    parameters = [(arg.namePtr().GetName(), arg.getVal(), arg.getError()) for arg in argset]

    n = len(argset)
    covariance = [[mat_cov[i][j] for j in range(n)] for i in range(n)]
    correlation = [[mat_cor[i][j] for j in range(n)] for i in range(n)]

    f_in.Close()

    return parameters, covariance, correlation

def _build_parameter_histogram(parameters):
    h1_params = TH1D("postfit_params", "postfit parameters", len(parameters), 0, len(parameters))
    h1_params.SetDirectory(0)

    for i, (name, value, error) in enumerate(parameters):
        h1_params.GetXaxis().SetBinLabel(i+1, name)
        h1_params.SetBinContent(i+1, value)
        h1_params.SetBinError(i+1, error)

    return h1_params

def _matrix_to_histogram(matrix, name, title, labels):
    n = len(labels)

    h2 = TH2D(name, title, n, 0, n, n, 0, n)
    h2.SetDirectory(0)

    for i, label in enumerate(labels):
        h2.GetXaxis().SetBinLabel(i+1, label)
        h2.GetYaxis().SetBinLabel(i+1, label)

    for i in range(n):
        for j in range(n):
            ibin = h2.GetBin(i+1, j+1)
            h2.SetBinContent(ibin, matrix[i][j])

    return h2

def _find_signal_yield(parameters):
    nsig = None
    nsigErr = None

    # Substring match, and the loop runs on: with more than one matching parameter the last one
    # wins. Preserved as-is. See KNOWN_ISSUES.md issue 53.
    for name, value, error in parameters:
        if "nsig" in name:
            nsig = value
            nsigErr = error

    return nsig, nsigErr

class FitParameterExtractor:

    def __init__(self, wsfile):
        self.wsfile = wsfile
        self.h1_params = None
        self.h2_cov = None
        self.h2_cor = None
        self.nsig = None
        self.nsigErr = None

    def Extract(self):
        parameters, covariance, correlation = _read_fit_result(self.wsfile)
        labels = [name for name, _, _ in parameters]

        self.h1_params = _build_parameter_histogram(parameters)
        self.h2_cov = _matrix_to_histogram(covariance, "h2_cov", "covariance matrix", labels)
        self.h2_cor = _matrix_to_histogram(correlation, "h2_cor", "correlation matrix", labels)

        self.nsig, self.nsigErr = _find_signal_yield(parameters)


    def GetH1Params(self):
        if not self.h1_params:
            self.Extract()
        return self.h1_params

    def GetH2Cov(self):
        if not self.h2_cov:
            self.Extract()
        return self.h2_cov

    def GetH2Cor(self):
        if not self.h2_cor:
            self.Extract()
        return self.h2_cor

    def GetNsig(self):
        if not self.nsig:
            self.Extract()
        return self.nsig

    def GetNsigErr(self):
        if not self.nsigErr:
            self.Extract()
        return self.nsigErr

    def WriteRoot(self, outfile):
        if not self.h1_params:
            self.Extract()

        f_out = ROOT.TFile(outfile, "RECREATE")

        self.h1_params.Write()
        self.h2_cov.Write()
        self.h2_cor.Write()

        f_out.Close()

def main(args):
    parser = argparse.ArgumentParser(description='%prog [options]')
    parser.add_argument('--wsfile', dest='wsfile', type=str, default='../run/FitResult.root', help='Input workspace file name')
    parser.add_argument('--outfile', dest='outfile', type=str, default='../run/ParsedFitResult.root', help='Output file name')
    
    args = parser.parse_args(args)
    
    fpe = FitParameterExtractor(args.wsfile)
    fpe.WriteRoot(args.outfile)

if __name__ == "__main__":  
   sys.exit(main(sys.argv[1:]))   
