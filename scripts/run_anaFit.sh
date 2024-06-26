#!/bin/bash

{
    . scripts/setup_buildAndFit.sh

    # for pars in five six seven
    for pars in five
    do
	# for trig in J50Comb J100
	    folder=run
	    signalfile=config/dijetisrTLA/signal/signal_dijetisrTLA.template
	    backgroundfile=config/dijetisrTLA/background_dijetisrTLA_${pars}Par.template
	    categoryfile=config/dijetisrTLA/category_dijetisrTLA.template
	    topfile=config/dijetisrTLA/dijetisrTLA.template
	    wsfile=${folder}/dijetisrTLA_combWS_${pars}Par.root
	    sigmean=200
	    sigwidth=10
	    dosignal=0
	    dolimit=0
	    # outputfile=${folder}/FitResult_anaFit_${pars}Par_mean${sigmean}_width${sigwidth}.root
		outputfile=${folder}/FitResult_anaFit_${pars}Par_bkgOnly.root
	    rangelow=150
	    rangehigh=1000
	    datafile=Input/data/dijetisrTLA/outputHistograms.root
		# datafile=run/postfit.root
	    datahist=mjj
	    nbkg="dummy" #overwritten by prefit
	    maskthreshold=0.01
	    doprefit=1

	    flags=""
	    if (( $dosignal )); then flags="$flags --dosignal"; fi
	    if (( $dolimit )); then flags="$flags --dolimit"; fi
	    if (( $doprefit )); then flags="$flags --doprefit"; fi

	    ./python/run_anaFit.py \
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
		$flags

		toys=100
		scalefactor=$( bc <<< 'scale=2; 30/1.015' )
		echo python python/generatePseudoData.py --infile ${outputfile/FitResult/PostFit} --inhist Run3TLA/postfit --outhist pseudodata --outfile ${folder}/Run3_TLA${rangelow}_${rangehigh}_${pars}Par_finebinned_scale${scalefactor}.root --nreplicas $toys --scaling $scalefactor

		python python/generatePseudoData.py --infile ${outputfile/FitResult/PostFit} --inhist Run3TLA/postfit --outhist pseudodata --outfile ${folder}/Run3_TLA${rangelow}_${rangehigh}_${pars}Par_finebinned_scale${scalefactor}.root --nreplicas $toys --scaling $scalefactor

    done
}
