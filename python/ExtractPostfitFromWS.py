#!/usr/bin/env python
import ROOT
import sys, re, os, math, argparse
from ROOT import *
import array
import json

#This scripts sometimes crashes with errors like "Error in `python': corrupted size vs. prev_size"
#It must be related to the way ROOT closes the file containing the RooWorkspace. Fortunately, the
#output is fine nevertheless.

#adapted from xmlAnaWSBuilder::auxUtil::getNDOF()
def getNPars(pdf, obs, exclSyst):
    params = pdf.getVariables()
    nuispdf = RooStats.MakeNuisancePdf(pdf, RooArgSet(obs), "nuisancePdf")

    counter=0
    
    for var in params:
        if(not var.isConstant() and
           var.GetName() != obs.GetName() and
           not (exclSyst and nuispdf and nuispdf.dependsOn(RooArgSet(var)))):
            # if exclSyst, do not count nuisance parameters
            counter+=1
        
    return counter

def expHist(h):
    for i in range(1, h.GetNbinsX()+1):
        if h.GetBinContent(i) != 0:
            h.SetBinContent(i, ROOT.TMath.Exp(h.GetBinContent(i)))
            h.SetBinError(i, h.GetBinError(i)*h.GetBinContent(i))

def _check_rebin_pair(rebinfile, rebinhist):
    """Refuse a half-given --rebinfile/--rebinhist pair.

    A pair, not two independent options: every use site tests `rebinfile and rebinhist`
    together, so half a pair would silently skip rebinning altogether (here) or silently fall
    back to the auto-generated dijetisrTLA binning, which stops at 1000 GeV (run_anaFit.py).
    Shared by both call sites - PostfitExtractor.__init__ below and run_anaFit.run_anaFit() -
    so the two guards cannot drift apart. See KNOWN_ISSUES.md issue 46.
    """
    if bool(rebinfile) != bool(rebinhist):
        raise ValueError(
            "rebinfile and rebinhist must be given together (got rebinfile=%r, rebinhist=%r). "
            "Supplying only one would silently fall back to the auto-generated binning, which "
            "stops at 1000 GeV." % (rebinfile, rebinhist)
        )

def _compute_chi2_terms(h_data, h_postfit, nbins, maskmin, maskmax, maskisbinnumber, useSumW2):
    """Accumulate chi2 over the unmasked bins and collect every defined per-bin residual.

    A bin with valueErrorData<=0 or postFitValue<=0 is skipped entirely - not counted in chi2,
    chi2bins, maskedchi2bins or residuals. That silent omission is KNOWN_ISSUES issue 41,
    preserved here rather than fixed.
    """
    chi2 = 0.
    chi2bins = 0
    maskedchi2bins = 0
    residuals = []

    for ibin in range(1, nbins+1):
        valueErrorData = h_data.GetBinError(ibin)
        valueData = h_data.GetBinContent(ibin)
        postFitValue = h_postfit.GetBinContent(ibin)
        if maskisbinnumber:
            binCenter = ibin + 0.5
        else:
            binCenter = h_data.GetBinCenter(ibin)

        if valueErrorData > 0. and postFitValue > 0.:
            if useSumW2:
                binSig = (valueData - postFitValue)/valueErrorData
            else:
                binSig = (valueData - postFitValue)/math.sqrt(postFitValue)

            residuals.append((ibin, binSig))

            if binCenter < maskmin or binCenter > maskmax:
                chi2bins += 1
                chi2 += binSig*binSig
            else:
                maskedchi2bins += 1

    return chi2, chi2bins, maskedchi2bins, residuals

def _degrees_of_freedom(chi2bins, npars):
    return chi2bins - npars

def _chi2_probability(chi2, ndof):
    return ROOT.Math.chisquared_cdf_c(chi2, ndof)

def _build_residual_histogram(h_postfit, channelname, residuals):
    h_residuals = h_postfit.Clone(channelname+"/residuals")
    h_residuals.SetDirectory(0)
    h_residuals.Reset("M")

    for ibin, binSig in residuals:
        h_residuals.SetBinContent(ibin, binSig)
        h_residuals.SetBinError(ibin, 0)

    return h_residuals

