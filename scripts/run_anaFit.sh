#!/bin/bash

{
    . scripts/setup_buildAndFit.sh

    # for pars in five six seven
    for pars in four five six seven eight #six #four five seven 
    do
          
            #rangelow=80 # using systematics !!!
            #rangelow=80
	    rangelow=120
	    #rangelow=200
	    #rangelow=300
	    
	    rangehigh=1000
	    #rangehigh=200

	    #folder=/eos/user/l/lbazzano/TLA/FreqFrameOutputs/minimumStudy/120_run_${pars}Par
	    folder=/eos/user/l/lbazzano/TLA/FreqFrameOutputs_noisocut/run_${rangelow}_${rangehigh}_${pars}Par
	    #folder=/eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_systematics_80_1000_${pars}Par # using systematics !!!

	    signalfile=config/dijetisrTLA/signal/signal_dijetisrTLA.template
	    #signalfile=config/dijetisrTLA/signal/signal_dijetisrTLA_zprime_parametrized.template # using systematics !!!

	    backgroundfile=config/dijetisrTLA/background_dijetisrTLA_${pars}Par.template
	    
            categoryfile=config/dijetisrTLA/category_dijetisrTLA.template
	    #categoryfile=config/dijetisrTLA/category_dijetisrTLA_zprime_parametrized.template # using systematics !!!
	    
	    topfile=config/dijetisrTLA/dijetisrTLA.template
	    wsfile=${folder}/dijetisrTLA_combWS_${pars}Par.root
	    sigmean=400
	    sigwidth=10
	    dosignal=0 # turn this off for bkg only!!!!!!!!!!!!!!!!!!!!!
	    dolimit=0

	    # outputfile=${folder}/FitResult_anaFit_${pars}Par_mean${sigmean}_width${sigwidth}.root
            outputfile=${folder}/FitResult_anaFit_${pars}Par_bkgOnly.root
	    
	    #sysfile=/eos/user/l/lbazzano/TLA/dijet-isr-tla-ntuple-analysis/dir/signalUncertainty_interpolated.json # using systematics !!!
	    #sysfile=/eos/user/l/lbazzano/TLA/dijet-isr-tla-ntuple-analysis/MGPy8EG_S1_qqa_Ph25_mRp400_gASp1_qContentUDSC/signalUncertainty_interpolated.json # using systematics !!!
	    

	    #datafile=/eos/user/l/lbazzano/TLA/FreqFrameTestBranch/FrequentistFramework/alexFile/outputHistograms.root
	    #datafile=/afs/cern.ch/user/l/lbazzano/public/data22_allcuts_histos.root # recent mjj with isolation cuts
	    
	    #datafile=/afs/cern.ch/user/l/lbazzano/public/data22_histos.root # (0.445 /fb) recent mjj without isolation cuts
	    #datafile=/eos/user/l/lbazzano/TLA/FreqFrameTestBranch/FrequentistFramework/alexFile/new/data23_allCutsOpt_histos.root # (0.927/fb) tentative isolation cuts applied
	    
            #datafile=/eos/user/l/lbazzano/TLA/FreqFrameTestBranch/FrequentistFramework/alexFile/new/mjj_00451866.root # going down to 50 GeV
	    #datahist=mjj_50
	    
	    #datafile=/eos/user/l/lbazzano/TLA/FreqFrameTestBranch/FrequentistFramework/alexFile/new/data23_optimizedCuts_histos.root # eta 2.1 cut

	    #datafile=/eos/user/l/lbazzano/TLA/FreqFrameTestBranch/FrequentistFramework/alexFile/mc_clean/data23_mjj100_histos.root # feb 2025

            #datafile=/eos/user/l/lbazzano/TLA/FreqFrameTestBranch/FrequentistFramework/alexFile/calib_etacut_mcclean_isocut/data23_calib_eta2p1_EMFrac0p9_histos.root # mar 2025
            datafile=/eos/user/l/lbazzano/TLA/FreqFrameTestBranch/FrequentistFramework/alexFile/calib_etacut_mcclean/data23_calib_eta2p1_histos.root # mar 2025

	    #datafile=/eos/user/l/lbazzano/TLA/hists/onlineoffline/user.lbazzano.data22_13p6TeV.440447.J2_TLA_g35_trigger_08_08_23/mjj_histograms.root
	    #Input/data/dijetisrTLA/outputHistograms.root
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
		#--sysfile $sysfile \

                #nsig=args.nsig,
                #dosignal=args.dosignal,
                #dolimit=args.dolimit,

		toys=100
		scalefactor=$( bc <<< 'scale=2; 30/1.015' )
		echo python python/generatePseudoData.py --infile ${outputfile/FitResult/PostFit} --inhist Run3TLA/postfit --outhist pseudodata --outfile ${folder}/Run3_TLA${rangelow}_${rangehigh}_${pars}Par_finebinned_scale${scalefactor}.root --nreplicas $toys --scaling $scalefactor

		python python/generatePseudoData.py --infile ${outputfile/FitResult/PostFit} --inhist Run3TLA/postfit --outhist pseudodata --outfile ${folder}/Run3_TLA${rangelow}_${rangehigh}_${pars}Par_finebinned_scale${scalefactor}.root --nreplicas $toys --scaling $scalefactor

    done
}
