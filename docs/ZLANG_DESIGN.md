# ZLang Design Notes

ZTPU uses typed ZLang constructs across the accelerator hierarchy.

## Datapaths

- Fixed-point arithmetic and saturation:
  [`src/arithmetic.zhl`](../src/arithmetic.zhl) and
  [`src/fxp_math.zhl`](../src/fxp_math.zhl).
- Generic processing elements and vectorized systolic arrays:
  [`src/pe.zhl`](../src/pe.zhl) and [`src/mxu.zhl`](../src/mxu.zhl).
- 2x2 and 4x4 matrix-engine configurations:
  [`src/ub_mxu_compute.zhl`](../src/ub_mxu_compute.zhl).

## State and Storage

- FSM control for DMA and compute engines:
  [`src/ub_dma.zhl`](../src/ub_dma.zhl),
  [`src/layout_dma_core.zhl`](../src/layout_dma_core.zhl), and
  [`src/ub_adam.zhl`](../src/ub_adam.zhl).
- Banked RAM, compile-time LUT generation, FIFOs, and completion storage:
  [`src/ub.zhl`](../src/ub.zhl),
  [`src/fixed_luts.zhl`](../src/fixed_luts.zhl), and
  [`src/storage.zhl`](../src/storage.zhl).

## Interfaces

- Ready/valid streams and AXI interfaces:
  [`src/ub_stream.zhl`](../src/ub_stream.zhl) and
  [`src/axi_arbiter.zhl`](../src/axi_arbiter.zhl).
- AXI4 external interface:
  [`src/layout_dma_axi4.zhl`](../src/layout_dma_axi4.zhl).
- CSR banks and AHB-Lite/APB register-bus bridges:
  [`src/cfgbus.zhl`](../src/cfgbus.zhl).
- Fence configuration and shared AXI arbitration:
  [`src/queued_q16_ahb_top.zhl`](../src/queued_q16_ahb_top.zhl).

## Verification Flow

```text
ZLang source -> semantic checks -> SystemVerilog -> Verilator
            \-> native simulator
            \-> formal properties
```

`tools/simulator_diff.py` applies the same event sequence to the native
simulator and generated SystemVerilog, then compares outputs after each event.
Formal scope is documented in
[`FORMAL_VERIFICATION.md`](FORMAL_VERIFICATION.md).
