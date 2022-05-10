import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer, RisingEdge, ReadOnly
from cocotb.regression import TestFactory
import math
import struct
import peakfinder_utils as pfu
import tables
import matplotlib.pyplot as plt

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
    self.NBINS = int(self.dut.NBINS)
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
    # Storing waveforms (buffer size is the actual latency of the peak with respect to the bx)
    self.deriv_buffer = pfu.RingBuffer(8 + 1)
    self.sample_buffer = pfu.RingBuffer(12 + 1)
    self.waveforms = []
    # reg map to be filled for exact tb
    self.reg_map = {}

  def input_process_ubcm(self):
    self.input_filename = "crate1.amc1_chA"
    raw_data_path = "/home/bril_firmware/Documents/peakfindertb/raw_data/"
    filepath = raw_data_path + "stable_1000orbits_bcm1f." + self.input_filename + ".bin"
    # Read file
    self._input_data = []
    with open(filepath, "rb") as self._input_file:
      for byte_list in pfu.read_binary(self._input_file, self.raw_orb_size):
        self._input_data.append( [struct.unpack('B', byte_list[i])[0] for i in range(self.raw_orb_size - self.orb_excess)] )

  def input_process_daq(self):
    self.input_filename = "daq_data"
    # process file with daq data
    daq_input = open("daq_input.dat", "r")
    daq_input_lines = daq_input.readlines()
    daq_input.close()
    daq_filepath = daq_input_lines[0][:-2]
    # read file
    self._input_data = []
    for line in daq_input_lines[1:]:
      if line[0] == "#":
        continue
      line_split = line.split(",")
      filename = line_split[0]
      runnum = int(line_split[1])
      lsnum = int(line_split[2])
      nbnum = int(line_split[3])
      channelid = int(line_split[4])
      h5file = tables.open_file(daq_filepath+"/"+filename, "r")
      if "/bcm1futcarawdata" in h5file:
        for row in h5file.get_node("/bcm1futcarawdata").iterrows():
          if row['algoid'] == 100 and row['runnum'] == runnum and row['lsnum'] == lsnum and row['nbnum'] == nbnum and row['channelid'] == channelid:
            self._input_data.append(row['data'][:(self.raw_orb_size - self.orb_excess)])
            break
      h5file.close()

  def input_process(self):
    #self.input_process_ubcm()
    self.input_process_daq()

  def input_get_next_orbit(self):
    if len(self._input_data) > 0:
      return self._input_data.pop(0)
    else:
      return []

  @cocotb.coroutine
  def reset( self, clk, rst, duration=10):
    """
    Basic resetting routine.
    """
    self.dut._log.info(pfu.string_color("Resetting DUT.", "blue"))
    rst.value = 1
    for i in range(duration):
      yield RisingEdge(clk)
    rst.value = 0
    for i in range(duration):
      yield RisingEdge(clk)
    self.dut._log.info(pfu.string_color("Reset complete.", "blue"))

  @cocotb.coroutine
  def drive_samples( self, clk, input_signal, data, plot = False ):
    """
    Feeding data into samples input, one bx at a time.
    """
    for bx in range( int (len(data) / self.NSAMP) ):
      self.bx_cnt = bx
      for i in range(self.NSAMP):
        self.dut.samples[i].value = int(data[ (bx*self.NSAMP) + i ])
      yield RisingEdge( clk )
    # plot if needed
    if plot:
      x = [number/self.NSAMP for number in list(range(self.raw_orb_size - self.orb_excess))]
      plt.plot(x, data)
      plt.show()

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
      detected_pulse = pfu.pulse( orbit=self.orb_cnt, bx=self.bx_cnt, amplitude=int(self.dut.local_maximum), position=int(math.log(int(self.dut.peaks),2)), tot=int(self.dut.time_over_threshold) )
      self.pulses.append( detected_pulse )
      trig = True
      while trig:
        yield RisingEdge( self.dut.bunch_clk )
        yield ReadOnly()
        if int(self.dut.peaks) > 0:
          # self.dut._log.info( pfu.string_color("CONSECUTIVE", "yellow") )
          self.consec_cnt += 1
          detected_pulse = pfu.pulse( orbit=self.orb_cnt, bx=self.bx_cnt, amplitude=int(self.dut.local_maximum), position=int(math.log(int(self.dut.peaks),2)), tot=int(self.dut.time_over_threshold) )
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
      yield RisingEdge(self.dut.clk)
      # store waveforms
      self.sample_buffer.append(self.dut.derivative_peakfinder_inst.samples.value)
      self.deriv_buffer.append(self.dut.derivative_peakfinder_inst.deriv_s.value)
      # peak detect
      if self.dut.peaks.value == 0:
        continue
      if self.dut.peaks==3 or self.dut.peaks==5 or self.dut.peaks==6 or self.dut.peaks==7:
        self.dut._log.info( pfu.string_color("Double Pulse!", "yellow") )
      for i in range( self.dut.NPEAKSMAX.value ):
        if int(self.dut.peaks[i].value) > 0:
          detected_pulse = pfu.pulse( orbit=self.orb_cnt, bx=self.bx_cnt, amplitude=int(self.dut.peaks_val[i]), position=int(self.dut.peaks_pos[i]), tot=None )
          self.pulses.append( detected_pulse )
      # append waveforms
      sample_converted = [x.integer for x in self.sample_buffer.get()[0]]
      self.waveforms.append(pfu.waveform(orbit=self.orb_cnt, bx=self.bx_cnt, type="sample", waveform=sample_converted))
      derivative_converted = [x.signed_integer for x in self.deriv_buffer.get()[0]]
      self.waveforms.append(pfu.waveform(orbit=self.orb_cnt, bx=self.bx_cnt, type="derivative", waveform=derivative_converted))
      trig = True
      while trig:
        yield RisingEdge( self.dut.clk )
        # store waveforms
        self.sample_buffer.append(self.dut.derivative_peakfinder_inst.samples.value)
        self.deriv_buffer.append(self.dut.derivative_peakfinder_inst.deriv_s.value)
        yield ReadOnly()
        if int(self.dut.peaks) > 0:
          for i in range( self.dut.NPEAKSMAX ):
            if self.dut.peaks[i]:
              # self.dut._log.info( pfu.string_color("CONSECUTIVE", "yellow") )
              self.consec_cnt += 1
              detected_pulse = pfu.pulse( orbit=self.orb_cnt, bx=self.bx_cnt, amplitude=int(self.dut.peaks_val[i]), position=int(self.dut.peaks_pos[i]), tot=None )
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
      #if prev == True:

    # derivative = pfu.snrd( data, 7 )

  def shiftToMask(self, mask, data):
    shift_val = 0
    mask_copy = mask
    while (mask_copy & 0x1 == 0):
      mask_copy = mask_copy >> 1
      shift_val += 1
    return (data << shift_val) & mask

  def shiftFromMask(self, mask, data):
    shift_val = 0
    mask_copy = mask
    while (mask_copy & 0x1 == 0):
      mask_copy = mask_copy >> 1
      shift_val += 1
    return (data & mask) >> shift_val

  @cocotb.coroutine
  def read(self, reg_name, applyMask=True):
    if not (reg_name in self.reg_map.keys()):
      raise ValueError("Failed IPbus read: unknown register")
      return []
    yield RisingEdge(self.dut.ipb_clk)
    self.dut.ipb_mosi_i.ipb_strobe.value = 1
    self.dut.ipb_mosi_i.ipb_write.value = 0
    self.dut.ipb_mosi_i.ipb_addr.value = int(self.reg_map[reg_name][0])
    self.dut.ipb_mosi_i.ipb_wdata.value = 0
    yield RisingEdge(self.dut.ipb_clk)
    res = self.shiftFromMask(self.reg_map[reg_name][1], int(self.dut.ipb_miso_o.ipb_rdata.value)) if applyMask else int(
      self.dut.ipb_miso_o.ipb_rdata.value)
    timeout = 0
    while (self.dut.ipb_miso_o.ipb_ack.value == 0):
      yield RisingEdge(self.dut.ipb_clk)
      res = self.shiftFromMask(self.reg_map[reg_name][1], int(self.dut.ipb_miso_o.ipb_rdata.value)) if applyMask else int(
        self.dut.ipb_miso_o.ipb_rdata.value)
      timeout += 1
      if timeout >= 10:
        raise RuntimeError("Failed IPbus read")
        break
    self.dut.ipb_mosi_i.ipb_strobe.value = 0
    self.dut.ipb_mosi_i.ipb_write.value = 0
    self.dut.ipb_mosi_i.ipb_addr.value = 0
    self.dut.ipb_mosi_i.ipb_wdata.value = 0
    self.dut.ipb_mosi_i._log.debug("Success IPbus read : %d" % (res))
    return [res]

  @cocotb.coroutine
  def write(self, reg_name, data):
    if not (reg_name in self.reg_map.keys()):
      raise ValueError("Failed IPbus write: unknown register")
      return [1]
    mask = self.reg_map[reg_name][1]
    data_to_write = self.shiftToMask(mask, data)
    if mask != 0xffffffff:
      current_value = yield self.read(reg_name, False)
      data_to_write |= (current_value[0] & ~mask)
    yield RisingEdge(self.dut.ipb_clk)
    self.dut.ipb_mosi_i.ipb_strobe.value = 1
    self.dut.ipb_mosi_i.ipb_write.value = 1
    self.dut.ipb_mosi_i.ipb_addr.value = int(self.reg_map[reg_name][0])
    self.dut.ipb_mosi_i.ipb_wdata.value = data_to_write
    yield RisingEdge(self.dut.ipb_clk)
    timeout = 0
    while (self.dut.ipb_miso_o.ipb_ack.value == 0):
      yield RisingEdge(self.dut.ipb_clk)
      timeout += 1
      if timeout >= 10:
        raise RuntimeError("Failed IPbus write")
        break
    self.dut.ipb_mosi_i.ipb_strobe.value = 0
    self.dut.ipb_mosi_i.ipb_write.value = 0
    self.dut.ipb_mosi_i.ipb_addr.value = 0
    self.dut.ipb_mosi_i.ipb_wdata.value = 0
    self.dut.ipb_mosi_i._log.debug("Success IPbus write")
    return [0]


