##

UBCM_PATH = ~/Documents/ubcm/fw/fpga/src
UBCM_MODULES = $(UBCM_PATH)/user/modules
COCOTB = ~/Documents/cocotb

COCOTB_LOG_LEVEL = ERROR
COCOTB_REDUCED_LOG_FMT = ERROR

SIM = questa
TOPLEVEL_LANG = vhdl

# COCOTB_ANSI_OUTPUT=1
GHDL_ARGS= -P/home/bril_firmware/Documents/compxlib64/unisim

MODULE = peakfinder_test

ifeq ($(TESTCASE),derivative_test)
	TOPLEVEL = derivative_peakfinder
else ifeq ($(TESTCASE),parallel_test)
	TOPLEVEL = parallel_analyzer
else
    $(error "Did not find TESTCASE=$(TESTCASE)")
endif

# Source files have to be specified in the correct compiled
# Which means packages first
# Dont forget to include the Unisim path in the modelsim.ini
# Design Resources
ifeq ($(TOPLEVEL),derivative_peakfinder)
    VHDL_SOURCES = 	$(UBCM_MODULES)/peakfinder/peakfinder_pkg.vhd \
					$(UBCM_PATH)/user/usr_bcm1f/data_package.vhd \
					$(UBCM_PATH)/user/usr_bcm1f/functions_package.vhd \
					$(UBCM_PATH)/user/usr_bcm1f/user_package_basic.vhd \
					$(UBCM_PATH)/ipbus_core/hdl/ipbus_package.vhd \
					$(UBCM_MODULES)/peakfinder/adder.vhd \
					$(UBCM_MODULES)/peakfinder/subtractor.vhd \
					$(UBCM_MODULES)/peakfinder/m7_block.vhd \
					$(UBCM_MODULES)/peakfinder/diff_m7.vhd \
					$(UBCM_MODULES)/peakfinder/deriv_buffer.vhd \
					$(UBCM_MODULES)/peakfinder/integrator.vhd \
					$(UBCM_MODULES)/peakfinder/derivative_peakfinder.vhd
else ifeq ($(TOPLEVEL),parallel_analyzer)
	VHDL_SOURCES = 	$(UBCM_PATH)/user/usr_bcm1f/data_package.vhd \
					$(UBCM_PATH)/user/usr_bcm1f/functions_package.vhd \
					$(UBCM_PATH)/user/usr_bcm1f/user_package_basic.vhd \
					$(UBCM_MODULES)/peakfinder/parallel_analyzer.vhd
else
    $(error "No sources found for TOPLEVEL=$(TOPLEVEL)")
endif

## Specify simulation time step
# VSIM_ARGS=-t 1ns

include $(COCOTB)/makefiles/Makefile.inc
include $(COCOTB)/makefiles/Makefile.sim