def _build_chi2_summary(chi2, chi2bins, npars, ndof, pval):
    # ndoferr is hardcoded to 0 below (there is no code path that sets it), so bin 2's error is
    # always 0 today. Pinned as-is: a future non-zero ndoferr is then a visible change.
    ndoferr = 0.

    h_chi2 = TH1D("chi2", "chi2", 6, 0, 6)
    h_chi2.SetDirectory(0)
    h_chi2.SetBinContent(1, chi2)
    h_chi2.SetBinError(1, 0)
    h_chi2.SetBinContent(2, chi2/ndof)
    h_chi2.SetBinError(2, ndoferr*chi2/(ndof*ndof))
    h_chi2.SetBinContent(3, chi2bins)
    h_chi2.SetBinError(3, 0)
    h_chi2.SetBinContent(4, npars)
    h_chi2.SetBinError(4, 0)
    h_chi2.SetBinContent(5, ndof)
    h_chi2.SetBinError(5, ndoferr)
    h_chi2.SetBinContent(6, pval)
    h_chi2.SetBinError(6, 0)

    h_chi2.GetXaxis().SetBinLabel(1, "chi2")
    h_chi2.GetXaxis().SetBinLabel(2, "chi2/ndof")
    h_chi2.GetXaxis().SetBinLabel(3, "nbins")
    h_chi2.GetXaxis().SetBinLabel(4, "npars")
    h_chi2.GetXaxis().SetBinLabel(5, "ndof")
    h_chi2.GetXaxis().SetBinLabel(6, "pval")

    return h_chi2

def _record_chi2(extractor, channelname, chi2, chi2bins, npars, ndof, pval, h_residuals, h_chi2):
    extractor.channel_chi2[channelname] = chi2
    extractor.channel_nbins[channelname] = chi2bins
    extractor.channel_npars[channelname] = npars
    extractor.channel_ndof[channelname] = ndof
    extractor.channel_pval[channelname] = pval

    extractor.channel_hresiduals[channelname] = h_residuals
    extractor.channel_hchi2[channelname] = h_chi2

def _print_chi2_summary(chi2, chi2bins, npars, ndof, pval):
    print()
    print('TEST chi2bins', chi2bins)
    print('TEST npars', npars)
    print('TEST ndof', ndof)
    print('TEST chi2', chi2)
    print('TEST pval', pval)
    print('TEST chi2/ndof', chi2/ndof)

def _bin_edges_from_data(h_data, nBins, datafirstbin):
    """Reconstruct the postfit bin edges by reading them off the data histogram.

    The pdf histogram knows how many bins the fit had but not where they are: createHistogram()
    gives it the pdf observable's own uniform binning. The edges come from the data instead,
    offset by datafirstbin - the bin just below the fit range - so that postfit bin i lands on
    data bin i+datafirstbin.
    """
    binEdges = []
    for i in range(1, nBins+2):
        binEdges.append(h_data.GetBinLowEdge(i+datafirstbin))
    return binEdges

def _postfit_histogram(hpdf, nBins, binEdges):
    """Copy the pdf histogram's contents onto the data binning, bin index by bin index.

    Not a rebinning: hpdf's own x axis is the pdf observable's range, and only the ordinal
    position of each bin carries over. Errors are set to 0 - the postfit curve has none here.
    """
    h_postfit = TH1D("postfit", "postfit", nBins, array.array('d', binEdges))
    h_postfit.SetDirectory(0)

    for ibin in range(1, nBins+1):
        h_postfit.SetBinContent(ibin, hpdf.GetBinContent(ibin))
        h_postfit.SetBinError(ibin, 0)

    return h_postfit

def _crop_data(h_data, nBins, binEdges):
    """Rebin the full data histogram down onto the fitted range's binning."""
    h_data_crop = h_data.Rebin(nBins, "h_data_crop", array.array('d', binEdges))
    h_data_crop.SetDirectory(0)
    return h_data_crop

def _rebin_edges(rebinfile, rebinhist, h_postfit):
    """Read the resolution binning and keep only the edges inside the fitted range.

    The upper limit is h_postfit.GetBinLowEdge(GetNbinsX()+2) - one bin past the last edge, not
    the last edge itself. TAxis computes an out-of-range bin from the *average* width
    (xmin + (bin-1)*(xmax-xmin)/nbins), so on a non-uniform postfit that limit would not be the
    real last bin width. Both locked analyses fit a 1 GeV uniform range (J100 481-3000, J50
    302-2997), so it is exactly one GeV past the end and admits no extra edge. Pinned by test
    rather than changed.
    """
    f_rebin = ROOT.TFile(rebinfile, "READ")
    h_rebin = f_rebin.Get(rebinhist)

    binEdges = []
    nBins = h_rebin.GetNbinsX()
    for i in range(1, nBins+2):
        edge = h_rebin.GetBinLowEdge(i)
        if edge < h_postfit.GetBinLowEdge(1) or edge > h_postfit.GetBinLowEdge(h_postfit.GetNbinsX()+2):
            continue
        binEdges.append(edge)

    f_rebin.Close()

    return binEdges

