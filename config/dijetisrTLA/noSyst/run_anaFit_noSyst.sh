#!/bin/bash

{
    # . scripts/setup_buildAndFit.sh

    doPseudodata=0
    # for pars in five six seven
    for pars in four
    do
	    folder=run/PreliminaryLimits_noSyst
	    signalfile=config/dijetisrTLA/signal/signal_dijetisr_zprime_parameterized_noSyst.template
	    backgroundfile=config/dijetisrTLA/background_dijetisrTLA_${pars}Par.template
	    categoryfile=config/dijetisrTLA/category_dijetisrTLA_noSyst.template
	    topfile=config/dijetisrTLA/dijetisrTLA_noSyst.template
	    
	    wsfile=${folder}/dijetisrTLA_combWS_${pars}Par.root
	    sigmean=250
	    sigwidth=-1 # dummy value. Real value taken from CB json sysfile
	    dosignal=1
	    dolimit=1
	    outputfile=${folder}/FitResult_anaFit_Zprime_${pars}Par.root
	    sysfile=config/dijetisrTLA/signalUncertainty_interpolated_${sigmean}.json
	    rangelow=130
	    rangehigh=1000

	    datafile=/afs/cern.ch/work/a/agekow/tlarun3/tla-ntuple-analysis-updated/new_outputs/data23_histos.root


	    datahist=mjj
            # datahist="pseudodata_50"
	    nbkg="dummy" #overwritten by prefit
	    maskthreshold=0.01
	    doprefit=1

	    flags=""
	    if (( $dosignal )); then flags="$flags --dosignal"; fi
	    if (( $dolimit )); then flags="$flags --dolimit"; fi
	    if (( $doprefit )); then flags="$flags --doprefit"; fi

	    # ./python/run_anaFit.py \
		./python/run_anaFit_updated.py \
    		--datafile $datafile \
    		--datahist $datahist \
    		--backgroundfile $backgroundfile \
    		--signalfile $signalfile \
    		--categoryfile $categoryfile \
    		--topfile $topfile \
    		--wsfile $wsfile \
    		--sigmean $sigmean \
    		--sigwidth $sigwidth \
    		--nbkg $nbkg \
    		--rangelow $rangelow \
    		--rangehigh $rangehigh \
    		--outputfile $outputfile \
			--maskthreshold $maskthreshold \
			--folder $folder \
			--sysfile $sysfile \
			$flags

		if [ "$doPseudodata" -eq 1 ]
		then
		toys=100
		scalefactor=$( bc <<< 'scale=2; 27.5' )

		echo python python/generatePseudoData.py --infile ${outputfile/FitResult/PostFit} --inhist Run3TLA/postfit --outhist pseudodata --outfile ${folder}/Run3_TLA${rangelow}_${rangehigh}_${pars}Par_finebinned_scale${scalefactor}.root --nreplicas $toys --scaling $scalefactor

		python python/generatePseudoData.py --infile ${outputfile/FitResult/PostFit} --inhist Run3TLA/postfit --outhist pseudodata --outfile ${folder}/Run3_TLA${rangelow}_${rangehigh}_${pars}Par_finebinned_scale${scalefactor}.root --nreplicas $toys --scaling $scalefactor
		fi
    done
}
