#!/usr/bin/env python
import argparse
import array
import math
import sys

import ROOT

# This scripts sometimes crashes with errors like "Error in `python': corrupted size vs. prev_size"
# It must be related to the way ROOT closes the file containing the RooWorkspace. Fortunately, the
# output is fine nevertheless.


# adapted from xmlAnaWSBuilder::auxUtil::getNDOF()
def getNPars(pdf, obs, exclSyst):
    params = pdf.getVariables()
    nuispdf = ROOT.RooStats.MakeNuisancePdf(pdf, ROOT.RooArgSet(obs), "nuisancePdf")

    counter = 0

    for var in params:
        if (
            not var.isConstant()
            and var.GetName() != obs.GetName()
            and not (exclSyst and nuispdf and nuispdf.dependsOn(ROOT.RooArgSet(var)))
        ):
            # if exclSyst, do not count nuisance parameters
            counter += 1

    return counter


def expHist(h):
    for i in range(1, h.GetNbinsX() + 1):
        if h.GetBinContent(i) != 0:
            h.SetBinContent(i, ROOT.TMath.Exp(h.GetBinContent(i)))
            h.SetBinError(i, h.GetBinError(i) * h.GetBinContent(i))


def getChi2(extractor, channelname, npars, useSumW2=False):
    chi2 = 0.0
    chi2bins = 0
    maskedchi2bins = 0

    h_data = extractor.channel_hdata[channelname]
    h_postfit = extractor.channel_hpostfit[channelname]
    h_residuals = h_postfit.Clone(channelname + "/residuals")
    h_residuals.SetDirectory(0)
    h_residuals.Reset("M")

    for ibin in range(1, h_residuals.GetNbinsX() + 1):
        # valueErrorData = h_data.GetBinError(ibin+extractor.datafirstbin)
        # valueData = h_data.GetBinContent(ibin+extractor.datafirstbin)
        # postFitValue = h_postfit.GetBinContent(ibin)
        # binCenter = h_data.GetBinCenter(extractor.datafirstbin+ibin)

        valueErrorData = h_data.GetBinError(ibin)
        valueData = h_data.GetBinContent(ibin)
        postFitValue = h_postfit.GetBinContent(ibin)
        if extractor.maskisbinnumber:
            binCenter = ibin + 0.5
        else:
            binCenter = h_data.GetBinCenter(ibin)

        binSig = 0.0
        if valueErrorData > 0.0 and postFitValue > 0.0:
            if useSumW2:
                binSig = (valueData - postFitValue) / valueErrorData
            else:
                binSig = (valueData - postFitValue) / math.sqrt(postFitValue)

            h_residuals.SetBinContent(ibin, binSig)
            h_residuals.SetBinError(ibin, 0)

            if binCenter < extractor.maskmin or binCenter > extractor.maskmax:
                # print("binCenter %.1f outside of maskmin %.1f and maskmax %.1f" % (binCenter, extractor.maskmin, extractor.maskmax))  # noqa: E501
                chi2bins += 1
                chi2 += binSig * binSig
            else:
                # print("binCenter %.1f inside of maskmin %.1f and maskmax %.1f" % (binCenter, extractor.maskmin, extractor.maskmax))  # noqa: E501
                maskedchi2bins += 1

    ndof = chi2bins - npars
    ndoferr = 0.0

    pval = ROOT.Math.chisquared_cdf_c(chi2, ndof)

    h_chi2 = ROOT.TH1D("chi2", "chi2", 6, 0, 6)
    h_chi2.SetDirectory(0)
    h_chi2.SetBinContent(1, chi2)
    h_chi2.SetBinError(1, 0)
    h_chi2.SetBinContent(2, chi2 / ndof)
    h_chi2.SetBinError(2, ndoferr * chi2 / (ndof * ndof))
    h_chi2.SetBinContent(3, chi2bins)
    h_chi2.SetBinError(3, 0)
    h_chi2.SetBinContent(4, npars)
    h_chi2.SetBinError(4, 0)
    h_chi2.SetBinContent(5, ndof)
    h_chi2.SetBinError(5, ndoferr)
    h_chi2.SetBinContent(6, pval)
    h_chi2.SetBinError(6, 0)

    print()
    print("TEST chi2bins", chi2bins)
    print("TEST npars", npars)
    print("TEST ndof", ndof)
    print("TEST chi2", chi2)
    print("TEST pval", pval)
    print("TEST chi2/ndof", chi2 / ndof)

    h_chi2.GetXaxis().SetBinLabel(1, "chi2")
    h_chi2.GetXaxis().SetBinLabel(2, "chi2/ndof")
    h_chi2.GetXaxis().SetBinLabel(3, "nbins")
    h_chi2.GetXaxis().SetBinLabel(4, "npars")
    h_chi2.GetXaxis().SetBinLabel(5, "ndof")
    h_chi2.GetXaxis().SetBinLabel(6, "pval")

    extractor.channel_chi2[channelname] = chi2
    extractor.channel_nbins[channelname] = chi2bins
    extractor.channel_npars[channelname] = npars
    extractor.channel_ndof[channelname] = ndof
    extractor.channel_pval[channelname] = pval

    extractor.channel_hresiduals[channelname] = h_residuals
    extractor.channel_hchi2[channelname] = h_chi2