def _rebin_channel(h_postfit, h_data, binEdges, datahist):
    """Rebin one channel's postfit and data pair onto the resolution binning.

    Both are detached explicitly. TH1::Rebin(n, newname, edges) clones through gDirectory, so
    the result is owned by whatever directory happens to be current - gROOT in practice, but a
    TFile if one were open, and then these would die with it. These are the histograms
    run_anaFit.py:189 reads the gating p-value from.
    """
    edges = array.array('d', binEdges)

    h_postfit_rebinned = h_postfit.Rebin(len(binEdges)-1, "postfit", edges)
    h_data_rebinned = h_data.Rebin(len(binEdges)-1, datahist, edges)

    h_postfit_rebinned.SetDirectory(0)
    h_data_rebinned.SetDirectory(0)

    return h_postfit_rebinned, h_data_rebinned

def getChi2(extractor, channelname, npars, useSumW2=False):
    h_data = extractor.channel_hdata[channelname]
    h_postfit = extractor.channel_hpostfit[channelname]
    nbins = h_postfit.GetNbinsX()

    chi2, chi2bins, maskedchi2bins, residuals = _compute_chi2_terms(
        h_data, h_postfit, nbins,
        extractor.maskmin, extractor.maskmax, extractor.maskisbinnumber, useSumW2,
    )

    ndof = _degrees_of_freedom(chi2bins, npars)
    pval = _chi2_probability(chi2, ndof)

    h_residuals = _build_residual_histogram(h_postfit, channelname, residuals)
    h_chi2 = _build_chi2_summary(chi2, chi2bins, npars, ndof, pval)

    _print_chi2_summary(chi2, chi2bins, npars, ndof, pval)
    _record_chi2(extractor, channelname, chi2, chi2bins, npars, ndof, pval, h_residuals, h_chi2)

def _open_workspace(wsfile, wsname):
    """Open the fit-result file and retrieve the workspace.

    Both are returned. The workspace is owned by the file and dies with it, so the caller has to
    hold the file open for as long as it touches the workspace or anything the workspace owns -
    the pdf, the category, the observables, the dataset. Extract() closes it on its last line.
    """
    root_file = ROOT.TFile(wsfile, "READ")
    workspace = root_file.Get(wsname)
    return root_file, workspace

def _load_data_histogram(datafile, datahist, undolog):
    """Read the data histogram, detach it, and close the file behind it.

    The detachment is what makes closing here safe, and it is why this returns the histogram
    alone where _open_workspace has to return its file too.
    """
    fd = ROOT.TFile(datafile, "READ")
    h_data = fd.Get(datahist)
    h_data.SetDirectory(0)
    if undolog:
        expHist(h_data)
    fd.Close()
    return h_data

def _model_components(workspace, modelname):
    """Pull the model's pdf, the channel category and the split dataset out of the workspace.

    Everything but nChan is workspace-owned and must not outlive it.

    The two prints stay inside rather than move to the caller: data.split() emits RooFit messages
    of its own, so lifting them out would reorder the log.
    """
    model = workspace.obj(modelname)
    pdf = model.GetPdf()
    cat = pdf.indexCat()
    nChan = cat.numBins("")

    print ("There are %d channels" % nChan)

    obs = pdf.getObservables(model.GetObservables())
    obs.Print()

    data = workspace.data("combData")
    dataList = data.split( cat, True )

    return pdf, cat, nChan, obs, data, dataList

def _channel_npars(pdfi, x, externalnpars):
    """Parameter count for the degrees of freedom: counted off the pdf unless overridden.

    getNPars() is called either way, as today. It is not free - it builds a nuisance pdf - but
    skipping it when externalnpars is set would change what RooFit is asked to construct.
    """
    npars = getNPars(pdfi, x, exclSyst=True)
    if externalnpars != None:
        npars = externalnpars
    return npars

def _background_only_pdf(workspace, channelname):
    """Build the extended background-only pdf for one channel.

    This *mutates* a workspace opened "READ": factory() adds pdf__background_ext_<channel> to it.
    That is harmless only because Extract() reopens the file on every call and so gets a fresh
    workspace each time; a second call for the same channel on the same workspace would be asked
    to re-create an object that already exists.
    """
    return workspace.factory("ExtendPdf::pdf__background_ext_"+channelname+"(pdf__background_"+channelname+",yield__background_"+channelname+")")

