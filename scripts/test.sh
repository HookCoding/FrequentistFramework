par=seven
mjj=135
maskmin=232 #only for pfe
maskmax=271 #only for pfe

#None
xm=""
qf=""

#R22
xm=xmlAnaWSBuilder/build/bin/XMLReader
qf=quickFit/build/quickFit

#R21
#xm=xmlAnaWSBuilderR21/build/XMLReader
#qf=quickFitR21/build/quickFit

# native
$xm \
  -x /eos/home-t/tofitsch/tlafits/run_135_1000_${par}Par/dijetTLA_fromTemplate.xml \
  -o "logy integral" \
  --minimizerStrategy 0

$qf \
  --chi2fit 1 \
  --poissonerror 1 \
  -f /eos/home-t/tofitsch/tlafits/run_${mjj}_1000_${par}Par/dijetisrTLA_combWS_${par}Par.root \
  -d combData  \
  --checkWS 1 \
  --hesse 1 \
  --savefitresult 1 \
  --saveWS 1 \
  --saveNP 1 \
  --saveErrors 1 \
  --minStrat 2 \
  --nllOffset 0 \
  --optConst 2 \
  --GKIntegrator 1 \
  --minTolerance 1E-6 \
  -o /eos/home-t/tofitsch/tlafits/run_${mjj}_1000_${par}Par/FitResult_anaFit_${par}Par_bkgOnly.root \
  &> /eos/home-t/tofitsch/tlafits/run_${mjj}_1000_${par}Par/quickFitLog_anaFit_${par}Par_bkgOnly.log

python plot_edm.py \
  /eos/home-t/tofitsch/tlafits/run_${mjj}_1000_${par}Par/quickFitLog_anaFit_${par}Par_bkgOnly.log \
  /eos/home-t/tofitsch/tlafits/run_${mjj}_1000_${par}Par/edm_anaFit_${par}Par_bkgOnly.pdf

python python/pfe.py --params $par --firstbin $mjj --maskstr ""

# masked
$xm \
  -x /eos/home-t/tofitsch/tlafits/run_135_1000_${par}Par/dijetTLA_fromTemplate_masked.xml \
  -o "logy integral" \
  --minimizerStrategy 0

$qf \
  --chi2fit 1 \
  --poissonerror 1 \
  -f /eos/home-t/tofitsch/tlafits/run_${mjj}_1000_${par}Par/dijetisrTLA_combWS_${par}Par_masked.root \
  -d combData \
  --checkWS 1 \
  --hesse 1 \
  --savefitresult 1 \
  --saveWS 1 \
  --saveNP 1 \
  --saveErrors 1 \
  --minStrat 2 \
  --nllOffset 0 \
  --optConst 2 \
  --GKIntegrator 1 \
  --minTolerance 1E-6 \
  --range SBLo_Run3TLA,SBHi_Run3TLA \
  -o /eos/home-t/tofitsch/tlafits/run_${mjj}_1000_${par}Par/FitResult_anaFit_${par}Par_bkgOnly_masked.root \
  &> /eos/home-t/tofitsch/tlafits/run_${mjj}_1000_${par}Par/quickFitLog_anaFit_${par}Par_bkgOnly_masked.log

python plot_edm.py \
  /eos/home-t/tofitsch/tlafits/run_${mjj}_1000_${par}Par/quickFitLog_anaFit_${par}Par_bkgOnly_masked.log \
  /eos/home-t/tofitsch/tlafits/run_${mjj}_1000_${par}Par/edm_anaFit_${par}Par_bkgOnly_masked.pdf

python python/pfe.py --params $par --firstbin $mjj --maskstr "_masked" --maskmin $maskmin --maskmax $maskmax

root -l -q "plot_postfit.cpp(\"/eos/home-t/tofitsch/tlafits/run_${mjj}_1000_${par}Par\", \"${par}\")"

alert
