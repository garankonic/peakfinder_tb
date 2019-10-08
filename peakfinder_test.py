import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer, RisingEdge, ReadOnly
from cocotb.regression import TestFactory
import math
import struct
import peakfinder_utils as pfu
import pulse as p

class PeakfinderTB( object ):
  """
  Implementing all necessary tools to run raw data through a peak finder VHDL module and saving the detected pulses in a file.
  Need to implement a <peakfinder>_producer for each desired peak finder, which produces pulse() objects for the detected pulses.
  Peak finder module must have:
    - Generic "NSAMPLES", specifying number of samples per bx
    - Bunch clock input for clocking in NSAMPLES per bx
    - Input port "samples", NSAMPLES wide
  """

  def __init__( self, dut ):
    # Device under test
    self.dut = dut
    # Number of samples per bx
    self.NSAMP = int(self.dut.NSAMPLES)
    # No. of bx per orbit
    self.orb_size = 3564
    # Raw data orbit is <orb_excess> samples longer than normal orbit (firmware specific)
    self.orb_excess = 3672
    # Size of a raw data orbit in samples
    self.raw_orb_size = ( self.orb_size * self.NSAMP ) + self.orb_excess
    # Orbit counter
    self.orb_cnt = 0
    # Bunch clock counter
    self.bx_cnt = 0
    # List with all detected pulses
    self.pulses = []
    # Consecutive hits (in neighbouring bx)
    self.consec_cnt = 0

  @cocotb.coroutine
  def reset( self, clk, rst, duration=10000  ):
    """
    Basic resetting routine.
    """
    self.dut._log.info(pfu.string_color("Resetting DUT.", "blue"))
    rst <= 1
    yield Timer(duration)
    yield RisingEdge( clk )
    rst <= 0
    self.dut._log.info(pfu.string_color("Reset complete.", "blue"))

  @cocotb.coroutine
  def drive_samples( self, clk, input_signal, data ):
    """
    Feeding data into samples input, one bx at a time.
    """
    # with open( filepath, "rb") as f:
      # for byte_list in pfu.read_binary( f, self.raw_orb_size ):
      #   self.orb_cnt += 1
      #   if iter_max>0 and self.orb_cnt > iter_max: break
      #   self.dut._log.info(pfu.string_color("Orbit " + str(self.orb_cnt), "blue"))
      #   # struct.unpack: Convert one orbit of binary data into list of uint8 samples
      #   data = [ struct.unpack( 'B', byte_list[i] )[0] for i in range(self.raw_orb_size - 3672) ]
    for bx in range( len(data) / self.NSAMP ):
      self.bx_cnt = bx
      self.dut.samples = data[ (bx*self.NSAMP) : (bx*self.NSAMP)+self.NSAMP ]
      yield RisingEdge( clk )

  @cocotb.coroutine
  def prallel_producer( self ):
    """
    Registering detected pulses for the
    parallel_analyzer.vhd peak finder.
    Function yields for a rising edge in detected peaks and
    then checks if still asserted in next bx to count consecutive bx peaks.
    TODO: Yield for something else than rising edge in the first place
    """
    while True:
      yield [ RisingEdge(self.dut.peaks[i]) for i in range(self.NSAMP) ]
      yield ReadOnly()
      detected_pulse = p.pulse( orbit=self.orb_cnt, bx=self.bx_cnt, amplitude=int(self.dut.local_maximum), position=int(math.log(int(self.dut.peaks),2)), tot=int(self.dut.time_over_threshold) )
      self.pulses.append( detected_pulse )
      trig = True
      while trig:
        yield RisingEdge( self.dut.bunch_clk )
        yield ReadOnly()
        if int(self.dut.peaks) > 0:
          # self.dut._log.info( pfu.string_color("CONSECUTIVE", "yellow") )
          self.consec_cnt += 1
          detected_pulse = p.pulse( orbit=self.orb_cnt, bx=self.bx_cnt, amplitude=int(self.dut.local_maximum), position=int(math.log(int(self.dut.peaks),2)), tot=int(self.dut.time_over_threshold) )
          self.pulses.append( detected_pulse )
          trig = True
        else:
          trig = False

  @cocotb.coroutine
  def derivative_producer( self ):
    """
    Registering detected pulses for the
    derivative_peakfinder.vhd peak finder.
    TODO: Yield for something else than rising edge.
    TODO: "No coroutines waiting on trigger that fired: RisingEdge(peaks(1))" -> solved with yielding to ReadOnly after RisingEdge
    """
    while True:
      yield [ RisingEdge(self.dut.peaks[i]) for i in range(self.dut.NPEAKSMAX) ]
      yield ReadOnly()
      if self.dut.peaks==3 or self.dut.peaks==5 or self.dut.peaks==6 or self.dut.peaks==7:
        self.dut._log.info( pfu.string_color("Dobule Pulse!", "yellow") )
      for i in range( self.dut.NPEAKSMAX ):
        detected_pulse = p.pulse( orbit=self.orb_cnt, bx=self.bx_cnt, amplitude=int(self.dut.peaks_val[i]), position=int(self.dut.peaks_pos[i]), tot=None )
        self.pulses.append( detected_pulse )
      trig = True
      while trig:
        yield RisingEdge( self.dut.clk )
        yield ReadOnly()
        if int(self.dut.peaks) > 0:
          for i in range( self.dut.NPEAKSMAX ):
            if self.dut.peaks[i]:
              # self.dut._log.info( pfu.string_color("CONSECUTIVE", "yellow") )
              self.consec_cnt += 1
              detected_pulse = p.pulse( orbit=self.orb_cnt, bx=self.bx_cnt, amplitude=int(self.dut.peaks_val[i]), position=int(self.dut.peaks_pos[i]), tot=None )
              self.pulses.append( detected_pulse )
          trig = True
        else:
          trig = False

  def simulation_producer( self, data ):
    for i, d in enumerate( data ):
      if d < THR:
        prev = False
        continue
      elif d > THR and prev == True:
        
        prev = True
      
      if prev == True:


    # derivative = pfu.snrd( data, 7 )