def _pdf_histogram(pdfi, x, expectedEvents, undolog):
    """Turn a pdf into a histogram scaled to its expected number of events.

    The bare except is preserved as-is: a pdf whose histogram integrates to zero leaves the
    histogram unscaled rather than raising.

    Used by the nominal block only. The background-only block scales a different histogram from
    the one it reads and therefore cannot call this - see the comment there.
    """
    hpdf = pdfi.createHistogram("hpdf", x)

    # hpdf.Scale(expectedEvents/hpdf.Integral())
    try:
        hpdf.Scale(expectedEvents/hpdf.Integral())
        # hpdf.Scale(data.sumEntries()/hpdf.Integral())
    except:
        pass

    if undolog:
        expHist(hpdf)

    return hpdf

class PostfitExtractor:
    def __init__(self,
                 wsfile, 
                 datafile, 
                 datahist, 
                 wsname="combWS", 
                 modelname="ModelConfig", 
                 datafirstbin=0, 
                 rebinfile=None, 
                 rebinhist=None, 
                 externalnpars=None, 
                 maskmin=-1, 
                 maskmax=-1,
                 bkgonly=False,
                 undolog=False,
                 maskisbinnumber=False,
                 useSumW2=False):

        # Guarded here rather than only in the CLI parser so the direct construction in
        # run_anaFit.py is covered too. See _check_rebin_pair()'s docstring above.
        _check_rebin_pair(rebinfile, rebinhist)

        self.wsfile = wsfile
        self.datafile = datafile
        self.datahist = datahist
        self.wsname = wsname
        self.modelname = modelname
        self.datafirstbin = datafirstbin
        self.rebinfile = rebinfile
        self.rebinhist = rebinhist
        self.externalnpars = externalnpars
        self.maskmin = maskmin
        self.maskmax = maskmax
        self.bkgonly = bkgonly
        self.undolog = undolog
        self.maskisbinnumber = maskisbinnumber
        self.useSumW2 = useSumW2
        self.h_data = None
        self.channel_chi2 = {}
        self.channel_nbins = {}
        self.channel_npars = {}
        self.channel_ndof = {}
        self.channel_pval = {}
        self.channel_hdata = {}
        self.channel_hpostfit = {}
        self.channel_hchi2 = {}
        self.channel_hresiduals = {}

    def Extract(self):
        
        f, w = _open_workspace(self.wsfile, self.wsname)

        self.h_data = _load_data_histogram(self.datafile, self.datahist, self.undolog)

        pdf, cat, nChan, obs, data, dataList = _model_components(w, self.modelname)

        # A local, not self.datafirstbin. The two reassignments in the rebinning blocks below
        # used to overwrite the constructor argument with a bin number in a different histogram,
        # so a second Extract() computed its bin edges from that instead. KNOWN_ISSUES issue 51.
        datafirstbin = self.datafirstbin

        for i in range(nChan):
            datai = dataList.At( i )
            channelname = cat.getLabel()
            pdfi = pdf.getPdf(channelname)
            x = pdfi.getObservables(datai).first()
            npars = _channel_npars(pdfi, x, self.externalnpars)

            if self.bkgonly:
                pdf_bkg = _background_only_pdf(w, channelname)

            expectedEvents = pdfi.expectedEvents(RooArgSet(x))
            hpdf = _pdf_histogram(pdfi, x, expectedEvents, self.undolog)

            print ("Channel %s:" % channelname)
            print ("Expected:", expectedEvents)
            print ("sumEntries:", data.sumEntries())
            print ("Integral:", hpdf.Integral())

            nBins = hpdf.GetNbinsX()
            binEdges = _bin_edges_from_data(self.h_data, nBins, datafirstbin)

            h_postfit = _postfit_histogram(hpdf, nBins, binEdges)

            self.channel_hdata[channelname] = _crop_data(self.h_data, nBins, binEdges)
            self.channel_hpostfit[channelname] = h_postfit

            getChi2(extractor=self, channelname=channelname, npars=npars, useSumW2=self.useSumW2)

            if self.bkgonly:
                expectedEvents_bkg = pdf_bkg.expectedEvents(RooArgSet(x))
                hpdf_bkg = pdf_bkg.createHistogram("hpdf_bkg", x)
                # Deliberately NOT _pdf_histogram(): the line below scales hpdf, while the
                # histogram actually read into the background-only postfit is hpdf_bkg, left
                # unscaled. That is KNOWN_ISSUES issue 49. Calling the shared helper here would
                # silently correct it and move the background-only p-value, which is the number
                # run_anaFit.py:189 gates on.
                # hpdf_bkg.Scale(expectedEvents_bkg/hpdf_bkg.Integral())
                try:
                    hpdf.Scale(expectedEvents_bkg/hpdf.Integral())
                    # hpdf_bkg.Scale(data.sumEntries()/hpdf_bkg.Integral())
                except:
                    pass

                if self.undolog:
                    expHist(hpdf_bkg)

                channelname_bkg = channelname+"_bkgonly"

                h_postfit_bkg = _postfit_histogram(hpdf_bkg, nBins, binEdges)

                self.channel_hdata[channelname_bkg] = _crop_data(self.h_data, nBins, binEdges)
                # if a mask was used we need to normalize the postfit correctly
