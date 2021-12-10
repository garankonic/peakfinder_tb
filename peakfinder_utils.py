################################################
# Common utilities for peak finder testbenches.
################################################
import matplotlib
matplotlib.use('Qt4Agg')
import matplotlib.pyplot as plt
import numpy as np
import csv
import sys
import pulse as p
import struct

def string_color( strng, color ):
  """
  Add color to a string.
  """
  if color == "red":
    strng = '\x1b[0;31;40m' + strng + '\x1b[0m'
  elif color == "green":
    strng = '\x1b[0;32;40m' + strng + '\x1b[0m'
  elif color == "yellow":
    strng = '\x1b[0;33;40m' + strng + '\x1b[0m'
  elif color == "blue":
    strng = '\x1b[0;34;40m' + strng + '\x1b[0m'
  return strng

def read_binary( file_object, chunk_size ):
  """
  Function generator to read a file piece by piece.
  """
  while True:
    data = file_object.read(chunk_size)
    if not data:
      break
    yield data

def write_pulses( filename, pulses):
  if not filename.endswith(".csv"):
    filename += ".csv"
  with open( filename , 'w') as f:
    for pulse in pulses:
      f.write( str(pulse.orbit) + ",")
      f.write( str(pulse.bx) + ",")
      f.write( str(pulse.amplitude) + ",")
      f.write( str(pulse.position) + ",")
      f.write( str(pulse.tot) + ",")
      f.write("\n")

## Make some common no_tp function?
## Some general histogramming function?

def occ_hist( filename, no_tp=False, tp_start=248 ,tp_stop=260 ):
  occ_histogram = [0] * 3564
  with open( filename ) as f:
    for row in csv.reader( f ):
      if no_tp == True:
        if int(row[1]) < tp_start or int(row[1]) > tp_stop:
          occ_histogram[ int(row[1]) ] += 1
      else:
        occ_histogram[ int(row[1]) ] += 1
  return occ_histogram

def amp_hist( filename, nbit, no_tp=False, tp_start=248 ,tp_stop=260 ):
  amp_histogram = [0] * (2**int(nbit))
  with open( filename ) as f:
    for row in csv.reader( f ):
      if no_tp == True:
        if int(row[1]) < tp_start or int(row[1]) > tp_stop:
          amp_histogram[ int(row[2]) ] += 1
      else:
        amp_histogram[ int(row[2]) ] += 1
  return amp_histogram

def pos_hist( filename, NSAMP=30, no_tp=False, tp_start=248 ,tp_stop=260 ):
  pos_histogram = [0] * NSAMP
  with open( filename ) as f:
    for row in csv.reader( f ):
      if no_tp == True:
        if int(row[1]) < tp_start or int(row[1]) > tp_stop:
          pos_histogram[ int(row[3]) ] += 1
      else:
        pos_histogram[ int(row[3]) ] += 1
  return pos_histogram

def read_pulses( filename, no_tp=False, tp_start=248 ,tp_stop=260 ):
  """
  filename: pulse object csv file
  """
  pulses = []
  with open( filename ) as f:
    for row in csv.reader( f ):
      if no_tp == True:
        if int(row[1]) < tp_start or int(row[1]) > tp_stop:
          pos_histogram[ int(row[3]) ] += 1
      else:
        pls = p.pulse( orbit=int(row[0]), bx=int(row[1]), amplitude=int(row[2]), position=int(row[3]), tot=0 )
        pls.tot = int( row[4] ) if isinstance(row[4], int) else 0
        pulses.append( pls )
  return pulses
  
def recon( filename, pulses, raw_orb_size=((3564*30)) ): #-3672
  """
  filename: raw data file
  pulses: pulses list
  """
  orb_cnt = 0
  with open( filename, "rb") as f:
    for byte_list in read_binary( f, raw_orb_size ):
      orb_cnt += 1
      data = [ struct.unpack( 'B', byte_list[i] )[0] for i in range(raw_orb_size) ]
      plt.plot( data )
      indices = [ i for i, pulse in enumerate(pulses) if pulse.orbit == orb_cnt ]
      positions = [ (pulses[i].bx * 30)-120 + pulses[i].position for i in indices ]
      # positions = [ (pulses[i].bx * 30) for i in indices ]
      amplitudes = [ pulses[i].amplitude for i in indices ]
      plt.plot( positions, amplitudes, 'o' )
      plt.show()

def snrd( in_data, win_size=7 ):
  if win_size not in [5, 7, 9]:
    raise ValueError("win_size wrong, has to be one of [5,7,9]")
  if len(in_data) < win_size:
    raise ValueError("Not enough input samples for that win_size")
  wing = (win_size - 1) / 2
  len_data = len( in_data )
  deriv = [0] * wing
  for x in range( wing, len_data - wing ):
    if win_size == 5:
      snrd = ( 2 * ( in_data[x+1] - in_data[x-1] ) + in_data[x+2] - in_data[x-2] ) / 4 #8
    elif win_size == 7:
      snrd = ( 5 * ( in_data[x+1] - in_data[x-1] ) + 4 * ( in_data[x+2] - in_data[x-2] ) + in_data[x+3] - in_data[x-3] ) / 4 #32
    elif win_size == 9:
      snrd = ( 14 * ( in_data[x+1] - in_data[x-1] ) + 14 * ( in_data[x+2] - in_data[x-2] ) + 6 * ( in_data[x+3] - in_data[x-3] ) + in_data[x+4] - in_data[x-4] ) / 4 #128
    else:
      raise ValueError("Unallowed win_size")
    deriv.append( snrd )
  deriv.extend( [0] * wing )
  return deriv

