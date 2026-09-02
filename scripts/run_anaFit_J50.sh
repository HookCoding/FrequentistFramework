#!/bin/bash

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
out_dir="${ANAFIT_OUTPUT_DIR:-$repo_dir/run/fits}"
setup_script="${ANAFIT_SETUP_SCRIPT:-$repo_dir/scripts/setup_buildAndFit.sh}"
analysis_runner="${ANAFIT_RUNNER:-$repo_dir/python/run_anaFit.py}"

mkdir -p "$out_dir"
cd "$repo_dir"

{
    . "$setup_script"
    setup_status=$?
    if (( setup_status != 0 )); then
        echo "ERROR: scientific environment setup failed with exit code $setup_status" >&2
        exit "$setup_status"
    fi

    # Set FIT_PARS to a space-separated list such as "six" or "six seven".
    pars_list="${FIT_PARS:-six}"
    for pars in $pars_list
    do

        # J100 six-parameter background-only fit.
        region=J50
        datafile=Input/data/dijetTLA/mjj_spectra_J50_dataAll.root
        datahist=hists_yStar06_massCut/HLT_j0_perf_ds1_L1J50/h_mjj
        rangelow=344
        rangehigh=2079
            for sigmean in 400 #350 300 250 225 200 180 160 150
            do
                #rangelow=80 # using systematics !!!
                #rangelow=80
            #rangelow=150
            #rangelow=200
            #rangelow=300
            #rangehigh=1000
            #rangehigh=200



            sigmean=400
            sigwidth=8
            #sigwidth=-1 # using systematics !!!!!!!!!!!!!!!!!!!!!

            #dosignal=0 # turn this off for bkg only!!!!!!!!!!!!!!!!!!!!!
            dosignal=0 # using systematics !!!
            dolimit=0




        # regular pseudodata validation tests
        #datafile=/eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_90_1000_sixPar/Run3_TLA90_1000_sixPar_finebinned_scale.root
        #datahist=pseudodata_0

                #folder=/eos/user/l/lbazzano/TLA/FreqFrameOutputs/minimumStudy/120_run_${pars}Par
            #folder=/eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_${rangelow}_${rangehigh}_${pars}Par
            folder=$out_dir/${region}/run_${rangelow}_${rangehigh}_${pars}Par
            #folder=/eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_${rangelow}_${rangehigh}_${pars}Par_BH # using BumpHunter !!!
            #folder=/eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_${rangelow}_${rangehigh}_${pars}Par_1000toys


                # using systematics !!!
            #sysfile=/eos/user/l/lbazzano/TLA/dijet-isr-tla-ntuple-analysis/dir/signalUncertainty_interpolated.json # using systematics !!!
                #sysfile=/eos/user/l/lbazzano/TLA/dijet-isr-tla-ntuple-analysis/old_ntuples/MGPy8EG_S1_qqa_Ph25_mRp400_gASp1_qContentUDSC/signalUncertainty_interpolated.json # using systematics !!!
            #sysfile=/eos/user/l/lbazzano/TLA/dijet-isr-tla-ntuple-analysis/nv8/user.lbazzano.510397.MGPy8EG_S1_qqa_Ph25_mRp400_gASp1_qContentUDSC.e8523_e8586_s4159_s4114_r16102_r15514.nv8_syst_2705_tree.root/signalUncertainty_interpolated.json # using systematics !!!
            sysfile=/eos/user/l/lbazzano/TLA/tla-ntuple-analysis/condor_result/MGPy8EG_S1_qqa_Ph25_mRp${sigmean}_gASp1_qContentUDSC/signalUncertainty_interpolated.json


            # systematics, data are injected files after scaling, always using pseudodata0 histogram (****)
            #datafile=/eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_${rangelow}_${rangehigh}_${pars}Par_syst/Run3_TLA87_1000_eightPar_finebinned_scale25.28_mean${sigmean}_width${sigwidth}_amp3.root
            #folder=/eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_${rangelow}_${rangehigh}_${pars}Par_syst/systematics_gaussian_mean${sigmean}_width${sigwidth}_amp3 # using systematics !!!

                # systematic testing higher minimum for fit
            #datafile=/eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_87_1000_eightPar_syst/Run3_TLA87_1000_eightPar_finebinned_scale25.28_mean${sigmean}_width${sigwidth}_amp3.root
            #folder=/eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_87_1000_eightPar_syst/systematics_gaussian_mean${sigmean}_width${sigwidth}_amp3_100_10000 # using systematics !!!


                # systematic testing injected from Injection Study
            #datafile=/eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_87_1000_tenPar/injected/Run3_TLA87_1000_tenPar_finebinned_scale_mean400_width10_amp3.root
            #folder=/eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_87_1000_eightPar_syst/systematics_gaussian_mean${sigmean}_width${sigwidth}_amp3_fromInjectedStudy # using systematics !!!

            # new injections, same strategy as in the Injection Study (sould need to think why these results give different correlation than "Injection Study" )
            #datafile=/eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_87_1000_tenPar/systematics/Run3_TLA87_1000_tenPar_finebinned_scale_mean${sigmean}_width${sigwidth}_amp3.root
                #folder=/eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_87_1000_tenPar/systematics/new/systematics_gaussian_mean${sigmean}_width${sigwidth}_amp3

            # Z' injections (no systematics, to do SS SI BS)
            #datafile=/eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_87_1000_tenPar/injected_Zprime/Run3_TLA87_1000_tenPar_finebinned_scale_Zprime${sigmean}_amp3.root
                #folder=/eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_87_1000_tenPar/injected_Zprime/systematics_gaussian_mean${sigmean}_amp3

            #datahist=pseudodata_0



            topfile=config/dijetisrTLA/dijetisrTLA.template
            wsfile=${folder}/dijetisrTLA_combWS_${pars}Par.root

            signalfile=config/dijetisrTLA/signal/signal_dijetisrTLA.template
            #signalfile=config/dijetisrTLA/signal/signal_dijetisrTLA_zprime_parametrized.template # using systematics !!!
            # alex signal file xml testing
            #signalfile=config/dijetisrTLA/noSyst/signal_dijetisr_zprime_parameterized_noSyst.template

            backgroundfile=config/dijetisrTLA/background_dijetisrTLA_${pars}Par.template

                categoryfile=config/dijetisrTLA/category_dijetisrTLA.template
            #categoryfile=config/dijetisrTLA/category_dijetisrTLA_zprime_parametrized.template # using systematics !!!
            # alex signal file xml testing
            #categoryfile=config/dijetisrTLA/noSyst/category_dijetisrTLA_noSyst.template


            #outputfile=${folder}/FitResult_anaFit_${pars}Par_mean${sigmean}_width${sigwidth}.root
                outputfile=${folder}/FitResult_anaFit_${pars}Par_bkgOnly.root
            #outputfile=${folder}/FitResult_anaFit_${pars}Par_mean${sigmean}.root



            #datafile=/eos/user/l/lbazzano/TLA/FreqFrameTestBranch/FrequentistFramework/alexFile/outputHistograms.root
            #datafile=/afs/cern.ch/user/l/lbazzano/public/data22_allcuts_histos.root # recent mjj with isolation cuts
            #datafile=/afs/cern.ch/user/l/lbazzano/public/data22_histos.root # (0.445 /fb) recent mjj without isolation cuts
            #datafile=/eos/user/l/lbazzano/TLA/FreqFrameTestBranch/FrequentistFramework/alexFile/new/data23_allCutsOpt_histos.root # (0.927/fb) tentative isolation cuts applied
                #datafile=/eos/user/l/lbazzano/TLA/FreqFrameTestBranch/FrequentistFramework/alexFile/new/mjj_00451866.root # going down to 50 GeV
            #datahist=mjj_50
            #datafile=/eos/user/l/lbazzano/TLA/FreqFrameTestBranch/FrequentistFramework/alexFile/new/data23_optimizedCuts_histos.root # eta 2.1 cut
            #datafile=/eos/user/l/lbazzano/TLA/FreqFrameTestBranch/FrequentistFramework/alexFile/mc_clean/data23_mjj100_histos.root # feb 2025
                #datafile=/eos/user/l/lbazzano/TLA/FreqFrameTestBranch/FrequentistFramework/alexFile/calib_etacut_mcclean_isocut/data23_calib_eta2p1_EMFrac0p9_histos.root # mar 2025 iso cut
                #datafile=/eos/user/l/lbazzano/TLA/FreqFrameTestBranch/FrequentistFramework/alexFile/calib_etacut_mcclean/data23_calib_eta2p1_histos.root # mar 2025 NO iso cut

                #datafile=/eos/user/l/lbazzano/TLA/FreqFrameOutputs_mcclean/run_systematics_80_1000_sevenPar/data23_optimizedCuts_histos_injected_mean400_width10_amp3.root # signal injected
            #datafile=/eos/user/l/lbazzano/TLA/hists/onlineoffline/user.lbazzano.data22_13p6TeV.440447.J2_TLA_g35_trigger_08_08_23/mjj_histograms.root
            #Input/data/dijetisrTLA/outputHistograms.root
            # datafile=run/postfit.root
            nbkg="dummy" #overwritten by prefit
            maskthreshold=0.01 #0.01
            doprefit=1

            flags=""
            if (( $dosignal )); then flags="$flags --dosignal"; fi
            if (( $dolimit )); then flags="$flags --dolimit"; fi
            if (( $doprefit )); then flags="$flags --doprefit"; fi

            "$analysis_runner" \
                --datafile "$datafile" \
                --datahist "$datahist" \
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

            analysis_status=$?
            if (( analysis_status != 0 )); then
                echo "ERROR: run_anaFit.py failed with exit code $analysis_status" >&2
                exit "$analysis_status"
            fi

            #--sysfile $sysfile \
                    # using systematics!!!! comment sysfile if not the case

                    #nsig=args.nsig,

            toys=100

            if [[ "${ANAFIT_SKIP_PLOTS:-0}" != "1" ]]; then
                python "$repo_dir/python/plotPostFit.py" \
                    -i "${folder}/PostFit_anaFit_${pars}Par_bkgOnly.root" \
                    -o "${folder}/postFit.pdf"

                root -l -q "plot_postfit.cpp(\"$folder\", \"$pars\")"
            fi

            # upscaling
            #scalefactor=$( bc <<< 'scale=2; 30/1.015' )
            #scalefactor=$( bc <<< 'scale=2; 25.2853/1.0' )
            #echo python python/generatePseudoData.py --infile ${outputfile/FitResult/PostFit} --inhist Run3TLA/postfit --outhist pseudodata --outfile ${folder}/Run3_TLA${rangelow}_${rangehigh}_${pars}Par_finebinned_scale${scalefactor}.root --nreplicas $toys --scaling $scalefactor
            #python python/generatePseudoData.py --infile ${outputfile/FitResult/PostFit} --inhist Run3TLA/postfit --outhist pseudodata --outfile ${folder}/Run3_TLA${rangelow}_${rangehigh}_${pars}Par_finebinned_scale${scalefactor}.root --nreplicas $toys --scaling $scalefactor

            # no upscaling
        # XXX
            #echo python python/generatePseudoData.py --infile ${outputfile/FitResult/PostFit} --inhist Run3TLA/postfit --outhist pseudodata --outfile ${folder}/Run3_TLA${rangelow}_${rangehigh}_${pars}Par_finebinned_scale${scalefactor}.root --nreplicas $toys
            #python python/generatePseudoData.py --infile ${outputfile/FitResult/PostFit} --inhist Run3TLA/postfit --outhist pseudodata --outfile ${folder}/Run3_TLA${rangelow}_${rangehigh}_${pars}Par_finebinned_scale${scalefactor}.root --nreplicas $toys

            done
        if command -v alert >/dev/null 2>&1; then
            alert
        fi
    done
}
