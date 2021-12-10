ISE_DIR=/home/soft/Xilinx/14.7

#vlib glbl
#vlog -work glbl $ISE_DIR/ISE_DS/ISE/verilog/src/glbl.v

vlib unisim
vcom -work unisim $ISE_DIR/ISE_DS/ISE/vhdl/src/unisims/unisim_VCOMP.vhd
vcom -work unisim $ISE_DIR/ISE_DS/ISE/vhdl/src/unisims/unisim_VPKG.vhd
vcom -work unisim $ISE_DIR/ISE_DS/ISE/vhdl/src/unisims/primitive/DSP48E1.vhd