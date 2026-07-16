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
                 updatews=False):

        self.wsfile = wsfile
        self.wsname = wsname
        self.mcname = mcname
        self.dataname = dataname

        self.nRetries1 = nRetries1
        self.nRetries2 = nRetries2
        self.seed = seed
        self.updatews = updatews

        ROOT.Math.MinimizerOptions.SetDefaultMaxFunctionCalls(50000)
        self.rnd = ROOT.TRandom3(self.seed)
        ROOT.gROOT.ProcessLine( "RooMsgService::instance().setGlobalKillBelow(RooFit::ERROR);" )

    def RandomizeParameters(self, np):
        for p in np:
            if not "nbkg" in p.GetName() and not "nsig" in p.GetName():
                # p.setVal(self.rnd.Uniform(p.getMin(), p.getMax()))
                p.setVal(self.rnd.Gaus(0.5*(p.getMin()+p.getMax()), 0.1*(p.getMax()-p.getMin())))
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

        w.obj("nbkg").setVal(nbkg)
        w.obj("nbkg").setRange(0, 2*nbkg)

        args = ROOT.RooLinkedList()
        args.Add(ROOT.RooCmdArg(RooFit.Constrain(np)))
        args.Add(ROOT.RooCmdArg(RooFit.GlobalObservables(go)))
        args.Add(ROOT.RooCmdArg(RooFit.ConditionalObservables(co)))
        args.Add(ROOT.RooCmdArg(RooFit.Save(1)))
        args.Add(ROOT.RooCmdArg(RooFit.Hesse(0)))
        args.Add(ROOT.RooCmdArg(RooFit.Hesse(0)))
        args.Add(ROOT.RooCmdArg(RooFit.PrintLevel(-1)))
        args.Add(ROOT.RooCmdArg(RooFit.PrintLevel(-1)))
        # args.Add(ROOT.RooCmdArg(RooFit.BatchMode(1)))
        args.Add(ROOT.RooCmdArg(RooFit.Strategy(2)))

        best_chi2Pars = [(float("inf"),None)]
        
        print("==================")
        print("Rolling %d samples:" % self.nRetries1)
        sw = ROOT.TStopwatch()
        sw.Start()
        
        steps = max(1, self.nRetries1/10)
        c = p.createChi2(dh, RooFit.DataError(0))

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

            p.fitTo(d, args)

            c = p.createChi2(dh, RooFit.DataError(0))
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
        for p in np:
            print(p.GetName(), p.getVal())
            
        print("==================")
        
        # f.Close()
        if self.updatews:
            w.loadSnapshot("bestPars")
            # f = ROOT.TFile(self.wsfile
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
    )

    print(pf.Fit())

if __name__ == "__main__":  
   sys.exit(main(sys.argv[1:]))   
