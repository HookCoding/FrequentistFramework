#!/usr/bin/env python
from __future__ import print_function

import ROOT
import sys, re, os, math, argparse, json

def doubleSidedCrystalBall(x, par):
   alpha_l = par[0] 
   alpha_h = par[1] 
   n_l     = par[2] 
   n_h     = par[3] 
   mean	   = par[4] 
   sigma   =  par[5]
   N	   = par[6]
   try:
      t = (x[0]-mean)/sigma

      fact1TLessMinosAlphaL = alpha_l/n_l
      fact2TLessMinosAlphaL = (n_l/alpha_l) - alpha_l -t
      fact1THigherAlphaH = alpha_h/n_h
      fact2THigherAlphaH = (n_h/alpha_h) - alpha_h +t
      
      if (-alpha_l <= t and alpha_h >= t):
          result = math.exp(-0.5*t*t)
      elif (t < -alpha_l):
          result = math.exp(-0.5*alpha_l*alpha_l)*math.pow(fact1TLessMinosAlphaL*fact2TLessMinosAlphaL, -n_l)
      elif (t > alpha_h):
          result = math.exp(-0.5*alpha_h*alpha_h)*math.pow(fact1THigherAlphaH*fact2THigherAlphaH, -n_h)
    
      return N*result
   except:
      return 0

def TF1DSCB(d):# pars

   mean=d["nominal_mean"]
   sigma=d["nominal_sigma"]
   alpha_l=d["nominal_alpha_l"]
   n_l=d["nominal_n_l"]
   alpha_h=d["nominal_alpha_h"]
   n_h=d["nominal_n_h"]
   print(mean,sigma,sigma,alpha_l,n_l,alpha_h,n_h)

   dscb = ROOT.TF1("dscb", doubleSidedCrystalBall, 0, 3000, 7)
   #dscb.SetParameters(pars[0], pars[1], pars[2], pars[3], pars[4], pars[5], pars[6])
   dscb.SetParameters(alpha_l,alpha_h,n_l,n_h,mean,sigma,100)

   return dscb

def GetNsig(histbkg, histsig, sigamp):
    histsig.Scale(1./histsig.Integral())
    # determine FWHM
    binSigLow = histsig.FindFirstBinAbove(histsig.GetMaximum()/2);
    binSigHigh = histsig.FindLastBinAbove(histsig.GetMaximum()/2);

    #need to seperate binSig and binBkg because the histograms may not start at same x
    binBkgLow  = histbkg.FindBin(histsig.GetBinCenter(binSigLow))
    binBkgHigh = histbkg.FindBin(histsig.GetBinCenter(binSigHigh))
    
    nBkg = histbkg.Integral(binBkgLow, binBkgHigh)
    fSig = histsig.Integral(binSigLow, binSigHigh)

    if nBkg > 0.:
        nSig = int(sigamp * math.sqrt(nBkg) / fSig)
    else:
        nSig = 0

    return nSig

def GetNsigTF1(histbkg, f1, sigamp, xmin=0, xmax=1e100):
    f1_integral = f1.Integral(f1.GetXmin(), f1.GetXmax())
    f1_max    = f1.GetMaximum(f1.GetXmin(), f1.GetXmax())
    f1_maxpos = f1.GetMaximumX(f1.GetXmin(), f1.GetXmax())
    print(f1_max,f1_maxpos,f1_integral)

    # determine FWHM
    posSigLow  = f1.GetX(0.5*f1_max, f1.GetXmin(), f1_maxpos)
    posSigHigh = f1.GetX(0.5*f1_max, f1_maxpos, f1.GetXmax())
 

    print(posSigLow,posSigHigh)
    posSigLow = max(xmin, posSigLow)
    posSigHigh = min(xmax, posSigHigh)
    print(posSigLow,posSigHigh)

    # find bins in bkg hist corresponding to FWHM range
    binBkgLow  = histbkg.FindBin(posSigLow)
    binBkgHigh = histbkg.FindBin(posSigHigh)
    print(binBkgLow,binBkgHigh)


    nBkg = histbkg.Integral(binBkgLow, binBkgHigh)
    fSig = f1.Integral(posSigLow, posSigHigh) / f1_integral

    if nBkg > 0.:
        nSig = int(sigamp * math.sqrt(nBkg) / fSig)
    else:
        nSig = 0

    print(nBkg,nSig)

    print("posSigLow:", posSigLow, "posSigHigh:", posSigHigh, "nBkg:", nBkg, "fSig:", fSig)


    return nSig

