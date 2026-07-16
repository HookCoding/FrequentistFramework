import ROOT, sys


def getHistogram(datafilename ,datahistname ):

    datafile = ROOT.TFile(datafilename,"READ")
    datahist = datafile.Get(datahistname)
    datahist.SetDirectory(0)
    #datahist.Scale(1, "width")
    datahist.Sumw2(ROOT.kTRUE);
    datafile.Close()
    return datahist

def setGausSignal(w, mZ, width = 0.07):
    # fit parameters
    w.factory("mZ[{0}]".format(mZ)) 
    w.var("mZ").setConstant(True)
    w.factory("prod::width(mZ,{0})".format(width))
    #w.factory("EXPR::signal('TMath::Gaus(@0, @1, @2, true)',{mass,mZ, width })")
    w.factory("RooGaussian::signal(mass,mZ, width)")

def setBkfFunc_UA2(w):
    # fit parameters
    '''w.factory("p1[0.1, -100, 100]") 
    w.factory("p2[4.5, -100, 10]") 
    w.factory("p3[21, -100, 100]") 
    w.factory("p4[-28, -300, 300]") '''
    w.factory("p1[0.129905, -0.5, 1.5]") 
    w.factory("p2[4.51084, -10, 10]") 
    w.factory("p3[23.4939, -30, 30]")  
    w.factory("p4[-36.767, -40, 10]") 
    # background function
    w.factory("EXPR::background('@1*TMath::Power(@0/13000.,-1*@2)*TMath::Exp( -1*(@3*@0/13000. + @4*TMath::Power(@0/13000.,2)))',{mass,p1,p2,p3,p4})")

def setBkfFunc_4param(w):
    # fit parameters
    w.factory("p1[0.25, -100, 100]") 
    w.factory("p2[9.15, -200, 200]") 
    w.factory("p3[-22.829, -200, 200]") 
    w.factory("p4[-6.9, -100, 100]") 
    # background function
    w.factory("EXPR::background('@1*TMath::Power(1-@0/13000.,1*@2)*1/TMath::Power( @0/13000., @3 + @4*TMath::Log(@0/13000.))',{mass,p1,p2,p3,p4})")


def makePlot(frame, frame2, frame3, datahist):
    c = ROOT.TCanvas("c1","c1",600,600)
    pad1 = ROOT.TPad("pad1", "pad1", 0, 0.5, 1, 1.0)
    pad1.SetBottomMargin(0) #Upper and lower plot are joined
    pad1.Draw()

    pad1.cd()
    #pad1.SetLeftMargin(0.15)
    #frame.GetYaxis().SetTitleOffset(1.6)
    frame.Draw()
    pad1.SetLogy()

    c.cd()
    pad2 = ROOT.TPad("pad2", "pad2", 0, 0.3, 1, 0.5);
    pad2.SetTopMargin(0);
    pad2.SetBottomMargin(0.0)
    #pad2.SetLeftMargin(0.15)
    pad2.Draw()
    pad2.cd()
    #frame2.GetYaxis().SetTitleOffset(1.6)
    frame2.GetYaxis().SetTitle("Residual Distribution")
    frame2.GetYaxis().SetLabelSize(0.1)
    frame2.GetYaxis().SetTitleOffset(0.3)
    frame2.GetYaxis().SetTitleSize(0.1)
    frame2.Draw()

    c.cd()
    pad3 = ROOT.TPad("pad3", "pad3", 0, 0.1, 1, 0.3);
    pad3.SetTopMargin(0);
    pad3.SetBottomMargin(0.1)
    #pad3.SetLeftMargin(0.15)
    pad3.Draw()
    pad3.cd()
    #pad3.SetLeftMargin(0.15)
    frame3.GetYaxis().SetTitleOffset(0.3)
    frame3.GetYaxis().SetTitle("Pull Distribution")
    frame3.GetXaxis().SetTitle("Mass [GeV]")
    frame3.GetXaxis().SetLabelSize(0.1)
    frame3.GetXaxis().SetTitleSize(0.1)
    frame3.GetYaxis().SetLabelSize(0.1)
    frame3.GetYaxis().SetTitleSize(0.1)
    frame3.Draw()

    raw_input("Press Enter...")


