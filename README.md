Incremental CdA analysis. All resulting csv files are in the 2 folders, test1 (IPA) and test2 (LOX). Below is an outline of how the scripts were used and in what order: 

#TLDR:
- To see "raw" data, go to each tests' folder and check the csv file "1_test{}_trimmed.csv" . PT1 and 2 are venturis. PT 3 is tank PT. PT 4 is orifice PT.
- To see data with cda values and mass flow rates, go to each tests' folder and check the csv file "3_test{}_with_cda.csv"
- To see graphs for cda values, go to each tets' folder and download the html files. Then, open it by either running "open {file name}" on Mac, or "start {file name}"

#More Details and Equations used:

1. Raw Data - all the TXT files in the folder raw data (both tests). For each test: 

2. Processed Data - CSV 1  (one for IPA, one for LOX). Trim off all data from before/after orifice mass flow is 14.84. \
    -> TIME | PT1 | PT2 | PT3 (Tank PT) | PT4 (Orifice PT)| Mass Flow (orifice)\
   Script: process_raw.py\
   Output: 1_test{}_trimmed.csv\

4. Processed with all mass flows - CSV 2\
    -> TIME | PT1 | PT2 | PT3 (Tank PT) | PT4 (Orifice PT) | Mass Flow (orifice) | Mass Flow (venturi)\
   Script: venturi_mass_flow.py\
   Output: 2_test{}_with_venturi.csv\
   Equations:
     - Mass Flow (IPA venturi) = 1.76310132e-5 * sqrt(2 * (PT2 - PT1) * 6894.8 * 999.1)
     - Mass Flow (LOX venturi) = 2.34674906e-5 * sqrt(2 * (PT2 - PT1) * 6894.8 * 999.1)

6. Final processed with CdA values - CSV 3\
    -> TIME | PT1 | PT2 | PT3 (Tank PT) | PT4 (Orifice PT) | Mass Flow (venturi) | CdA (venturi) | Mass Flow (orifice) | CdA (orifice)\
   Script: cda_calculations.py\
   Output: 3_test{}_with_cda.csv\
   Equations:
     - orifice CdA: CdA = mass flow (venturi) /sqrt(2 * 999.1 * (PT3-4)*6894.8)
     - venturi CdA: CdA = mass flow (orifice) /sqrt(2 * 999.1 * (PT3-PT4)*6894.8)
  
7. Graph CdA (y) vs mass flow(x) for both venturi and orifice\
   First download these 2 files:
   - graph_cda_test1.html 
   - graph_cda_test2.html
  To see these graphs in your browser: 
  On Mac, from the directory you downloaded these files on, run "start graph_cda_test{}.html"
  On Windows, from the directory you downloaded these files on, run "start graph_cda_test{}.html"
  you can zoom in by selecting part of the graph, check out tool bar!

