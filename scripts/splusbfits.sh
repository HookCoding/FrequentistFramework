#!/bin/bash

# Loop from 150 to 1000 in increments of 25
for ((SIG=150; SIG<=1000; SIG+=25)); do
    for ((WID=5; WID<=10; WID+=5)); do

    # Run the quickfit command with the current value of SIG
    quickFit -f run/dijetisrTLA_combWS_fourPar.root -d combData -p nsig_mean${SIG}_width${WID} --checkWS 1  --hesse 1 --savefitresult 1 --saveWS 1 --saveNP 1 --saveErrors 1 -o run/FitResult_mean${SIG}_width${WID}.root
    done
done