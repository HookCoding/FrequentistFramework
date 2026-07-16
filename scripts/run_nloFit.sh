#!/bin/bash

{
    . scripts/setup_buildCombineFit.sh

    # for constr in 1 2 5 10 20
    for constr in 5
    do
	# for trig in J50Comb J100
	for trig in J100
	do
	    
	    folder=run/outOfTheBoxFit
	    modelfile=Input/model/dijetTLAnlo/templates2021/LO_CT14nnlo_reducedNPs_scaledOnly_reweightedNLO/HistFactory_dijetTLAnlo_J100yStar06_bkg_ws.root
	    bkgfile=config/dijetTLAnlo/templates2021/background_dijetTLAnlo_J100yStar06_CT14nnlo.template
	    sigfile=config/dijetTLAnlo/templates2021/signal/signal_dijetTLAnlo_J100yStar06.template
	    categoryfile=config/dijetTLAnlo/templates2021/category_dijetTLAnlo_J100yStar06.template
	    topfile=config/dijetTLAnlo/templates2021/dijetTLAnlo_J100yStar06.template
	    combinefile=config/dijetTLAnlo/Inflation_CT14.template
	    wsfile=${folder}/dijetTLAnlo_combWS_nloFit.root
	    sigmean=1000
	    sigwidth=7
	    rangelow=457
	    rangehigh=2997
	    signalmodelfile=Input/model/dijetTLAnlo/templates2021/signal/HistFactory_dijetTLAnlo_J100yStar06_sig_mean${sigmean}_width${sigwidth}_ws.root
	    outputfile=${folder}/FitResult_nloFit_${trig}yStar06_templates2021_CT14nnlo_scaledOnly_constr${constr}_mean${sigmean}_width${sigwidth}.root

	    externalchi2fct=fit
	    externalchi2file=Input/model/dijetTLAnlo/templates2021/LO_CT14nnlo_reducedNPs_scaledOnly_reweightedNLO/chi2/chi2_range_457_2997_J100_constr${constr}.root
	    externalchi2bins=58
	    if [[ $trig =~ "J50" || $trig =~ "J40" ]]
	    then
		externalchi2file=Input/model/dijetTLAnlo/templates2021/LO_CT14nnlo_reducedNPs_scaledOnly_reweightedNLO/chi2/chi2_range_302_1516_J50Comb_constr${constr}.root
		externalchi2bins=39
	    fi

	    datafile=Input/data/dijetTLAnlo/binning2021/unblinding1_mjj_spectra_range171_3217_fixedBins.root
	    datahist=L1${trig}/Mjj_TLA2022binning
	    nbkg="2E8,0,3E8"
	    maskthreshold=0.01
	    doinitialpars=1
	    dosignal=1
	    dolimit=1
	    doprefit=1

	    flags=""
	    if (( $doinitialpars )); then flags="$flags --doinitialpars"; fi
	    if (( $dosignal )); then flags="$flags --dosignal"; fi
	    if (( $dolimit )); then flags="$flags --dolimit"; fi
	    if (( $doprefit )); then flags="$flags --doprefit"; fi
	    
	    ./python/run_nloFit.py \
    		--datafile $datafile \
    		--datahist $datahist \
    		--modelfile $modelfile \
    		--signalmodelfile $signalmodelfile \
    		--bkgfile $bkgfile \
    		--sigfile $sigfile \
    		--categoryfile $categoryfile \
    		--topfile $topfile \
    		--combinefile $combinefile \
    		--wsfile $wsfile \
    		--sigmean $sigmean \
    		--sigwidth $sigwidth \
    		--nbkg $nbkg \
    		--rangelow $rangelow \
    		--rangehigh $rangehigh \
    		--outputfile $outputfile \
		--constr $constr \
		--externalchi2file $externalchi2file \
		--externalchi2fct $externalchi2fct \
		--externalchi2bins $externalchi2bins \
		--maskthreshold $maskthreshold \
		--folder $folder \
		$flags
	done
    done
}
