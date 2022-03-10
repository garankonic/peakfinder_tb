-- system libraries
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use work.data_package.all;
use work.ipbus.all;

-- arithmetic functions with Signed or Unsigned values
use IEEE.NUMERIC_STD.ALL;

-- port declaraion
entity derivative_peakfinder_wrapper is
  generic(
    NSAMPLES : natural := 30;
    NPEAKSMAX : natural := 3;
    NBINS : natural := 6
  );
  port(
    clk : in std_logic; -- bunch clk
    clk80 : in std_logic;
    rst : in std_logic;
    samples : in sample_array_t( 0 to NSAMPLES - 1 );
    peaks : out std_logic_vector( 0 to NPEAKSMAX - 1 );
    peaks_val : out uint12_array_t( 0 to NPEAKSMAX - 1 );
    peaks_pos : out uint16_array_t( 0 to NPEAKSMAX - 1 );
    peaks_bins : out std_logic_vector( 0 to NBINS - 1 );
    --
    ipb_rst : in std_logic;
    ipb_clk : in std_logic;
    ipb_mosi_i : in ipb_wbus;
    ipb_miso_o : out ipb_rbus
  );
end derivative_peakfinder_wrapper;

architecture rtl of derivative_peakfinder_wrapper is

    signal ipb_mosi_buf         : ipb_wbus;
    
begin

    -- peakfinder
    derivative_peakfinder_inst : entity work.derivative_peakfinder
    generic map (
        NSAMPLES    => NSAMPLES,
        NPEAKSMAX   => NPEAKSMAX,
        NBINS       => NBINS
    )
    port map (
        clk             => clk,
        clk80   => clk80,
        rst     => rst,
        samples => samples,
        peaks   => peaks,
        peaks_val   => peaks_val,
        peaks_pos   => peaks_pos,
        peaks_bins  => peaks_bins,
        --  => --,
        ipb_rst     => ipb_rst,
        ipb_clk     => ipb_clk,
        ipb_mosi_i  => ipb_mosi_buf,
        ipb_miso_o  => ipb_miso_o
    );

   -- needed for the riviera - it does not like records
   ipb_mosi_buf <= ipb_mosi_i when rising_edge(ipb_clk);

end rtl;

