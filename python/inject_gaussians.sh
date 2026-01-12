#!/bin/bash

#infile="/eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_87_1000_tenPar/Run3_TLA87_1000_tenPar_finebinned_scale.root"
#infile="/eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_108_1000_tenPar/Run3_TLA108_1000_tenPar_finebinned_scale.root"
#infile="/eos/user/l/lbazzano/TLA/FreqFrameTestBranch/FrequentistFramework/alexFile/1fb/data23_1fb_eta2p1_EMFrac0p93_ystar0p8.root"
infile="/eos/user/l/lbazzano/TLA/FreqFrameOutputs/run_125_1000_tenPar/Run3_TLA125_1000_tenPar_finebinned_scale.root"
histname="pseudodata"
firsttoy=0
lasttoy=99

for sigmean in 120 150 180 200 250 300 400 600 800; do 
    for sigwidth in 5 10 15; do
        for sigamp in {0..5}; do 
             echo "python InjectGaussian.py \
                --infile $infile \
                --histname $histname \
                --sigmean $sigmean \
                --sigwidth $sigwidth \
                --sigamp $sigamp \
                --firsttoy $firsttoy \
                --lasttoy $lasttoy "
        done
    done
done
