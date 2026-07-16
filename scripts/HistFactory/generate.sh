#!/bin/bash

SIGMEANS=( 350 375 400 425 450 500 550 600 650 700 750 800 850 900 950 1000 1050 1100 1150 1200 1300 1400 1500 1600 1700 1800 ) 
SIGWIDTHS=( 1 5 7 10 12 15 )

FILES_BKG="Input/model/dijetTLAnlo/HistFactoryInput/templates2021/bkg/dijet_HTystar_00_06_R04_P2_ScaleMjj_standTheoryUncert_rebin4_LO_ABMP16_5_nnlo_reducedNPs_DataIsJ100_reweightedData_reweightedNLO_range171_3217_fixedBins_normalized_upDown.root
Input/model/dijetTLAnlo/HistFactoryInput/templates2021/bkg/dijet_HTystar_00_06_R04_P2_ScaleMjj_standTheoryUncert_rebin4_LO_ABMP16_5_nnlo_reducedNPs_DataIsJ100_scaledOnly_reweightedNLO_range171_3217_fixedBins_normalized_upDown.root
Input/model/dijetTLAnlo/HistFactoryInput/templates2021/bkg/dijet_HTystar_00_06_R04_P2_ScaleMjj_standTheoryUncert_rebin4_LO_CT14nnlo_reducedNPs_DataIsJ100_reweightedData_reweightedNLO_range171_3217_fixedBins_normalized.root
Input/model/dijetTLAnlo/HistFactoryInput/templates2021/bkg/dijet_HTystar_00_06_R04_P2_ScaleMjj_standTheoryUncert_rebin4_LO_CT14nnlo_reducedNPs_DataIsJ100_scaledOnly_reweightedNLO_range171_3217_fixedBins_normalized.root
Input/model/dijetTLAnlo/HistFactoryInput/templates2021/bkg/dijet_HTystar_00_06_R04_P2_ScaleMjj_standTheoryUncert_rebin4_LO_JR14NLO08VF_reducedNPs_DataIsJ100_reweightedData_reweightedNLO_range171_3217_fixedBins_normalized.root
Input/model/dijetTLAnlo/HistFactoryInput/templates2021/bkg/dijet_HTystar_00_06_R04_P2_ScaleMjj_standTheoryUncert_rebin4_LO_JR14NLO08VF_reducedNPs_DataIsJ100_scaledOnly_reweightedNLO_range171_3217_fixedBins_normalized.root
Input/model/dijetTLAnlo/HistFactoryInput/templates2021/bkg/dijet_HTystar_00_06_R04_P2_ScaleMjj_standTheoryUncert_rebin4_LO_MMHT2014nlo68clas118_reducedNPs_DataIsJ100_reweightedData_reweightedNLO_range171_3217_fixedBins_normalized.root
Input/model/dijetTLAnlo/HistFactoryInput/templates2021/bkg/dijet_HTystar_00_06_R04_P2_ScaleMjj_standTheoryUncert_rebin4_LO_MMHT2014nlo68clas118_reducedNPs_DataIsJ100_scaledOnly_reweightedNLO_range171_3217_fixedBins_normalized.root"
FILES_BKG=( $FILES_BKG )

FILES_OUT="Input/model/dijetTLAnlo/templates2021/LO_ABMP16_5_nnlo_reducedNPs_reweightedData_reweightedNLO/HistFactory_dijetTLAnlo_J100yStar06_bkg_ws.root
Input/model/dijetTLAnlo/templates2021/LO_ABMP16_5_nnlo_reducedNPs_scaledOnly_reweightedNLO/HistFactory_dijetTLAnlo_J100yStar06_bkg_ws.root
Input/model/dijetTLAnlo/templates2021/LO_CT14nnlo_reducedNPs_reweightedData_reweightedNLO/HistFactory_dijetTLAnlo_J100yStar06_bkg_ws.root
Input/model/dijetTLAnlo/templates2021/LO_CT14nnlo_reducedNPs_scaledOnly_reweightedNLO/HistFactory_dijetTLAnlo_J100yStar06_bkg_ws.root
Input/model/dijetTLAnlo/templates2021/LO_JR14NLO08VF_reducedNPs_reweightedData_reweightedNLO/HistFactory_dijetTLAnlo_J100yStar06_bkg_ws.root
Input/model/dijetTLAnlo/templates2021/LO_JR14NLO08VF_reducedNPs_scaledOnly_reweightedNLO/HistFactory_dijetTLAnlo_J100yStar06_bkg_ws.root
Input/model/dijetTLAnlo/templates2021/LO_MMHT2014nlo68clas118_reducedNPs_reweightedData_reweightedNLO/HistFactory_dijetTLAnlo_J100yStar06_bkg_ws.root
Input/model/dijetTLAnlo/templates2021/LO_MMHT2014nlo68clas118_reducedNPs_scaledOnly_reweightedNLO/HistFactory_dijetTLAnlo_J100yStar06_bkg_ws.root"
FILES_OUT=( $FILES_OUT )

N=$((${#FILES_BKG[@]} - 1))
for i in $(seq 0 $N)
do
    FILE_BKG=${FILES_BKG[$i]}
    FILE_OUT=${FILES_OUT[$i]}
    echo python python/PrepareTemplates/dijetTLAnlo_genBkg.py --infile $FILE_BKG --outfile $FILE_OUT
    python python/PrepareTemplates/dijetTLAnlo_genBkg.py --infile $FILE_BKG --outfile $FILE_OUT
done

mkdir -p Input/model/dijetTLAnlo/HistFactoryInput/templates2021/signal
mkdir -p Input/model/dijetTLAnlo/templates2021/signal

for SIGMEAN in "${SIGMEANS[@]}"
do
    for SIGWIDTH in "${SIGWIDTHS[@]}"
    do
	TMPFILE="Input/model/dijetTLAnlo/HistFactoryInput/templates2021/signal/sigshape_J100yStar06_mean${SIGMEAN}_width${SIGWIDTH}_range171_3217.root"
	OUTFILE="Input/model/dijetTLAnlo/templates2021/signal/HistFactory_dijetTLAnlo_J100yStar06_sig_mean${SIGMEAN}_width${SIGWIDTH}_ws.root"

	python python/PrepareTemplates/createGaussHist.py --infile ${FILE_BKG//_fixedBins_normalized/} --histname "nominal" --sigMean ${SIGMEAN} --sigWidth ${SIGWIDTH} --injectGhost --outfile ${TMPFILE}
	python python/PrepareTemplates/unifyBinning.py ${TMPFILE}

	echo python python/PrepareTemplates/dijetTLAnlo_genSig.py --infile ${TMPFILE//.root/_fixedBins.root} --outfile ${OUTFILE}
	python python/PrepareTemplates/dijetTLAnlo_genSig.py --infile ${TMPFILE//.root/_fixedBins.root} --outfile ${OUTFILE}
    done
done
