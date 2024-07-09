#!/bin/env python

from __future__ import print_function
from distutils.util import strtobool
import math, array, bisect
import sys, argparse
import ROOT
from ROOT import RooFit

class PreFitter:
    def __init__(self, 
                 wsfile,
                 wsname = "combWS", 
                 mcname = "ModelConfig", 
                 dataname = "combData", 
                 nRetries1 = 100000,
                 nRetries2 = 10,
                 seed=42,
                 updatews=False,
                 chi2fit=False,
                 chi2constraints=True,
                 poi=None,
                 rangeName=None):

        self.wsfile = wsfile
        self.wsname = wsname
        self.mcname = mcname
        self.dataname = dataname

        self.nRetries1 = nRetries1
        self.nRetries2 = nRetries2
        self.seed = seed
        self.updatews = updatews
        self.chi2fit = chi2fit
        self.chi2constraints = chi2constraints
        self.poi = poi
        self.rangeName = rangeName

        ROOT.Math.MinimizerOptions.SetDefaultMaxFunctionCalls(50000)
        self.rnd = ROOT.TRandom3(self.seed)
        ROOT.gROOT.ProcessLine( "RooMsgService::instance().setGlobalKillBelow(RooFit::ERROR);" )

    def RandomizeParameters(self, np):
        for p in np:
            if not "nbkg" in p.GetName() and not "nsig" in p.GetName():
                if self.chi2constraints:
                    p.setVal(self.rnd.Gaus(0.5*(p.getMin()+p.getMax()), 0.1*(p.getMax()-p.getMin())))
                else:
                    p.setVal(self.rnd.Uniform(p.getMin(), p.getMax()))
                # p.setVal(self.rnd.Gaus(0., 1.))

    def Fit(self):

        f = ROOT.TFile(self.wsfile, "UPDATE")
        w = f.Get(self.wsname)

        mc = w.obj(self.mcname)
        d = w.obj(self.dataname)
        p = mc.GetPdf()
        o = mc.GetObservables()
        co = mc.GetConditionalObservables()
        go = mc.GetGlobalObservables()
        np = mc.GetNuisanceParameters()

        dh = ROOT.RooDataHist("dh", "dh", o, d)

        nbkg = dh.sum(False)
        print("nbkg=",nbkg)

        w.obj("nbkg").setRange(0.8*nbkg, 1.2*nbkg)
        w.obj("nbkg").setVal(nbkg)

        args = ROOT.RooLinkedList()
        args.Add(ROOT.RooCmdArg(RooFit.Constrain(np)))
        args.Add(ROOT.RooCmdArg(RooFit.GlobalObservables(go)))
        args.Add(ROOT.RooCmdArg(RooFit.ConditionalObservables(co)))
        args.Add(ROOT.RooCmdArg(RooFit.Save(1)))
        args.Add(ROOT.RooCmdArg(RooFit.Hesse(0)))
        args.Add(ROOT.RooCmdArg(RooFit.Hesse(0)))
        args.Add(ROOT.RooCmdArg(RooFit.PrintLevel(-1)))
        # args.Add(ROOT.RooCmdArg(RooFit.BatchMode(1)))
        args.Add(ROOT.RooCmdArg(RooFit.Strategy(2)))

        args_chi2 = ROOT.RooLinkedList()
        args_chi2.Add(ROOT.RooCmdArg(RooFit.Save(1)))
        args_chi2.Add(ROOT.RooCmdArg(RooFit.Hesse(0)))
        args_chi2.Add(ROOT.RooCmdArg(RooFit.Hesse(0)))
        args_chi2.Add(ROOT.RooCmdArg(RooFit.PrintLevel(-1)))
        # args_chi2.Add(ROOT.RooCmdArg(RooFit.BatchMode(1)))
        args_chi2.Add(ROOT.RooCmdArg(RooFit.Strategy(2)))

        best_chi2Pars = [(float("inf"),None)]
        
        print("==================")
        print("Rolling %d samples:" % self.nRetries1)
        sw = ROOT.TStopwatch()
        sw.Start()
        
        steps = max(1, self.nRetries1/10)
        # c = p.createChi2(dh, RooFit.DataError(0))
        if self.rangeName == None:
            c = p.createChi2(dh, RooFit.Extended(True), RooFit.DataError(ROOT.RooAbsData.Poisson))
        else:
            # for some reason slower by factor ~10 in nretries1 and factor ~30 in nretries2
            # but also chi2 ~10^9 if range not excluded
            c = p.createChi2(dh, RooFit.Extended(True), RooFit.DataError(ROOT.RooAbsData.Poisson), RooFit.Range(self.rangeName), RooFit.SplitRange(False))

        if self.poi:
            #poi string is like "mu1=0_-1_1,mu2=0_0_0"
            pois=self.poi.split(',')
            for _p in pois:
                _p=_p.split('=')[0]
                w.var(_p).setConstant()
                print("Setting constant:", _p)

        # w.var("obs_x_J100yStar06").setConstant()
                
        if self.chi2fit:
            constraints = ROOT.RooArgSet()
            if self.chi2constraints:
                for _pdf in w.allPdfs():
                    if "ConstraintPdf" in _pdf.GetName():
                        constraints.add(_pdf)

            # crashes if "channellist" still in set of observables for RooConstraintSum
            realobs = ROOT.RooArgSet()
            for x in o:
                if x.InheritsFrom("RooRealVar"):
                    realobs.add(x)
                
            constraint_sum = ROOT.RooConstraintSum("constraint_sum", "constraint_sum", constraints, realobs)
            # constraint_sum = ROOT.RooConstraintSum("constraint_sum", "constraint_sum", constraints, ROOT.RooArgSet())
            constrained_chi2 = ROOT.RooFormulaVar("constrained_chi2", "0.5*@0+@1", ROOT.RooArgList(c, constraint_sum))
               
            minim = ROOT.RooMinimizer(constrained_chi2)
            minim.setStrategy(1);
            minim.setPrintLevel(-1);
            minim.setEps(1.e-2);
            minim.setMinimizerType("Minuit2");

        for i in range(self.nRetries1):
            if (i%steps == 0):
                print(i)
        
            if i>0:
                self.RandomizeParameters(np)
        
            chi2 = c.getVal()
            if (chi2 < best_chi2Pars[-1][0]):
                # do not know how to remove a snapshot from ws again :(
                # snapName = "bestPars_%d" % i
                # w.saveSnapshot(snapName, np)
                # bisect.insort(best_chi2Pars, (chi2, snapName))
                # if len(best_chi2Pars) > self.nRetries2:
                #     if best_chi2Pars[-1][1]:
                #         # remove snapshot from ws
                #         print("remove snapshot", best_chi2Pars[-1][1])
                #         w.removeSet(best_chi2Pars[-1][1])
                

                if len(best_chi2Pars) >= self.nRetries2 and best_chi2Pars[-1][1]:
                    # overwrite previous snapshot
                    snapName = best_chi2Pars[-1][1]
                else:
                    snapName = "bestPars_%d" % i

                w.saveSnapshot(snapName, np)
                bisect.insort(best_chi2Pars, (chi2, snapName))
                if len(best_chi2Pars) > self.nRetries2:
                    best_chi2Pars.pop()

        print(best_chi2Pars)
        
        # w.Print()

        print("==================")
        print("Finished sampling")
        sw.Stop()
        sw.Print()
        sw.Reset()
        sw.Start()
        
        print("Starting fit of %d best samples" % self.nRetries2)
            
        bestChi2 = float("inf")
        bestPars = None
        
        for  i in range(self.nRetries2):
            w.loadSnapshot(best_chi2Pars[i][1])

            if self.chi2fit:
                # p.chi2FitTo(dh, args_chi2)
                minim.minimize("Minuit2")
            else:
                p.fitTo(d, args)

            # c = p.createChi2(dh, RooFit.DataError(0))
            # c = p.createChi2(dh, RooFit.Extended(True), RooFit.DataError(RooAbsData.Poisson))
            thisFitChi2 = c.getVal()
            if (thisFitChi2 < bestChi2):
        	bestChi2 = thisFitChi2
                snapName = "bestPars"
                w.saveSnapshot(snapName, np)
        
            print("trial %2d: chi2=%.4f" % (i, thisFitChi2))
        
        print("==================")
        print("Finished fitting")
        sw.Stop()
        sw.Print()
        
        print("Best Total:")
        
        print("chi2 =", bestChi2)
        w.loadSnapshot("bestPars")
        for p in np:
            print(p.GetName(), p.getVal())
            
        print("==================")
        
        if self.updatews:
            w.Write(self.wsname)
            
        f.Close()
        
        return np,nbkg
        