def InjectZprime(infile, histname, sigfile, sighist, sigamp, outfile, firsttoy=None, lasttoy=None):
    f_in = ROOT.TFile(infile, "READ")
    f_sig = ROOT.TFile(sigfile, "READ")

    h_sig = f_sig.Get(sighist)
    h_sig.SetDirectory(0)
    h_sig.Smooth(3)

    f_out = ROOT.TFile(outfile, "RECREATE")
    f_out.cd()

    gRand = ROOT.TRandom3()
    seed = 0

    for histKey in f_in.GetListOfKeys():
        histName = histKey.GetName()
        
        if not histname in histName:
            continue
        if firsttoy != None and lasttoy != None and re.search(r'.*_(\d+)', histName):
            #reduce size by omitting all other toys
            toy = int(re.search(r'.*_(\d+)', histName).group(1))
            if toy < firsttoy or toy > lasttoy:
                seed += 1
                continue

        hist = f_in.Get(histName).Clone()
        hinj = hist.Clone()
        hinjonly = hist.Clone("injectedSignal") 
        hinjonly.Reset("M")

        # define the parameters of the gaussian and fill it
        nSig = GetNsig(hist, h_sig, sigamp)
        if nSig > 0.:
            print('Injecting Signal ', sighist, ' Number of events = ', nSig, end=' ') 
            print(' (ntimes = ', sigamp, ')')

            gRand.SetSeed(seed)
            hinjonly.FillRandom(h_sig, nSig) 
            hinj.Add(hinjonly)

        hinj.Write(histName)
        hist.Write(histName+"_beforeInjection")
        hinjonly.Write(histName+"_injection")

        seed += 1

    print("writing file "+str(outfile))        
    f_out.Close()

def InjectDSCB(infile, histname, sigfile, sigamp, outfile, firsttoy=None, lasttoy=None, xmin=0, xmax=1e100):
    f_in = ROOT.TFile(infile, "READ")
    f_out = ROOT.TFile(outfile, "RECREATE")
    f_out.cd()

    gRand = ROOT.TRandom3()
    seed = 0

    for histKey in f_in.GetListOfKeys():
        histName = histKey.GetName()
        
        if not histname in histName:
            continue
        if firsttoy != None and lasttoy != None and re.search(r'.*_(\d+)', histName):
            #reduce size by omitting all other toys
            toy = int(re.search(r'.*_(\d+)', histName).group(1))
            if toy < firsttoy or toy > lasttoy:
                seed += 1
                continue

        hist = f_in.Get(histName).Clone()
        hinj = hist.Clone()
        hsig = hist.Clone("injectedSignal") 
        hsig.Reset("M")

        with open(sigfile, "r") as f: # this file needs to be the parametrized json file
            data = json.load(f)
        
        first_key = list(data.keys())[0]
        d = data[first_key]
        
        dscb = TF1DSCB(d)
   

        # define the parameters of the gaussian and fill it
        nSig = GetNsigTF1(hist, dscb, sigamp, xmin, xmax)
        if nSig > 0.:
            print('Injecting DSCB with mean = ', d["nominal_mean"], ' Number of events = ', nSig, end=' ') 
            print(' (ntimes = ', sigamp, ')')

            gRand.SetSeed(seed)
            hsig.FillRandom('dscb', nSig) 
            hinj.Add(hsig)

        hinj.Write(histName)
        hist.Write(histName+"_beforeInjection")
        hsig.Write(histName+"_injection")

        seed += 1
            
    f_out.Close()