class PostfitExtractor:
    def __init__(
        self,
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
        useSumW2=False,
    ):
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

    def normalizePostFit(self, h_postfit, h_data):
        """
        Normalize postfit so that the number of events in the fitted regions agree
        """

        nEvents_data_min = h_data.Integral(1, h_data.GetXaxis().FindBin(self.maskmin))
        nEvents_data_max = h_data.Integral(
            h_data.GetXaxis().FindBin(self.maskmax), h_data.GetNbinsX() + 1
        )

        nEvents_postfit_min = h_postfit.Integral(1, h_postfit.GetXaxis().FindBin(self.maskmin))
        nEvents_postfit_max = h_postfit.Integral(
            h_postfit.GetXaxis().FindBin(self.maskmax), h_postfit.GetNbinsX() + 1
        )

        h_postfit.Scale(
            (nEvents_data_min + nEvents_data_max) / (nEvents_postfit_min + nEvents_postfit_max)
        )

        return h_postfit

    def _open_workspace_and_data(self):
        f = ROOT.TFile(self.wsfile, "READ")
        w = f.Get(self.wsname)

        fd = ROOT.TFile(self.datafile, "READ")
        self.h_data = fd.Get(self.datahist)
        self.h_data.SetDirectory(0)
        if self.undolog:
            expHist(self.h_data)

        model = w.obj(self.modelname)
        pdf = model.GetPdf()
        cat = pdf.indexCat()
        nChan = cat.numBins("")

        print("There are %d channels" % nChan)

        obs = pdf.getObservables(model.GetObservables())
        obs.Print()

        data = w.data("combData")
        dataList = data.split(cat, True)

        return f, fd, w, pdf, cat, data, dataList, nChan

    def _build_channel_postfit_histogram(self, pdfi, x, channelname, npars, data):
        expectedEvents = pdfi.expectedEvents(ROOT.RooArgSet(x))
        hpdf = pdfi.createHistogram("hpdf", x)

        # hpdf.Scale(expectedEvents/hpdf.Integral())
        try:
            hpdf.Scale(expectedEvents / hpdf.Integral())
            # hpdf.Scale(data.sumEntries()/hpdf.Integral())
        except:  # noqa: E722 - bare except preserved verbatim from the original script
            pass

        if self.undolog:
            expHist(hpdf)

        print("Channel %s:" % channelname)
        print("Expected:", expectedEvents)
        print("sumEntries:", data.sumEntries())
        print("Integral:", hpdf.Integral())

        binEdges = []
        nBins = hpdf.GetNbinsX()
        for i in range(1, nBins + 2):
            binEdges.append(self.h_data.GetBinLowEdge(i + self.datafirstbin))

        h_postfit = ROOT.TH1D("postfit", "postfit", nBins, array.array("d", binEdges))
        h_postfit.SetDirectory(0)

        for ibin in range(1, nBins + 1):
            h_postfit.SetBinContent(ibin, hpdf.GetBinContent(ibin))
            h_postfit.SetBinError(ibin, 0)

        self.channel_hdata[channelname] = self.h_data.Rebin(
            nBins, "h_data_crop", array.array("d", binEdges)
        )
        self.channel_hdata[channelname].SetDirectory(0)
        self.channel_hpostfit[channelname] = h_postfit

        getChi2(extractor=self, channelname=channelname, npars=npars, useSumW2=self.useSumW2)

        return nBins, binEdges, hpdf

    def _build_bkgonly_variant(self, w, channelname, x, hpdf, nBins, binEdges, npars):
        # pdf_bkg_unscaled/yield_bkg are assigned but never read - preserved
        # verbatim from the original script, not removed (see guardrail
        # against fixing unrelated pre-existing issues).
        pdf_bkg_unscaled = w.obj("pdf__background_" + channelname)  # noqa: F841
        yield_bkg = w.obj("yield__background_" + channelname)  # noqa: F841
        pdf_bkg = w.factory(
            "ExtendPdf::pdf__background_ext_"
            + channelname
            + "(pdf__background_"
            + channelname
            + ",yield__background_"
            + channelname
            + ")"
        )

        expectedEvents_bkg = pdf_bkg.expectedEvents(ROOT.RooArgSet(x))
        hpdf_bkg = pdf_bkg.createHistogram("hpdf_bkg", x)
        # hpdf_bkg.Scale(expectedEvents_bkg/hpdf_bkg.Integral())
        try:
            # NOTE: this scales `hpdf` (the main channel's already-consumed
            # histogram), not `hpdf_bkg`, exactly as in the original script
            # - preserved verbatim, not fixed, since it is not in scope for
            # this chunk (see doc/TIER3_COMPLETION_PLAN.md Chunk 16's own
            # scoped-bugs list and doc/ACTIVITY_LOG.md's Chunk 16.B entry).
            hpdf.Scale(expectedEvents_bkg / hpdf.Integral())
            # hpdf_bkg.Scale(data.sumEntries()/hpdf_bkg.Integral())
        except:  # noqa: E722 - bare except preserved verbatim from the original script
            pass

        if self.undolog:
            expHist(hpdf_bkg)

        channelname_bkg = channelname + "_bkgonly"

        h_postfit_bkg = ROOT.TH1D("postfit", "postfit", nBins, array.array("d", binEdges))
        h_postfit_bkg.SetDirectory(0)

        for ibin in range(1, nBins + 1):
            h_postfit_bkg.SetBinContent(ibin, hpdf_bkg.GetBinContent(ibin))
            h_postfit_bkg.SetBinError(ibin, 0)

        self.channel_hdata[channelname_bkg] = self.h_data.Rebin(
            nBins, "h_data_crop", array.array("d", binEdges)
        )
        self.channel_hdata[channelname_bkg].SetDirectory(0)
        # if a mask was used we need to normalize the postfit correctly
        #                if self.maskmin > -1 or self.maskmax > -1:
        #                    h_postfit_bkg = self.normalizePostFit(h_postfit_bkg, self.channel_hdata[channelname_bkg])  # noqa: E501
        self.channel_hpostfit[channelname_bkg] = h_postfit_bkg

        getChi2(extractor=self, channelname=channelname_bkg, npars=npars, useSumW2=self.useSumW2)

        return channelname_bkg

    def _apply_external_rebinning(self, channelname, channelname_bkg, npars):
        if not (self.rebinfile and self.rebinhist):
            return

        h_postfit = self.channel_hpostfit[channelname]

        f_rebin = ROOT.TFile(self.rebinfile, "READ")
        h_rebin = f_rebin.Get(self.rebinhist)

        binEdges = []
        nBins = h_rebin.GetNbinsX()
        for i in range(1, nBins + 2):
            edge = h_rebin.GetBinLowEdge(i)
            if edge < h_postfit.GetBinLowEdge(1) or edge > h_postfit.GetBinLowEdge(
                h_postfit.GetNbinsX() + 2
            ):
                continue
            binEdges.append(edge)

        f_rebin.Close()

        rebinnedchannelname = channelname + "_rebinned"
        self.channel_hpostfit[rebinnedchannelname] = self.channel_hpostfit[channelname].Rebin(
            len(binEdges) - 1, "postfit", array.array("d", binEdges)
        )
        self.channel_hdata[rebinnedchannelname] = self.channel_hdata[channelname].Rebin(
            len(binEdges) - 1, self.datahist, array.array("d", binEdges)
        )
        self.datafirstbin = self.channel_hdata[rebinnedchannelname].FindBin(self.datafirstbin) - 1

        getChi2(
            extractor=self, channelname=rebinnedchannelname, npars=npars, useSumW2=self.useSumW2
        )

        if self.bkgonly and channelname_bkg is not None:
            rebinnedchannelname_bkg = channelname_bkg + "_rebinned"
            self.channel_hpostfit[rebinnedchannelname_bkg] = self.channel_hpostfit[
                channelname_bkg
            ].Rebin(len(binEdges) - 1, "postfit", array.array("d", binEdges))
            self.channel_hdata[rebinnedchannelname_bkg] = self.channel_hdata[channelname_bkg].Rebin(
                len(binEdges) - 1, self.datahist, array.array("d", binEdges)
            )
            self.datafirstbin = (
                self.channel_hdata[rebinnedchannelname_bkg].FindBin(self.datafirstbin) - 1
            )

            getChi2(
                extractor=self,
                channelname=rebinnedchannelname_bkg,
                npars=npars,
                useSumW2=self.useSumW2,
            )

    def Extract(self):
        f, fd, w, pdf, cat, data, dataList, nChan = self._open_workspace_and_data()

        for i in range(nChan):
            datai = dataList.At(i)
            channelname = cat.getLabel()
            pdfi = pdf.getPdf(channelname)
            x = pdfi.getObservables(datai).first()
            npars = getNPars(pdfi, x, exclSyst=True)
            if self.externalnpars is not None:
                npars = self.externalnpars

            nBins, binEdges, hpdf = self._build_channel_postfit_histogram(
                pdfi, x, channelname, npars, data
            )

            if self.bkgonly:
                channelname_bkg = self._build_bkgonly_variant(
                    w, channelname, x, hpdf, nBins, binEdges, npars
                )
            else:
                channelname_bkg = None

            self._apply_external_rebinning(channelname, channelname_bkg, npars)

        fd.Close()
        f.Close()

    def WriteRoot(self, outfile, dirPerCategory=False):
        if not self.h_data:
            self.Extract()

        fout = ROOT.TFile(outfile, "RECREATE")

        if dirPerCategory:
            for channelname in self.channel_chi2:
                d = fout.mkdir(channelname)
                d.cd()

                self.channel_hdata[channelname].Write("data")
                self.channel_hpostfit[channelname].Write("postfit")
                self.channel_hresiduals[channelname].Write("residuals")
                self.channel_hchi2[channelname].Write("chi2")
        else:
            # just take first (and hopefully only) channel
            #
            # Chunk 16a fix (doc/TIER3_COMPLETION_PLAN.md /
            # doc/ACTIVITY_LOG.md): `.values()[-1]` was Python-2-only
            # dict-values indexing - a real TypeError under Python 3.
            # `list(...)[-1]` is the Python-3-correct equivalent,
            # selecting the same "last" channel this branch's own
            # comment and the dirPerCategory=True branch's channel
            # iteration both already treat as this method's one
            # long-standing convention - not changed to "first" despite
            # the comment above, per the original code's own indexing.
            self.h_data.Write("data")
            list(self.channel_hpostfit.values())[-1].Write("postfit")
            list(self.channel_hresiduals.values())[-1].Write("residuals")
            # self.channel_hresiduals.values()[-1].Write("postFitSigma")
            list(self.channel_hchi2.values())[-1].Write("chi2")

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
    parser = argparse.ArgumentParser(description="%prog [options]")
    parser.add_argument(
        "--datafile",
        dest="datafile",
        type=str,
        default="../Input/data/dijetTLAnlo/data_J75yStar03_range400_2079.root",
        help="original data file name (to get binning from)",
    )
    parser.add_argument(
        "--datahist",
        dest="datahist",
        type=str,
        default="data",
        help="original data hist name (to get binning from)",
    )
    parser.add_argument(
        "--datafirstbin",
        dest="datafirstbin",
        type=int,
        default=0,
        help="First bin in data histogram considered in fit. 0 for first non-underflow bin",
    )
    parser.add_argument("--wsfile", dest="wsfile", type=str, help="Workspace file name")
    parser.add_argument(
        "--wsname", dest="wsname", type=str, default="combWS", help="Name of workspace"
    )
    parser.add_argument(
        "--modelname",
        dest="modelname",
        type=str,
        default="ModelConfig",
        help="Name of model in workspace",
    )
    parser.add_argument("--outfile", dest="outfile", type=str, default="", help="Output file name")
    parser.add_argument(
        "--rebinfile",
        dest="rebinfile",
        type=str,
        help="Specify if rebinning to different template wanted",
    )
    parser.add_argument(
        "--rebinhist",
        dest="rebinhist",
        type=str,
        help="Specify if rebinning to different template wanted",
    )
    parser.add_argument(
        "--externalnpars",
        dest="externalnpars",
        default=None,
        type=float,
        help="Number of effective parameters for chi2 calculation",
    )
    parser.add_argument(
        "--maskmin",
        dest="maskmin",
        type=int,
        default=-1,
        help="Masked range to exclude from chi2 calculation",
    )
    parser.add_argument(
        "--maskmax",
        dest="maskmax",
        type=int,
        default=-1,
        help="Masked range to exclude from chi2 calculation",
    )
    parser.add_argument(
        "--dirpercategory",
        dest="dirpercategory",
        action="store_true",
        help="Create one output directory per channel (also for rebinning)",
    )
    parser.add_argument(
        "--bkgonly",
        dest="bkgonly",
        action="store_true",
        help="Add directory for bkg-only postfit. Needs --dirpercategory set.",
    )
    parser.add_argument(
        "--undolog",
        dest="undolog",
        action="store_true",
        help="Perform exp(N) on all data and fit histograms if log(N) was used for fitting.",
    )
    parser.add_argument(
        "--maskisbinnumber",
        dest="maskisbinnumber",
        action="store_true",
        help=(
            "Interprete maskmin and maskmax as bin numbers instead of values on the x-axis of "
            "the datahist. (Necessary for hacked NLOFit bins)"
        ),
    )
    parser.add_argument(
        "--useSumW2",
        dest="useSumW2",
        action="store_true",
        help="Use data histogram errors instead of sqrt(N_fit) for the residual calculation.",
    )

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
        useSumW2=args.useSumW2,
    )
    pfe.Extract()
    pfe.WriteRoot(args.outfile, args.dirpercategory)

    print("Finished ExtractPostfitFromWS")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
