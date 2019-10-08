class pulse( object ):
  """
  The pulse() class is describing a detected pulse (event).
  orbit: Orbit number
  bx: Bunch crossing number of respective orbit.
  amplitude: Pulse amplitude (peak value)
  position: Pulse/peak position within bx
  tot: Time over Threshold
  """
  def __init__( self, orbit, bx, amplitude, position, tot ):
    self.orbit = orbit
    self.bx = bx
    self.amplitude = amplitude
    self.position = position
    self.tot = tot