#                if self.maskmin > -1 or self.maskmax > -1:
#                    h_postfit_bkg = self.normalizePostFit(h_postfit_bkg, self.channel_hdata[channelname_bkg])
                self.channel_hpostfit[channelname_bkg] = h_postfit_bkg
    
                getChi2(extractor=self, channelname=channelname_bkg, npars=npars, useSumW2=self.useSumW2)

            binEdges = None
            if self.rebinfile and self.rebinhist:
                binEdges = _rebin_edges(self.rebinfile, self.rebinhist, h_postfit)

                rebinnedchannelname=channelname+"_rebinned"
                (self.channel_hpostfit[rebinnedchannelname],
                 self.channel_hdata[rebinnedchannelname]) = _rebin_channel(
                    self.channel_hpostfit[channelname], self.channel_hdata[channelname],
                    binEdges, self.datahist)
                datafirstbin = self.channel_hdata[rebinnedchannelname].FindBin(datafirstbin) - 1

                getChi2(extractor=self, channelname=rebinnedchannelname, npars=npars, useSumW2=self.useSumW2)

            if self.bkgonly and self.rebinfile and self.rebinhist:
                rebinnedchannelname_bkg=channelname_bkg+"_rebinned"
                (self.channel_hpostfit[rebinnedchannelname_bkg],
                 self.channel_hdata[rebinnedchannelname_bkg]) = _rebin_channel(
                    self.channel_hpostfit[channelname_bkg], self.channel_hdata[channelname_bkg],
                    binEdges, self.datahist)
                datafirstbin = self.channel_hdata[rebinnedchannelname_bkg].FindBin(datafirstbin) - 1

                getChi2(extractor=self, channelname=rebinnedchannelname_bkg, npars=npars, useSumW2=self.useSumW2)
    
        f.Close()

    def WriteRoot(self, outfile, dirPerCategory=False):
        # The dirPerCategory=False branch subscripted dict_values, which Python 3 does not allow,
        # so it raised TypeError on every invocation it ever had. Deleted rather than repaired:
        # there is no behaviour to preserve and inventing one would be a new feature. Refused
        # explicitly, and before the output file is touched, rather than silently writing an
        # empty one. See KNOWN_ISSUES.md issue 54.
        if not dirPerCategory:
            raise ValueError(
                "WriteRoot(dirPerCategory=False) is not implemented. The single-directory branch "
                "raised TypeError on every call under Python 3 and has been removed; pass "
                "dirPerCategory=True."
            )

        if not self.h_data:
            self.Extract()

        fout = ROOT.TFile(outfile, "RECREATE")

        for channelname in self.channel_chi2:
            d = fout.mkdir(channelname)
            d.cd()

            self.channel_hdata[channelname].Write("data")
            self.channel_hpostfit[channelname].Write("postfit")
            self.channel_hresiduals[channelname].Write("residuals")
            self.channel_hchi2[channelname].Write("chi2")

        fout.Close()

    def GetChi2(self, channelname=None):
        if not self.channel_chi2:
            self.Extract()
        if channelname:
            return self.channel_chi2[channelname]
        else:
            return next(iter(self.channel_chi2.values()))

    def GetNbins(self, channelname=None):
        if not self.channel_nbins:
            self.Extract()
        if channelname:
            return self.channel_nbins[channelname]
        else:
            return next(iter(self.channel_nbins))

    def GetNpars(self, channelname=None):
        if not self.channel_npars:
            self.Extract()
        if channelname:
            return self.channel_npars[channelname]
        else:
            return next(iter(self.channel_npars))

    def GetNdof(self, channelname=None):
        if not self.channel_ndof:
            self.Extract()
        if channelname:
            return self.channel_ndof[channelname]
        else:
            return next(iter(self.channel_ndof))
        
    def GetPval(self, channelname=None):
        if not self.channel_pval:
            self.Extract()
        if channelname:
            return self.channel_pval[channelname]
        else:
            return next(iter(self.channel_pval.values()))

    def GetH1Chi2(self, channelname=None):
        if not self.channel_hchi2:
            self.Extract()
        if channelname:
            return self.channel_hchi2[channelname]
        else:
            return next(iter(self.channel_hchi2))

    def GetH1Postfit(self, channelname=None):
        if not self.channel_hpostfit:
            self.Extract()
        if channelname:
            return self.channel_hpostfit[channelname]
        else:
            return next(iter(self.channel_hpostfit))

    def GetH1Residuals(self, channelname=None):
        if not self.channel_hresiduals:
            self.Extract()
        if channelname:
            return self.channel_hresiduals[channelname]
        else:
            return next(iter(self.channel_hresiduals))

    def GetCategories(self):
        if not self.channel_chi2:
            self.Extract()
        return self.channel_chi2.keys()