if __name__ == '__main__':

    # Construct model
    w = ROOT.RooWorkspace("w")

    #### Set input data & fit range ####
    #observable mass with fit range

    inputfilename = "../Input/data/dijetTLA/lookInsideTheBoxWithUniformMjj.root"
    #inputhistname = "PseudoData_BG_InjectedSignal_500000_99"
    inputhistname = "Nominal/DSJ100yStar06_TriggerJets_J100_yStar06_mjj_finebinned_all_data"


    #For the 1400 GeV mass point we fit bins 22 through 40 which corresponds to a mass range of 927-1998 GeV.
    #for the 800 GeV Z' mass, we fit from bins 9  to 27 in our spectrum, which corresponds to a mass range of 531 GeV to 1186 GeV.

    w.factory("mass[ 531,1186]")
    datahist = getHistogram(inputfilename, inputhistname)
    w.var("mass").setBins(1186-531);
    
    dataevts= datahist.Integral(531,1186)
    nsiginject = 100000
    mytitle = "J100 Pseudodata, Nsig_injected = {0}, fit range = [ 531,1186]".format(nsiginject)

    #### Set up bkg function ###########
    #setBkfFunc_UA2(w)
    setBkfFunc_UA2(w)

    #### Set up signal function ########
    setGausSignal(w,800, 0.07) 
    sigNorm =  w.pdf("signal").getVal( ROOT.RooArgSet(w.var("mass")))
    print "Initial signal normalization = ", sigNorm


    ####################################
    ##### Set up final model to fit
    
    w.factory("SUM::model(nsig[0.0,0.0,{0}]*signal, nbkg[{0},0,{0}*2]*background)".format(dataevts));

    ####################################

    #### Bookkeeping & setup ########
    ROOT.SetOwnership(datahist,False)

    # put histogram into RooDataHist object
    data = ROOT.RooDataHist("data","data",ROOT.RooArgList(w.var('mass')),datahist);
    # for memory management
    ROOT.SetOwnership(data,False)
    # workaround to call import function (import is a protected keyword in python)
    getattr(w,'import')(data, ROOT.RooFit.Rename("data"))


    #### Set up minimizer ########
    w.pdf("model").setAttribute("BinnedLikelihood", True);
    nll = w.pdf("model").createNLL(data)
    nll.enableOffsetting(True)
    minim = ROOT.RooMinimizer(nll);

    ####################################
    # do the first fit
    minim.minimize("Migrad")

    ###### Inject signal ########
    if nsiginject > 0:
    # set value of injected signal
        w.var("nsig").setVal(nsiginject) ;


        ######### Generate a dataset of 10000 events in mass from the model
        #pseudodata = w.pdf("model").generate(ROOT.RooArgSet(w.var("mass")),int(dataevts)) ; # too much data to use this implementation
        pseudodata = w.pdf("model").generateBinned(ROOT.RooArgSet(w.var("mass")),int(dataevts))

        w.var("nsig").setVal(0) ;

        ######### fit again to the data ########

        nllpd = w.pdf("model").createNLL(pseudodata)
        nllpd.enableOffsetting(True)
        minim = ROOT.RooMinimizer(nllpd);
        minim.minimize("Migrad")

    ######## initial plotting stuff ########
    # set up frame object


    frame = w.var('mass').frame(ROOT.RooFit.Title(mytitle)) ;

    modelcolor = ROOT.kAzure+1
    signalcolor = ROOT.kGreen-9
    if nsiginject > 0:
        pseudodata.plotOn(frame) ;
    else:
        w.data("data").plotOn(frame, ROOT.RooFit.LineColor(ROOT.kRed)) ;
    w.pdf("signal").plotOn(frame,ROOT.RooFit.LineColor(signalcolor)) ;
    w.pdf("background").plotOn(frame, ROOT.RooFit.LineColor(ROOT.kBlue)) ;
    w.pdf("model").plotOn(frame,ROOT.RooFit.LineColor(modelcolor)) ;
    w.pdf("model").paramOn(frame,ROOT.RooFit.Layout(0.65)) ;

    # Construct a histogram with the residuals of the data w.r.t. the curve
    hresid = frame.residHist() 
    hresid.SetLineColor(modelcolor)
    hresid.SetMarkerColor(modelcolor)

    # Construct a histogram with the pulls of the data w.r.t the curve
    hpull = frame.pullHist() 
    hpull.SetLineColor(modelcolor)
    hpull.SetMarkerColor(modelcolor)

    # Create a new frame to draw the residual distribution and add the distribution to the frame
    frame2 = w.var('mass').frame(ROOT.RooFit.Title("")) ;
    frame2.addPlotable(hresid) ;

    # Create a new frame to draw the pull distribution and add the distribution to the frame
    frame3 = w.var('mass').frame(ROOT.RooFit.Title("")) ;
    frame3.addPlotable(hpull) ;

    ######## Print any relevant info ########

    w.Print()

    nsig = w.var("nsig").getVal( ROOT.RooArgSet(w.var("mass")))
    nsigerr = w.var("nsig").getError() 

    print "Data events in fit range =", dataevts
    print "Bkg events = ", w.var("nbkg").getVal( ROOT.RooArgSet(w.var("mass")))
    print "Signal events = ", nsig
    print "Signal significance = ", nsig/w.var("nsig").getError()  
    print "Signal recovery is", 100 + (nsig - nsiginject)/nsiginject*100,"%"

    makePlot(frame, frame2, frame3, datahist)

    


