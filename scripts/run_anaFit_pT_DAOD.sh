#!/bin/bash

generatePD=0

{
    . scripts/setup_buildAndFit.sh

    # for pars in four five six seven eight
    for pars in six
    do
	    folder=run/fitDAODs_
	    signalfile=config/dijetTLA/signal/signal_dijetTLA.template
	    backgroundfile=config/dijetTLA/background_dijetTLA_J100yStar06_${pars}Par.template
	    categoryfile=config/dijetTLA/category_dijetTLA.template
	    topfile=config/dijetTLA/dijetTLA_J100yStar06.template
	    wsfile=${folder}/dijetTLA_combWS_anaFit_${pars}Par_${trig}yStar06_bkgonly.root
	    sigmean=1000
	    sigwidth=5
	    dosignal=0
	    dolimit=0
	    doBH=0
	    doprefit=1
	    dochi2fit=0
	    dochi2constraints=1

	    maskthreshold=-1
	    outputfile=${folder}/FitResult_anaFit_${pars}Par_yStar06_bkgonly.root
	    rangelow=85
	    # rangelow=302
	    # rangelow=344
	    # rangehigh=1516
	    rangehigh=1516
	    nbkg="DUMMY"
	    # if [[ $trig == "J100" ]]
	    # then
	    # 	rangelow=481
	    # 	rangehigh=2997
	    # 	nbkg="DUMMY"
	    # fi
	    # datafile=Input/data/dijetTLA/mjj_spectra_fullRun2.root
	    # datafile=run/GSC_May2023_TLA_lead.root
	    # datafile=run/NTuples/NTuples_afterJES_${campaign}_hadded.root
	    # datafile=run/NTuples/NTuples_noResidual_${campaign}_hadded.root
	    datafile=/run/b2_all.root
	    datahist=scaled_hh_leadingReferencePt_weighted
	    flags=""
	    if (( $dosignal )); then flags="$flags --dosignal"; fi
	    if (( $dolimit )); then flags="$flags --dolimit"; fi
	    if (( $doBH )); then flags="$flags --doBH"; fi
	    if (( $doprefit )); then flags="$flags --doprefit"; fi
	    if (( $dochi2fit )); then flags="$flags --dochi2fit"; fi
	    if (( $dochi2constraints )); then flags="$flags --dochi2constraints"; fi

	    ./python/run_anaFit.py \
    	    	--datafile $datafile \
    	    	--datahist $datahist \
    	    	--signalfile $signalfile \
    	    	--backgroundfile $backgroundfile \
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

	    if (( $generatePD ))
	    then
		# if [[ $trig == "J40" ]]
		# then
		#     scalefactor=$( bc <<< 'scale=2; 3.3/0.342' )
		# fi
		# if [[ $trig == "J50" ]]
		# then
		#     scalefactor=$(  bc <<< 'scale=2; 5.77/0.548' )
		# fi
		# if [[ $trig == "J50Topo" ]]
		# then
		#     scalefactor=$( bc <<< 'scale=2; 9.22/1.01' )
		# fi
		# if [[ $trig == "J50Comb" ]]
		# then
		#     scalefactor=$( bc <<< 'scale=2; 14.5/1.484' )
		# fi
		# if [[ $trig == "J100" ]]
		# then
		#     scalefactor=$( bc <<< 'scale=2; 133.2/19.643' )
		#     # scalefactor=$( bc <<< 'scale=2; 133.2/9.822' )
		# fi

		scalefactor=1
		toys=1000


		postfitfile=${outputfile/FitResult/PostFit}
		postfitfilemasked=${postfitfile/.root/_masked.root}
		if [ -f "$postfitfilemasked" ]; then
		    echo "Using masked postfit file for PD generation: $postfitfilemasked"
		    postfitfile=$postfitfilemasked
		fi
		
		echo python python/generatePseudoData.py --infile $postfitfile --inhist J100yStar06/postfit --outhist pseudodata --outfile ${folder}/PD_Run2_GlobalFit_${rangelow}_${rangehigh}_${pars}Par_finebinned_${trig}_scale${scalefactor}.root --nreplicas $toys --scaling $scalefactor

		python python/generatePseudoData.py --infile $postfitfile --inhist J100yStar06/postfit --outhist pseudodata --outfile ${folder}/PD_Run2_GlobalFit_${rangelow}_${rangehigh}_${pars}Par_finebinned_${trig}_scale${scalefactor}.root --nreplicas $toys --scaling $scalefactor
	    fi
    done
}