def main(args):

    parser = argparse.ArgumentParser(description='%prog [options]')
    parser.add_argument('--datafile', dest='datafile', type=str, default='../Input/data/dijetTLAnlo/data_J75yStar03_range400_2079.root', help='original data file name (to get binning from)')
    parser.add_argument('--datahist', dest='datahist', type=str, default='data', help='original data hist name (to get binning from)')
    parser.add_argument('--datafirstbin', dest='datafirstbin', type=int, default=0, help='First bin in data histogram considered in fit. 0 for first non-underflow bin')
    parser.add_argument('--wsfile', dest='wsfile', type=str, help='Workspace file name')
    parser.add_argument('--wsname', dest='wsname', type=str, default='combWS', help='Name of workspace')
    parser.add_argument('--modelname', dest='modelname', type=str, default='ModelConfig', help='Name of model in workspace')
    parser.add_argument('--outfile', dest='outfile', type=str, default='', help='Output file name')
    parser.add_argument('--rebinfile', dest='rebinfile', type=str, help='Specify if rebinning to different template wanted')
    parser.add_argument('--rebinhist', dest='rebinhist', type=str, help='Specify if rebinning to different template wanted')
    parser.add_argument('--externalnpars', dest='externalnpars', default=None, type=float, help='Number of effective parameters for chi2 calculation')
    parser.add_argument('--maskmin', dest='maskmin', type=int, default=-1, help='Masked range to exclude from chi2 calculation')
    parser.add_argument('--maskmax', dest='maskmax', type=int, default=-1, help='Masked range to exclude from chi2 calculation')
    parser.add_argument('--dirpercategory', dest='dirpercategory', action='store_true', help='Create one output directory per channel (also for rebinning)')
    parser.add_argument('--bkgonly', dest='bkgonly', action='store_true', help='Add directory for bkg-only postfit. Needs --dirpercategory set.')
    parser.add_argument('--undolog', dest='undolog', action='store_true', help='Perform exp(N) on all data and fit histograms if log(N) was used for fitting.')
    parser.add_argument('--maskisbinnumber', dest='maskisbinnumber', action='store_true', help='Interprete maskmin and maskmax as bin numbers instead of values on the x-axis of the datahist. (Necessary for hacked NLOFit bins)')
    parser.add_argument('--useSumW2', dest='useSumW2', action='store_true', help='Use data histogram errors instead of sqrt(N_fit) for the residual calculation.')

    args = parser.parse_args(args)

    pfe = PostfitExtractor(
        wsfile=args.wsfile,
        datafile=args.datafile,
        datahist=args.datahist,
        datafirstbin=args.datafirstbin,
        wsname=args.wsname,
        modelname=args.modelname,
        rebinfile=args.rebinfile,
        rebinhist=args.rebinhist,
        externalnpars=args.externalnpars,
        maskmin=args.maskmin,
        maskmax=args.maskmax,
        bkgonly=args.bkgonly,
        undolog=args.undolog,
        maskisbinnumber=args.maskisbinnumber,
        useSumW2=args.useSumW2
    )
    pfe.Extract()
    pfe.WriteRoot(args.outfile, args.dirpercategory)
    
    print ("Finished ExtractPostfitFromWS")

if __name__ == "__main__":  
   sys.exit(main(sys.argv[1:]))   
