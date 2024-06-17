# Script to quickly write many gaussian signal xml cards

mass = list(range(150, 1000, 25))
widths = [0.05,0.1] 

def writeSignals():
    # Example Output
    """
    <!DOCTYPE Model  SYSTEM 'AnaWSBuilder.dtd'>
    <Model Type="UserDef">
    <Item Name="mass_450[450]"/>
    <Item Name="prod::width_450_5(mass_450,0.05)"/>
    <ModelItem Name="RooGaussian::signal(:observable:, mass_450, width_450_5)"/>
    </Model>
    """

    for m in mass:
        for w in widths:
            filename = f"gaussianSignal_mean{m}_width{int(w*100)}.xml"
            with open(filename, "w") as f:
                f.write("<!DOCTYPE Model  SYSTEM \'AnaWSBuilder.dtd\'>" + '\n' + '<Model Type="UserDef">' + '\n')
                f.write(f'  <Item Name="mass_{m}[{m}]"/>' + '\n')
                f.write(f'  <Item Name="prod::width_{m}_{int(w*100)}(mass_{m},{w:.3f})"/>' + '\n')
                f.write(f'  <ModelItem Name="RooGaussian::signal(:observable:, mass_{m}, width_{m}_{int(w*100)})"/>' + '\n')
                f.write("</Model>")

def writeCategory():
    #Example
    """
    <!DOCTYPE Channel SYSTEM 'AnaWSBuilder.dtd'>
    <Channel Name="mc16d" Type="shape" Lumi="1">
      <Data InputFile="/afs/cern.ch/work/a/agekow/FrequentistFramework/dijetisrTLA/root_files/singlePhoton_mjj.root" FileType="histogram" HistName="mjj" Observable="mjj[100,500]" Binning="400"/>

    <Sample Name="background" InputFile="config/dijetisrTLA/background_dijetISR_fivePar.xml" MultiplyLumi="0" ImportSyst=":self:">
      <NormFactor Name="nbkg[1E8,1E8,5E8]"/>
    </Sample>

    <Sample Name="signal_mean450_width5" InputFile="config/dijetisrTLA/signal/test_mean450_width5.xml" MultiplyLumi="1" >
      <NormFactor Name="nsig_mean450_width5[0,-1E4,1E4]" />
    </Sample>

    </Channel>
    """
    # May need to go into category card and alter intiial guesses by hand
    filename = "category_dijetisrTLA.xml"
    with open(filename, "w") as f:

      f.write("<!DOCTYPE Channel SYSTEM 'AnaWSBuilder.dtd'>" + '\n')
      f.write('<Channel Name="mc16d" Type="shape" Lumi="1">' + '\n')
      f.write('  <Data InputFile="/afs/cern.ch/work/a/agekow/FrequentistFramework/dijetisrTLA/root_files/singlePhoton_mjj.root" FileType="histogram" HistName="mjj" Observable="mjj[100,1000]" Binning="900"/>' + '\n'*2)
      f.write('  <Sample Name="background" InputFile="config/dijetisrTLA/background_dijetISR_fivePar.xml" MultiplyLumi="0" ImportSyst=":self:">' + '\n')
      f.write('    <NormFactor Name="nbkg[3E8,3E8,6E8]"/>' + '\n' + '  </Sample>' + '\n'*2)
      for m in mass:
          for w in widths:
              name = f'signal_mean{m}_width{int(w*100)}'
              f.write(f'  <Sample Name="{name}" InputFile="config/dijetisrTLA/signal/gaussianSignal_mean{m}_width{int(w*100)}.xml" MultiplyLumi="1">' + '\n')
              f.write(f'    <NormFactor Name="nsig_mean{m}_width{int(w*100)}[0,-1E3,1E3]" />' + '\n' + '  </Sample>' + '\n'*2)
      f.write('</Channel>')

def writeTopCard():
  """
  !DOCTYPE Combination  SYSTEM 'AnaWSBuilder.dtd'>
  <Combination WorkspaceName="combWS" ModelConfigName="ModelConfig" DataName="combData" OutputFile="workspace/dijetisrTLA/dijetisrTLA.root" Blind="false">
    <Input>config/dijetISRRun3/category_dijetISRRun3.xml</Input>
    <POI>nsig_mean450_width5,nbkg</POI>
    <Asimov Name="POISnap"  Setup=""  Action="savesnapshot" SnapshotPOI="nominalPOI"/>
    <Asimov Name="NPSnap"  Setup="nsig_mean450_width5=0" Action="fixsyst:fit:float:savesnapshot:nominalPOI" SnapshotNuis="nominalNuis" SnapshotGlob="nominalGlobs"/>
  </Combination>
  """
  filename = "dijetisrTLA.xml"
  with open(filename, "w") as f:
    f.write("<!DOCTYPE Combination SYSTEM 'AnaWSBuilder.dtd'>" + '\n')
    f.write('<Combination WorkspaceName="combWS" ModelConfigName="ModelConfig" DataName="combData" OutputFile="workspace/dijetisrTLA/dijetisrTLA.root" Blind="false">' + '\n')
    f.write('  <Input>config/dijetisrTLA/category_dijetisrTLA.xml</Input>' + '\n')
    f.write('  <POI> nbkg')
    for m in mass:
      for w in widths:
        f.write(f',nsig_mean{m}_width{int(w*100)}')
    f.write("</POI> \n")
    f.write('  <Asimov Name="POISnap"  Setup=""  Action="savesnapshot" SnapshotPOI="nominalPOI"/> \n')
    f.write('  <Asimov Name="NPSnap" Setup= "')
    for m in mass:
      for w in widths:
        f.write(f'nsig_mean{m}_width{int(w*100)}=0,' ) #may need to remove trailing comma
    f.write('" Action="fixsyst:fit:float:savesnapshot:nominalPOI" SnapshotNuis="nominalNuis" SnapshotGlob="nominalGlobs"/> \n')        
    f.write('</Combination>')

if __name__ == "__main__":
  import sys
  if sys.argv[1] == "signal":
    writeSignals()
  elif sys.argv[1] == "category":
    writeCategory()
  elif sys.argv[1] == "top":
    writeTopCard()
  else:
    print("Which function do you want to run?")
    sys.exit(1)
