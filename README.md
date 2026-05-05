Incremental CdA analysis. All resulting csv files are in the 2 folders, test1 (IPA) and test2 (LOX). Below is an outline of how the scripts were used and in what order: 

1. Raw Data - all the TXT files in the folder raw data (both tests). For each test: 

2. Processed Data - CSV 1  (one for IPA, one for LOX). Trim off all data from before/after orifice mass flow is 14.84. 
    -> TIME | PT1 | PT2 | Mass Flow (orifice)
   Script: process_raw.py
   Output: 1_test{}_trimmed.csv

4. Processed with all mass flows - CSV 2 
    -> TIME | PT1 | PT2 | Mass Flow (orifice) | Mass Flow (venturi)
   Script: venturi_mass_flow.py
   Output: 2_test{}_with_venturi.csv
   Equations:
     - Mass Flow (IPA venturi) = 3.19408152e-5 * sqrt(2 * (PT2 - PT1) * 6894.8 * 999.1)
     - Mass Flow (LOX venturi) = 1.83788431e-5 * sqrt(2 * (PT2 - PT1) * 6894.8 * 999.1)

6. Final processed with CdA values - CSV 3
    -> TIME | PT1 | PT2 | Mass Flow (venturi) | CdA (venturi) | Mass Flow (orifice) | CdA (orifice)
   Script: cda_calculations.py
   Output: 3_test{}_with_cda.csv
   Equations:
     - CdA equation for orifice: CdA = mass flow (orifice) /sqrt(2*999.1*(PT2-0)*6894.8)
     - CdA equation for venturi: CdA = mass flow (venturi) /sqrt(2*999.1*(PT2-PT1)*6894.8)
  
7. Graph CdA (y) vs mass flow(x) for both venturi and orifice
   Script: graph_cda.py
   Output: graph_cda_test{}.png

