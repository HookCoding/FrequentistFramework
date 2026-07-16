import ROOT
import os, sys

doSysts = True

# Which card?
doSignalCards  = False # go check the Model node information in the if statement!
doCategoryCard = False # go check Data information
doSteeringCard = True  # go check 


mass_grid = [ 200,250,300,350,400,450,500,550,600,650,700,750,800,850,900,950,1000,1050,1100,1150,1200,1250,1300,1350,1400,1450,1500,1550,1600,1650,1700,1750,1800,1850,1900,1950,2000]
coupling = '0p1'

##################################################################

if doSignalCards:

  for mR in mass_grid:
    
    massStr = str(mR)

    # CHECK
    outputfileName = "config/dijetTLA/signal/signal_dijetTLA_J100yStar06_zprime_gq{0}_mR{1}".format(coupling, massStr)
    if not doSysts:
      outputfileName += "_noSysts"
    outputfileName += ".xml"

    # Model Node:
    Input = "Input/model/dijetTLA/zprime/HLT_j0_perf_ds1_L1J100/HistFactory_dijetTLA_J100yStar06_zprime_gq{0}_mR{1}.root".format(coupling, massStr)
    Type = "External"
    WSName  = "combined"
    #RooRealSumPdf:
    ModelName = "J100yStar06_model"
    ObservableName = "obs_x_J100yStar06"


    with open( outputfileName, 'w') as f:
	
      HEADER = "<!DOCTYPE Model  SYSTEM \'AnaWSBuilder.dtd\'>\n"
      f.write(HEADER)
      
      # Model Parent Node:
      modelNodeStr = "<Model Type=\"{0}\" Input=\"{1}\" WSName=\"{2}\" ModelName=\"{3}\" ObservableName=\"{4}\">\n\n".format( Type, Input, WSName, ModelName, ObservableName )
      f.write( modelNodeStr )

      # Rename Lumi stuff:
      f.write(" <Item Name=\"unit[1]\" />\n" )
      f.write(" <Rename OldName=\"Lumi\" NewName=\"unit\" />\n\n" )

      if doSysts:
	
	# open Input file and read systs from there:
	inFile = ROOT.TFile( Input, "READ")
	ws = inFile.Get( WSName )
	# get constraint names:
	pdfs = ws.allPdfs()
	pdfNames = [ p.GetName() for p in pdfs if ("Constraint" in p.GetName() and "alpha" in p.GetName()) ]
	# get NP names:
	variables = ws.allVars()
	varNames = [ v.GetName() for v in variables if ("alpha" in v.GetName() and not "nom" in v.GetName() ) ]
	# get Global Observables:
	gos = ws.genobj("ModelConfig").GetGlobalObservables()
	goNames = [go.GetName() for go in gos if "alpha" in go.GetName() ]
	# check that lists are same size:
	if not ( len(goNames) == len(pdfNames) and len(pdfNames) == len(varNames) ):
	  print "ERROR in retrieving systematics information. DEBUG INFO:"
	  print "CONSTRAINT PDF NAMES:"
	  for p in pdfNames:
	    print " ",p
	  print "NPNAMES:"
	  for v in varNames:
	    print " ",v
	  print "GONAMES:"
	  for g in goNames:
	    print " ",g

	  sys.exit()

	for p,v,g in zip( pdfNames, varNames, goNames):
	  systNodeStr = " <ExtSyst ConstrName=\"{0}\" NPName=\"{1}\" GOName=\"{2}\" />\n".format( p, v, g )
	  f.write( systNodeStr )

      # close model node:
      f.write( "\n" )
      f.write( "</Model>" )
      f.close()