def InjectZprime_DSCBlimits(infile, histname, sigfile, sigfile_dscb, sighist, sigamp, outfile, firsttoy=None, lasttoy=None, xmin=0, xmax=1e100):
    f_in = ROOT.TFile(infile, "READ")
    f_sig = ROOT.TFile(sigfile, "READ")

    h_sig = f_sig.Get(sighist)
    h_sig.SetDirectory(0)
    h_sig.Smooth(3)

    f_out = ROOT.TFile(outfile, "RECREATE")
    f_out.cd()

    gRand = ROOT.TRandom3()
    seed = 0
        

    for histKey in f_in.GetListOfKeys():
        histName = histKey.GetName()
        
        if not histname in histName:
            continue
        if firsttoy != None and lasttoy != None and re.search(r'.*_(\d+)', histName):
            #reduce size by omitting all other toys
            toy = int(re.search(r'.*_(\d+)', histName).group(1))
            if toy < firsttoy or toy > lasttoy:
                seed += 1
                continue

        hist = f_in.Get(histName).Clone()
        hinj = hist.Clone()
        hinjonly = hist.Clone("injectedSignal") 
        hinjonly.Reset("M")

        # define the parameters of the gaussian and fill it
        #nSig = GetNsig(hist, h_sig, sigamp) # do it using the dscb.................................

        with open(sigfile_dscb, "r") as f: # this file needs to be the parametrized json file
            data = json.load(f)
        
        first_key = list(data.keys())[0]
        d = data[first_key]        
        dscb = TF1DSCB(d)
   
        # define the parameters
        nSig = GetNsigTF1(hist, dscb, sigamp, xmin, xmax)
        # go back to the histogram from Z' montecarlo ..............................................


        if nSig > 0.:
            print('Injecting Signal ', sighist, ' Number of events = ', nSig, end=' ') 
            print(' (ntimes = ', sigamp, ')')

            gRand.SetSeed(seed)
            hinjonly.FillRandom(h_sig, nSig) 
            hinj.Add(hinjonly)

        hinj.Write(histName)
        hist.Write(histName+"_beforeInjection")
        hinjonly.Write(histName+"_injection")

        seed += 1

    print("writing file "+str(outfile))        
    f_out.Close()

def main(args):

    parser = argparse.ArgumentParser(description='%prog [options]')
    parser.add_argument('--infile', dest='infile', type=str, default='../Input/data/dijetTLAnlo/data_J75yStar03_range400_2079.root', help='original data file name')
    parser.add_argument('--histname', dest='histname', type=str, default='data', help='original data hist name')
    parser.add_argument('--sigfile', dest='sigfile', type=str, help='path to root file with histogram of signal histogram')
    parser.add_argument('--sigfile_dscb,', dest='sigfile_dscb', type=str,default='', help='path to histogram of signal histogram, this is the json file')
    parser.add_argument('--sighist', dest='sighist', type=str, help='histogram name of input signal')
    parser.add_argument('--sigamp', dest='sigamp', type=float, default=3, help='number of injected events (in sigmas of central bin)')
    parser.add_argument('--outfile', dest='outfile', type=str, default='', help='Output file name')
    parser.add_argument('--firsttoy', dest='firsttoy', type=int, help='Only consider toys larger than this number')
    parser.add_argument('--lasttoy', dest='lasttoy', type=int, help='Only consider toys lower than this number')

    args = parser.parse_args(args)

    searchstring =r"mRp(\d+)"
    print(args.sighist)
    print(searchstring)
    res=re.search(searchstring, args.sigfile)
    print(res)
    m=int(res.group(1))
    print(m)
    if args.outfile == "":
        # args.outfile = os.path.split(args.infile)[-1].replace(".root", "_mR%d_amp%.0f.root" % (m, args.sigamp))
        args.outfile = args.infile.replace(".root", "_Zprime%.0f_amp%.0f.root" % (m,  args.sigamp)) #.replace("/run_fivePar/", "/run_fivePar/injected/")
    

    
    if ".json" in args.sigfile:
      InjectDSCB(infile=args.infile,
                 histname=args.histname,
                 sigfile=args.sigfile, # sigfile needs to be the json file
                 sigamp=args.sigamp,
                 outfile=args.outfile,
                 firsttoy=args.firsttoy,
                 lasttoy=args.lasttoy)
    elif args.sigfile_dscb=="":
      InjectZprime(infile=args.infile,
                 histname=args.histname,
                 sigfile=args.sigfile,
                 sighist=args.sighist,
                 sigamp=args.sigamp,
                 outfile=args.outfile,
                 firsttoy=args.firsttoy,
                 lasttoy=args.lasttoy)
    else:
      InjectZprime_DSCBlimits(infile=args.infile,
                 histname=args.histname,
                 sigfile=args.sigfile, # root file with histogram to sampe from
                 sigfile_dscb=args.sigfile_dscb,# json file wich defines DSCB function
                 sighist=args.sighist,
                 sigamp=args.sigamp,
                 outfile=args.outfile,
                 firsttoy=args.firsttoy,
                 lasttoy=args.lasttoy)
if __name__ == "__main__":  
   sys.exit(main(sys.argv[1:]))   
