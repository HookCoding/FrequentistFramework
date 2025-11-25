#!/bin/bash

#infile="/eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_87_1000_tenPar/Run3_TLA87_1000_tenPar_finebinned_scale.root"
infile="/eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_108_1000_tenPar/Run3_TLA108_1000_tenPar_finebinned_scale.root"
histname="pseudodata"
firsttoy=0
lasttoy=99

#sigamp=3
sighist="mjj_yStar_cut_nominal"

sigfiles=(
/eos/user/l/lbazzano/TLA/tla-ntuple-analysis/condor_result/MGPy8EG_S1_qqa_Ph25_mRp150_gASp1_qContentUDSC/systematic_updown_mjj_MGPy8EG_S1_qqa_Ph25_mRp150_gASp1_qContentUDSC.root
/eos/user/l/lbazzano/TLA/tla-ntuple-analysis/condor_result/MGPy8EG_S1_qqa_Ph25_mRp160_gASp1_qContentUDSC/systematic_updown_mjj_MGPy8EG_S1_qqa_Ph25_mRp160_gASp1_qContentUDSC.root
/eos/user/l/lbazzano/TLA/tla-ntuple-analysis/condor_result/MGPy8EG_S1_qqa_Ph25_mRp180_gASp1_qContentUDSC/systematic_updown_mjj_MGPy8EG_S1_qqa_Ph25_mRp180_gASp1_qContentUDSC.root
/eos/user/l/lbazzano/TLA/tla-ntuple-analysis/condor_result/MGPy8EG_S1_qqa_Ph25_mRp200_gASp1_qContentUDSC/systematic_updown_mjj_MGPy8EG_S1_qqa_Ph25_mRp200_gASp1_qContentUDSC.root
/eos/user/l/lbazzano/TLA/tla-ntuple-analysis/condor_result/MGPy8EG_S1_qqa_Ph25_mRp225_gASp1_qContentUDSC/systematic_updown_mjj_MGPy8EG_S1_qqa_Ph25_mRp225_gASp1_qContentUDSC.root
/eos/user/l/lbazzano/TLA/tla-ntuple-analysis/condor_result/MGPy8EG_S1_qqa_Ph25_mRp250_gASp1_qContentUDSC/systematic_updown_mjj_MGPy8EG_S1_qqa_Ph25_mRp250_gASp1_qContentUDSC.root
/eos/user/l/lbazzano/TLA/tla-ntuple-analysis/condor_result/MGPy8EG_S1_qqa_Ph25_mRp300_gASp1_qContentUDSC/systematic_updown_mjj_MGPy8EG_S1_qqa_Ph25_mRp300_gASp1_qContentUDSC.root
/eos/user/l/lbazzano/TLA/tla-ntuple-analysis/condor_result/MGPy8EG_S1_qqa_Ph25_mRp350_gASp1_qContentUDSC/systematic_updown_mjj_MGPy8EG_S1_qqa_Ph25_mRp350_gASp1_qContentUDSC.root
/eos/user/l/lbazzano/TLA/tla-ntuple-analysis/condor_result/MGPy8EG_S1_qqa_Ph25_mRp400_gASp1_qContentUDSC/systematic_updown_mjj_MGPy8EG_S1_qqa_Ph25_mRp400_gASp1_qContentUDSC.root
)

sigfiles_dscb=(
/eos/user/l/lbazzano/TLA/tla-ntuple-analysis/condor_result/MGPy8EG_S1_qqa_Ph25_mRp150_gASp1_qContentUDSC/signalUncertainty_interpolated.json
/eos/user/l/lbazzano/TLA/tla-ntuple-analysis/condor_result/MGPy8EG_S1_qqa_Ph25_mRp160_gASp1_qContentUDSC/signalUncertainty_interpolated.json
/eos/user/l/lbazzano/TLA/tla-ntuple-analysis/condor_result/MGPy8EG_S1_qqa_Ph25_mRp180_gASp1_qContentUDSC/signalUncertainty_interpolated.json
/eos/user/l/lbazzano/TLA/tla-ntuple-analysis/condor_result/MGPy8EG_S1_qqa_Ph25_mRp200_gASp1_qContentUDSC/signalUncertainty_interpolated.json
/eos/user/l/lbazzano/TLA/tla-ntuple-analysis/condor_result/MGPy8EG_S1_qqa_Ph25_mRp225_gASp1_qContentUDSC/signalUncertainty_interpolated.json
/eos/user/l/lbazzano/TLA/tla-ntuple-analysis/condor_result/MGPy8EG_S1_qqa_Ph25_mRp250_gASp1_qContentUDSC/signalUncertainty_interpolated.json
/eos/user/l/lbazzano/TLA/tla-ntuple-analysis/condor_result/MGPy8EG_S1_qqa_Ph25_mRp300_gASp1_qContentUDSC/signalUncertainty_interpolated.json
/eos/user/l/lbazzano/TLA/tla-ntuple-analysis/condor_result/MGPy8EG_S1_qqa_Ph25_mRp350_gASp1_qContentUDSC/signalUncertainty_interpolated.json
/eos/user/l/lbazzano/TLA/tla-ntuple-analysis/condor_result/MGPy8EG_S1_qqa_Ph25_mRp400_gASp1_qContentUDSC/signalUncertainty_interpolated.json
)


for sigamp in {0..5}; do
    for i in "${!sigfiles[@]}"; do
        sigfile="${sigfiles[$i]}"
        sigfile_dscb="${sigfiles_dscb[$i]}"

        echo "python InjectZprime.py \
            --infile $infile \
            --histname $histname \
            --sigfile $sigfile \
            --sigfile_dscb $sigfile_dscb \
            --sighist $sighist \
            --sigamp $sigamp \
            --firsttoy $firsttoy \
            --lasttoy $lasttoy"
    done
done

