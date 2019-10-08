import matplotlib
matplotlib.use('Qt4Agg')
import matplotlib.pyplot as plt
import numpy as np
import peakfinder_utils as pfu

pulses = pfu.read_pulses( "results/PARALLELTESTcrate1.amc1_chA_lvlthr130_totthr3.csv") 

for pulse in pulses:
  print pulse.bx


pfu.recon( "/home/bril_firmware/Documents/firmware/ubcm/fw/fpga/src/user/modules/peakfinder/tests/raw_data/stable_1000orbits_bcm1f.crate1.amc1_chA.bin", pulses )