#######################################################333
if doCategoryCard:
  
  # CHECK
  outputfileName = "config/dijetTLA/category_dijetTLA_J100yStar06_fivePar_zprime"
  if not doSysts:
    outputfileName+="_noSysts"
  outputfileName+=".xml"

  channelName = "J100yStar06"
  dataInputFile = "Input/data/dijetTLA/lookInsideTheBoxWithUniformMjj.root" 
  dataType = "histogram"
  histName = "Nominal/DSJ100yStar06_TriggerJets_J100_yStar06_mjj_finebinned_all_data"

  
  with open( outputfileName, 'w') as f:
  
    HEADER = "<!DOCTYPE Channel SYSTEM \'AnaWSBuilder.dtd\'>\n"
    CHstr  = "<Channel Name=\"{0}\" Type=\"shape\" Lumi=\"1\">\n\n".format(channelName)
    DATAstr = "  <Data InputFile=\"{0}\" FileType=\"{1}\" HistName=\"{2}\" Observable=\"obs_x_channel[531,2079]\" Binning=\"1548\" InjectGhost=\"1\"/>\n\n".format(dataInputFile, dataType, histName)
    BKGstr1 = "  <Sample Name=\"background\" InputFile=\"config/dijetTLA/background_dijetTLA_J100yStar06_fivePar.xml\" MultiplyLumi=\"0\" ImportSyst=\":self:\">\n"
    BKGstr2 = "    <!-- 29/fb: -->\n"
    BKGstr3 = "    <NormFactor Name=\"nbkg[2E8,0,3E8]\"/>\n"
    BKGstr4 = "  </Sample>\n\n"

    f.write(HEADER)
    f.write(CHstr)
    f.write(DATAstr)
    f.write(BKGstr1)
    f.write(BKGstr2)
    f.write(BKGstr3)
    f.write(BKGstr4)

    for mR in mass_grid:
      
      massStr = str(mR)
      if doSysts:
	systStr = ""
      else:
	systStr = "_noSysts"
      SAMPLEstr = "  <Sample Name=\"signal_mR{0}_gq{1}\" InputFile=\"config/dijetTLA/signal/signal_dijetTLA_J100yStar06_zprime_gq{1}_mR{0}{2}.xml\" MultiplyLumi=\"0\" >\n".format(massStr,coupling, systStr)
      SAMPLEstr1 ="    <NormFactor Name=\"nsig_mR{0}_gq{1}[0,0,1E6]\"/>\n".format(massStr, coupling)
      f.write(SAMPLEstr)
      f.write(SAMPLEstr1)
      f.write("  </Sample>\n\n")
    
    f.write("</Channel>\n")
    f.close()


if doSteeringCard:

  # CHECK
  outputfileName = "config/dijetTLA/dijetTLA_J100yStar06_zprime.xml"
  wsOutputFile   = "run/dijetTLA/dijetTLA_J100yStar06_zprime.root" 
  categoryCard   = "config/dijetTLA/category_dijetTLA_J100yStar06_fivePar_zprime.xml"
  
  with open( outputfileName, 'w') as f:
  
    HEADER  = "<!DOCTYPE Combination  SYSTEM \'AnaWSBuilder.dtd\'>\n"
    CombStr = "<Combination WorkspaceName=\"combWS\" ModelConfigName=\"ModelConfig\" DataName=\"combData\" OutputFile=\"{0}\">\n\n".format(wsOutputFile)
    INPUTstr = "  <Input>{0}</Input>\n\n".format(categoryCard)
    POIs = ["nsig_mR{0}_gq{1}".format(m, coupling) for m in mass_grid]
    POIs  = ','.join(POIs)
    POIstr = "  <POI>{0}</POI>\n\n".format(POIs)
    ASIMOVstr_1 = "  <Asimov Name=\"POISnap\"  Setup=\"\"  Action=\"savesnapshot\" SnapshotPOI=\"nominalPOI\"/>\n\n"
    
    POIsetup = POIs.replace(coupling, coupling+"=0")
    ASIMOVstr_2 = "  <Asimov Name=\"NPSnap\"  Setup=\"{0}\"  Action=\"fixsyst:fit:float:savesnapshot:nominalPOI\" SnapshotNuis=\"nominalNuis\" SnapshotGlob=\"nominalGlobs\"/>\n\n".format(POIsetup)

    f.write(HEADER)
    f.write(CombStr)
    f.write(INPUTstr)
    f.write(POIstr)
    f.write(ASIMOVstr_1)
    f.write(ASIMOVstr_2)
    f.write("</Combination>")
    f.close()
