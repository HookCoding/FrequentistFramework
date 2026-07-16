#!/usr/bin/env python

initialParameters = {
    'TLA2016' : { 
	
	'J100' : {  	
	  
	  'nbkg' 	: "2E8,0,3E8",
	  'datafile'	: "Input/data/dijetTLA/lookInsideTheBoxWithUniformMjj.root",
	  'datahist'	: "Nominal/DSJ100yStar06_TriggerJets_J100_yStar06_mjj_finebinned_all_data",
	  # Analysis range		
	  'low'  : 531 ,
	  'high' : 2997,
	},
    },
    'partialDataset' : { # Partial datafile (1st unblinding)
	
	'J100' : {  	
	  
	  'nbkg' 	: "4E7,0,1E8",
	  'datafile'	: "Input/data/dijetTLA/unblinding1_mjj_spectra.root",
	  'datahist'	: "L1J100/Mjj_1GeVbinning",
	  # Analysis range		
	  'low'  : 457,
	  'high' : 2997,
	  'lumi' : 3.6,
	},
	
	'J40'  : {  
	  
	  'nbkg'	: "1E7,0,2E7",
	  'datafile'	: "Input/data/dijetTLA/unblinding1_mjj_spectra.root",
	  'datahist'	: "L1J40/Mjj_1GeVbinning",                      	  
	  'low'  : 302,
	  'high' : 1516, 
	},
	
	'J50'  : {	
	  
	  'nbkg' : "1E7,0,2E7",
	  'datafile'	: "Input/data/dijetTLA/unblinding1_mjj_spectra.root",
	  'datahist'	: "L1J50/Mjj_1GeVbinning",
	  'low'  : 302,
	  'high' : 1516, 
	},

    },

    'full' : {  # Full lumi: total datafile

	'J100' : {  	
	  
	  'nbkg' 	: "9E8,0,2E9",
	  'datafile'	: "",
	  'datahist'	: "",
	  'low'  :457 ,
	  'high' : 2997,
	  'lumi' : 133.2,
	},
	
	'J40'  : {  
	  
	  'nbkg'	: "1E7,0,2E7",
	  'datafile'	: "",
	  'datahist'	: "",                      	  
	  'low'  : 302,
	  'high' : 1516, 
	},
	
	'J50'  : {	
	  
	  'nbkg' : "1E7,0,2E7",
	  'datafile'	: "",
	  'datahist'	: "",
	  'low'  : 302,
	  'high' : 1516, 
	},
    },
}
