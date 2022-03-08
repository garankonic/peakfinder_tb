##
# UBCM_PATH environment variable has to be set

UBCM_FW_SRC = $(UBCM_PATH)/fw/fpga/src
UBCM_MODULES = $(UBCM_FW_SRC)/user/modules

SIM = riviera
TOPLEVEL_LANG = vhdl
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
					$(UBCM_FW_SRC)/user/usr_bcm1f/data_package.vhd \
					$(UBCM_FW_SRC)/user/usr_bcm1f/functions_package.vhd \
					$(UBCM_FW_SRC)/user/usr_bcm1f/user_package_basic.vhd \
					$(UBCM_FW_SRC)/ipbus_core/hdl/ipbus_package.vhd \
					$(UBCM_MODULES)/peakfinder/adder.vhd \
					$(UBCM_MODULES)/peakfinder/subtractor.vhd \
					$(UBCM_MODULES)/peakfinder/m7_block.vhd \
					$(UBCM_MODULES)/peakfinder/diff_m7.vhd \
					$(UBCM_MODULES)/peakfinder/deriv_buffer.vhd \
					$(UBCM_MODULES)/peakfinder/integrator.vhd \
					$(UBCM_MODULES)/peakfinder/derivative_peakfinder.vhd
else ifeq ($(TOPLEVEL),parallel_analyzer)
	VHDL_SOURCES = 	$(UBCM_FW_SRC)/user/usr_bcm1f/data_package.vhd \
					$(UBCM_FW_SRC)/user/usr_bcm1f/functions_package.vhd \
					$(UBCM_FW_SRC)/user/usr_bcm1f/user_package_basic.vhd \
					$(UBCM_MODULES)/peakfinder/parallel_analyzer.vhd
else
    $(error "No sources found for TOPLEVEL=$(TOPLEVEL)")
endif

## Specify simulation time step
ifeq ($(SIM),riviera)
    ACOM_ARGS = -2002
else ifeq ($(SIM),modelsim)
    VSIM_ARGS = -t 1ps
endif

# include sim
include $(shell cocotb-config --makefiles)/Makefile.sim