###############################
## TEST FUNCTIONS
###############################

@cocotb.test()
def derivative_model( dut )


@cocotb.test()
def parallel_test( dut, iter_max=2 ):
  """
  Parallel_analyzer.vhd basic test function
  """
  tb = PeakfinderTB( dut )
  # Setting thresholds
  dut._log.info(pfu.string_color("Setting thresholds.", "blue"))
  level_threshold = 130
  tot_threshold = 3
  dut.level_threshold <= level_threshold
  dut.tot_threshold <= tot_threshold
  # Start
  dut.enabled <= 1
  cocotb.fork( Clock(dut.bunch_clk, 30000, 'ps').start() )
  yield tb.reset( dut.bunch_clk, dut.srst )
  cocotb.fork( tb.prallel_producer() )
  filename = "crate1.amc1_chA"
  raw_data_path = "/home/bril_firmware/Documents/peakfindertb/raw_data/"
  filepath = raw_data_path + "stable_1000orbits_bcm1f." + filename + ".bin"
  # Read file
  with open( filepath, "rb") as f:
    for byte_list in pfu.read_binary( f, tb.raw_orb_size ):
      tb.orb_cnt += 1
      if iter_max>0 and tb.orb_cnt > iter_max: break
      data = [ struct.unpack( 'B', byte_list[i] )[0] for i in range(tb.raw_orb_size - 3672) ]
      # Feed data
      yield tb.drive_samples( clk=dut.bunch_clk, input_signal=dut.samples, data=data )

  dut._log.info( pfu.string_color("Quick stat: Detected ", "green") + pfu.string_color( str(len(tb.pulses)), "yellow") + pfu.string_color(" pulses", "green") )
  dut._log.info( pfu.string_color("Out of which ", "green") + pfu.string_color( str(tb.consec_cnt), "yellow") + pfu.string_color(" were consecutive.", "green") )
  pfu.write_pulses( "../results/PARALLELTEST"+filename+"_lvlthr"+str(level_threshold)+"_totthr"+str(tot_threshold), tb.pulses )

@cocotb.test()
def derivative_test( dut, iter_max=2 ):
  """
  Parallel_analyzer.vhd basic test function
  """
  tb = PeakfinderTB( dut )
  # Setting thresholds
  dut._log.info(pfu.string_color("Setting thresholds.", "blue"))
  TOP = 3
  deriv_thr = 15
  val_thr = 40
  dut.TOP = TOP
  dut.deriv_thr <= deriv_thr
  dut.val_thr <= val_thr
  # Start
  dut._log.info(pfu.string_color("Starting bunch clock.", "blue"))
  cocotb.fork( Clock(dut.clk, 30000, 'ps').start() )
  yield tb.reset( dut.clk, dut.rst )
  cocotb.fork( tb.derivative_producer() )
  filename = "crate1.amc1_chC"
  raw_data_path = "/home/bril_firmware/Documents/peakfindertb/raw_data/"
  filepath = raw_data_path + "stable_1000orbits_bcm1f." + filename + ".bin"
  with open( filepath, "rb") as f:
    for byte_list in pfu.read_binary( f, tb.raw_orb_size ):
      tb.orb_cnt += 1
      if iter_max>0 and tb.orb_cnt > iter_max: break
      data = [ struct.unpack( 'B', byte_list[i] )[0] for i in range(tb.raw_orb_size - 3672) ]
      # Feed data
      yield tb.drive_samples( clk=dut.clk, input_signal=dut.samples, data=data )

  dut._log.info( pfu.string_color("Quick stat: Detected ", "green") + pfu.string_color( str(len(tb.pulses)), "yellow") + pfu.string_color(" pulses", "green") )
  pfu.write_pulses( "../results/DERIVATIVETEST"+filename+"_deriv_thr"+str(deriv_thr)+"_val_thr"+str(val_thr), tb.pulses )





# ###########################
# # Specify permutations
# # and generate the tests
# ###########################
# factory = TestFactory(run_test)
# factory.add_option("filename",
#                    ["crate1.amc1_chA", "crate1.amc1_chC", "crate1.amc2_chA", "crate1.amc2_chC", "crate2.amc1_chA", "crate2.amc1_chC", "crate2.amc2_chA", "crate2.amc2_chC"])
# factory.add_option("level_threshold",
#                    [130,132,134,136,140,142])
# factory.add_option("tot_threshold",
#                    [2, 3, 4])
# factory.generate_tests()
