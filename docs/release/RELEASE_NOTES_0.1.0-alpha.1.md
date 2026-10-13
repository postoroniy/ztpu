# ZTPU 0.1.0-alpha.1

First source release of the ZLang HDL implementation of ZTPU.

## Included

- Queued Q16 execution through UB DMA, MXU, VMU, ADAM, and layout DMA.
- 2x2 and 4x4 exact-Q16 matrix paths.
- Experimental Q8 and W4A8 static-weight modes.
- AHB-Lite and APB configuration interfaces.
- AXI fencing, arbitration, completion handling, IRQ, and counters.
- ZLang native-simulator and Verilator comparison tests.
- Formal safety checks for control and DMA-fence modules.

## Toolchain

The release is pinned to ZLang HDL `v0.1.0a23`. Exact revisions and package
hashes are listed in `contracts/toolchain.json`.

## Scope

- Q16 is the functional correctness contract.
- Q8 and W4A8 are experimental modes.
- Pretrained models and datasets are not included.
- Synthesis, FPGA timing, physical design, silicon, and TOPS results are not
  included.
- Generated SystemVerilog is built locally and is not part of the source
  archive.
