#!/bin/bash

FILES="Input/model/dijetTLAnlo/HistFactoryInput/templates2021/bkg/dijet_HTystar_00_06_R04_P2_ScaleMjj_standTheoryUncert_rebin4_LO_ABMP16_5_nnlo_reducedNPs_DataIsJ100_reweightedData_reweightedNLO.root
Input/model/dijetTLAnlo/HistFactoryInput/templates2021/bkg/dijet_HTystar_00_06_R04_P2_ScaleMjj_standTheoryUncert_rebin4_LO_ABMP16_5_nnlo_reducedNPs_DataIsJ100_scaledOnly_reweightedNLO.root
Input/model/dijetTLAnlo/HistFactoryInput/templates2021/bkg/dijet_HTystar_00_06_R04_P2_ScaleMjj_standTheoryUncert_rebin4_LO_CT14nnlo_reducedNPs_DataIsJ100_reweightedData_reweightedNLO.root
Input/model/dijetTLAnlo/HistFactoryInput/templates2021/bkg/dijet_HTystar_00_06_R04_P2_ScaleMjj_standTheoryUncert_rebin4_LO_CT14nnlo_reducedNPs_DataIsJ100_scaledOnly_reweightedNLO.root
Input/model/dijetTLAnlo/HistFactoryInput/templates2021/bkg/dijet_HTystar_00_06_R04_P2_ScaleMjj_standTheoryUncert_rebin4_LO_JR14NLO08VF_reducedNPs_DataIsJ100_reweightedData_reweightedNLO.root
Input/model/dijetTLAnlo/HistFactoryInput/templates2021/bkg/dijet_HTystar_00_06_R04_P2_ScaleMjj_standTheoryUncert_rebin4_LO_JR14NLO08VF_reducedNPs_DataIsJ100_scaledOnly_reweightedNLO.root
Input/model/dijetTLAnlo/HistFactoryInput/templates2021/bkg/dijet_HTystar_00_06_R04_P2_ScaleMjj_standTheoryUncert_rebin4_LO_MMHT2014nlo68clas118_reducedNPs_DataIsJ100_reweightedData_reweightedNLO.root
Input/model/dijetTLAnlo/HistFactoryInput/templates2021/bkg/dijet_HTystar_00_06_R04_P2_ScaleMjj_standTheoryUncert_rebin4_LO_MMHT2014nlo68clas118_reducedNPs_DataIsJ100_scaledOnly_reweightedNLO.root"

FILES=( $FILES )

rangeMin=171
rangeMax=3217

for FILE in "${FILES[@]}"
do
    echo $FILE

    tmpfile=$FILE
    
    echo python python/PrepareTemplates/cutHistRange.py --rangeMin $rangeMin --rangeMax $rangeMax $tmpfile 
    python python/PrepareTemplates/cutHistRange.py --rangeMin $rangeMin --rangeMax $rangeMax $tmpfile 
    tmpfile=${tmpfile/.root/_range${rangeMin}_${rangeMax}.root}

    echo python python/PrepareTemplates/unifyBinning.py $tmpfile
    python python/PrepareTemplates/unifyBinning.py $tmpfile
    tmpfile=${tmpfile/.root/_fixedBins.root}
    
    echo python python/PrepareTemplates/normalizeUnity.py $tmpfile
    python python/PrepareTemplates/normalizeUnity.py $tmpfile
    tmpfile=${tmpfile/.root/_normalized.root}

    if [[ $tmpfile == *"ABMP16"* ]]
    then
	echo python python/PrepareTemplates/makeUpDown.py $tmpfile
	python python/PrepareTemplates/makeUpDown.py $tmpfile
	tmpfile=${tmpfile/.root/_upDown.root}
    fi
    
done
