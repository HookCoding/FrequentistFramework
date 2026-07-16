#!/usr/bin/env python

from stitch_swiftResults import StitchSwiftResults

path = "/afs/cern.ch/work/m/mtoscani/public/TLA/FrequentistFramework/run/"

patternMatches = [
 
   #"Swift_WHW1_fixLow1_TR0_fixHigh0_3par/PostFit_fivePar_J100yStar_bOnly_i*.root",
   #"Swift_WHW2_fixLow1_TR0_fixHigh0_3par/PostFit_fivePar_J100yStar_bOnly_i*.root",
   #"Swift_WHW3_fixLow1_TR0_fixHigh0_3par/PostFit_fivePar_J100yStar_bOnly_i*.root",
   #"Swift_WHW4_fixLow1_TR0_fixHigh0_3par/PostFit_fivePar_J100yStar_bOnly_i*.root",
   #"Swift_WHW5_fixLow1_TR0_fixHigh0_3par/PostFit_fivePar_J100yStar_bOnly_i*.root",
   #"Swift_WHW6_fixLow1_TR0_fixHigh0_3par/PostFit_fivePar_J100yStar_bOnly_i*.root",
   "Swift_WHW7_fixLow1_TR0_fixHigh0_3par/PostFit_fivePar_J100yStar_bOnly_i*.root",
   "Swift_WHW8_fixLow1_TR0_fixHigh0_3par/PostFit_fivePar_J100yStar_bOnly_i*.root",
    ]

outputFileNames = [
  #"Swift_WHW1_fixLow1_TR0_fixHigh0_3par.root",
  #"Swift_WHW2_fixLow1_TR0_fixHigh0_3par.root",
  #"Swift_WHW3_fixLow1_TR0_fixHigh0_3par.root",
  #"Swift_WHW4_fixLow1_TR0_fixHigh0_3par.root",
  #"Swift_WHW5_fixLow1_TR0_fixHigh0_3par.root",
  #"Swift_WHW6_fixLow1_TR0_fixHigh0_3par.root"
  "Swift_WHW7_fixLow1_TR0_fixHigh0_3par.root",
  "Swift_WHW8_fixLow1_TR0_fixHigh0_3par.root"   
  ]


for pattern, outName in zip(patternMatches, outputFileNames):
  
  fullPath = path + pattern
  outName = path + outName
  print "Doing:", fullPath
  StitchSwiftResults( fullPath, outName )

