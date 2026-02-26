# native
#quickFit \
#  --chi2fit 1 \
#  --poissonerror 1 \
#  -f /eos/home-t/tofitsch/tlafits/run_135_1000_tenPar/dijetisrTLA_combWS_tenPar.root \
#  -d combData  \
#  --checkWS 1 \
#  --hesse 1 \
#  --savefitresult 1 \
#  --saveWS 1 \
#  --saveNP 1 \
#  --saveErrors 1 \
#  --minStrat 2 \
#  --nllOffset 0 \
#  --optConst 2 \
#  --GKIntegrator 1 \
#  --minTolerance 1E-2 \
#  -o /eos/home-t/tofitsch/tlafits/run_135_1000_tenPar/FitResult_anaFit_tenPar_bkgOnly.root

## masked
quickFit \
  --chi2fit 1 \
  --poissonerror 1 \
  -f /eos/home-t/tofitsch/tlafits/run_135_1000_tenPar/dijetisrTLA_combWS_tenPar_masked.root \
  -d combData \
  --checkWS 1 \
  --hesse 1 \
  --savefitresult 1 \
  --saveWS 1 \
  --saveNP 1 \
  --saveErrors 1 \
  --minStrat 1 \
  --nllOffset 0 \
  --optConst 2 \
  --GKIntegrator 1 \
  --minTolerance 1E-6 \
  --range SBLo,SBHi \
  -o /eos/home-t/tofitsch/tlafits/run_135_1000_tenPar/FitResult_anaFit_tenPar_bkgOnly_masked.root

#root -l -q "plot_postfit.cpp(\"/eos/home-t/tofitsch/tlafits/run_135_1000_tenPar\", \"ten\")"
#root -l -q test.cpp
