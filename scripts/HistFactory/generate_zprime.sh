#!/bin/bash

#  Mass grid defined as in morphing:
mR=( 200 250 300 350 400 450 500 550 600 650 700 750 800 850 900 950 1000 1050 1100 1150 1200 1250 1300 1350 1400 1450 1500 1550 1600 1650 1700 1750 1800 1850 1900 1950 2000 )

FILE_TEMPLATES="Input/model/dijetTLA/zprime/HLT_j0_perf_ds1_L1J100/SignalTemplates_th1s_gq0p1.root"

##### Cut histograms in FILE_TEMPLATES in the analysis range:
# (Not needed in the end):

#rangeMin=531
#rangeMax=2079

#echo "Cutting signal histograms in analysis range"

# python python/PrepareTemplates/cutHistRange.py --rangeMin $rangeMin --rangeMax $rangeMax $FILE_TEMPLATES
#FILE_TEMPLATES=${FILE_TEMPLATES/.root/_range${rangeMin}_${rangeMax}.root}

##### Inject ghosts 

echo "Injecting ghosts"
OUT_FILE=${FILE_TEMPLATES/.root/_wGhosts.root}
echo python python/PrepareTemplates/injectGhosts.py --infile ${FILE_TEMPLATES} --output ${OUT_FILE}
python python/PrepareTemplates/injectGhosts.py --infile ${FILE_TEMPLATES} --output ${OUT_FILE}
FILE_TEMPLATES=${OUT_FILE}

##### BUILD HistFactory

for mass in ${mR[@]}
do
  echo "Processing mass point $mass"
  OUT_FILE="Input/model/dijetTLA/zprime/HLT_j0_perf_ds1_L1J100/HistFactory_dijetTLA_J100yStar06_zprime_gq0p1_mR${mass}.root"
  echo python/PrepareTemplates/dijetTLA_genZprime.py --infile ${FILE_TEMPLATES} --mass ${mass} --outfile ${OUT_FILE}
  python python/PrepareTemplates/dijetTLA_genZprime.py --infile ${FILE_TEMPLATES} --mass ${mass} --outfile ${OUT_FILE}
done