###############################
## TEST FUNCTIONS
###############################
@cocotb.test()
def derivative_model( dut ):
  pass

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
  dut.level_threshold.value = level_threshold
  dut.tot_threshold.value = tot_threshold
  # Start
  dut.enabled.value = 1
  cocotb.fork( Clock(dut.clk, 25000, 'ps').start() )
  cocotb.fork(Clock(dut.clk80, 12500, 'ps').start())
  cocotb.fork(Clock(dut.ipb_clk, 32500, 'ps').start())
  yield tb.reset( dut.clk, dut.ipb_rst )
  yield tb.reset( dut.clk, dut.srst )
  cocotb.fork( tb.prallel_producer() )
  # process input
  tb.input_process()
  # inject
  while True:
    # count orbits
    tb.orb_cnt += 1
    if iter_max>0 and tb.orb_cnt > iter_max: break
    data = tb.input_get_next_orbit()
    if len(data) == 0: break
    # Feed data
    yield tb.drive_samples( clk=dut.clk, input_signal=dut.samples, data=data )

  dut._log.info( pfu.string_color("Quick stat: Detected ", "green") + pfu.string_color( str(len(tb.pulses)), "yellow") + pfu.string_color(" pulses", "green") )
  dut._log.info( pfu.string_color("Out of which ", "green") + pfu.string_color( str(tb.consec_cnt), "yellow") + pfu.string_color(" were consecutive.", "green") )
  pfu.write_pulses( "../results/PARALLELTEST"+tb.input_filename+"_lvlthr"+str(level_threshold)+"_totthr"+str(tot_threshold), tb.pulses )