def main(args):
    parser = argparse.ArgumentParser(description='%prog [options]')
    parser.add_argument('--wsfile', dest='wsfile', type=str, required=True, help='RooWorkspace file name')
    parser.add_argument('--wsname', dest='wsname', type=str, default="combWS", help='RooWorkspace name')
    parser.add_argument('--mcname', dest='mcname', type=str, default="ModelConfig", help='ModelConfig name')
    parser.add_argument('--dataname', dest='dataname', type=str, default="combData", help='RooDataSet name')
    parser.add_argument('--nRetries1', dest='nRetries1', type=int, default=10000, help='Number of trials for initial sampling')
    parser.add_argument('--nRetries2', dest='nRetries2', type=int, default=10, help='Number of tried fits')
    parser.add_argument('--seed', dest='seed', type=int, default=42, help='Seed for random number generator')
    parser.add_argument('--updatews', dest='updatews', type=strtobool, default=0, help='Write new initial pars to workspace')
    parser.add_argument('--chi2fit', dest='chi2fit', type=strtobool, default=0, help='Minimize chi2 instead of NLL')
    parser.add_argument('--chi2constraints', dest='chi2constraints', type=strtobool, default=1, help='Include constraint terms in chi2')
    parser.add_argument('--poi', dest='poi', type=str, help='POI name to fix')
    parser.add_argument('--rangeName', dest='rangeName', type=str, help='Name of range to restrict fit range')
    
    args = parser.parse_args(args)

    pf = PreFitter(
        wsfile = args.wsfile,
        wsname = args.wsname,
        mcname = args.mcname,
        dataname = args.dataname,
        nRetries1 = args.nRetries1,
        nRetries2 = args.nRetries2,
        seed = args.seed,
        updatews = args.updatews,
        chi2fit = args.chi2fit,
        chi2constraints = args.chi2constraints,
        poi = args.poi,
        rangeName = args.rangeName
    )

    print(pf.Fit())

if __name__ == "__main__":  
   sys.exit(main(sys.argv[1:]))   
