# Changelog

## 0.1.0-alpha.1 - 2026-10-14

- Initial ZLang HDL release.
- Added queued Q16 execution for DMA, layout, MXU, VMU, and ADAM operations.
- Added AHB-Lite and APB configuration interfaces, AXI fencing and arbitration,
  completion handling, IRQ, and performance counters.
- Added experimental Q8 and W4A8 static-weight modes.
- Added ZLang native-simulator and generated-SystemVerilog tests.
- Added formal checks for the completion queue, DMA fault state, and AXI fences.
- Pinned ZLang HDL `v0.1.0a23`.