@cocotb.test()
def derivative_test( dut, iter_max=2 ):
  """
  Parallel_analyzer.vhd basic test function
  """
  tb = PeakfinderTB( dut )
  # register map
  tb.reg_map["deriv_thr"] = (0x0, 0x00000FFF)
  tb.reg_map["top"] = (0x1, 0x0000000F)
  tb.reg_map["val_thr"] = (0x2, 0x00000FFF)
  tb.reg_map["bin_LUT_0"] = (0x3, 0xFFFFFFFF)
  tb.reg_map["bin_LUT_1"] = (0x4, 0xFFFFFFFF)
  tb.reg_map["bin_LUT_2"] = (0x5, 0xFFFFFFFF)
  # init ipb and samples
  dut.ipb_rst.value = 1
  dut.rst.value = 1
  dut.ipb_mosi_i.ipb_strobe.value = 0
  dut.ipb_mosi_i.ipb_write.value = 0
  dut.ipb_mosi_i.ipb_addr.value = 0
  dut.ipb_mosi_i.ipb_wdata.value = 0
  for i in range(tb.NSAMP):
    dut.samples[i].value = 0
  # Setting thresholds
  dut._log.info(pfu.string_color("Setting thresholds.", "blue"))
  top = 1
  deriv_thr = 2
  val_thr = 40
  # Bin LUTs
  lut = [int((i * tb.NBINS) / tb.NSAMP) for i in range(tb.NSAMP)]
  lut_0 = 0
  lut_1 = 0
  lut_2 = 0
  for i in range(10):
    lut_0 |= lut[i] << 3 * i
    lut_1 |= lut[i + 10] << 3 * i
    lut_2 |= lut[i + 20] << 3 * i
  # Start
  dut._log.info(pfu.string_color("Starting bunch clock.", "blue"))
  cocotb.fork(Clock(dut.clk, 25000, 'ps').start())
  cocotb.fork(Clock(dut.clk80, 12500, 'ps').start())
  cocotb.fork(Clock(dut.ipb_clk, 32500, 'ps').start())
  yield tb.reset(dut.clk, dut.ipb_rst)
  yield tb.reset(dut.clk, dut.rst)
  # now write ipbus registers
  yield tb.write("top", top)
  yield tb.write("deriv_thr", deriv_thr)
  yield tb.write("val_thr", val_thr)
  yield tb.write("bin_LUT_0", lut_0)
  yield tb.write("bin_LUT_1", lut_1)
  yield tb.write("bin_LUT_2", lut_2)
  # run producer
  cocotb.fork( tb.derivative_producer() )
  # process input
  tb.input_process()
  # inject
  while True:
    # count orbits
    tb.orb_cnt += 1
    if iter_max > 0 and tb.orb_cnt > iter_max: break
    data = tb.input_get_next_orbit()
    if len(data) == 0: break
    # Feed data
    yield tb.drive_samples(clk=dut.clk, input_signal=dut.samples, data=data)

  dut._log.info("Quick stat: Detected " + str(len(tb.pulses)) + " pulses")
  pfu.write_pulses( "../results/DERIVATIVETEST"+tb.input_filename+"_deriv_thr"+str(deriv_thr)+"_val_thr"+str(val_thr), tb.pulses, tb.waveforms )





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
