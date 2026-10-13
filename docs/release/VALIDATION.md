# Validation

Validation completed on 2026-10-14.

| Component | Version or result |
| --- | --- |
| ZLang HDL | `0.1.0a23` |
| ZLang commit | `f773a89aa7ebfe3539b8834d339b072b35a0e562` |
| Python | 3.12.3 |
| pytest | 9.1.1 |
| Verilator | 5.053 development build (`v5.052-258-ga419e9157`) |
| Icarus Verilog | 14.0 development build |
| Functional suite | 56 passed |
| Formal suite | 46 safety properties proven; 6 covers reached |
| Native simulator vs Verilator | 2 scenarios; 22 and 54 events |

The simulator comparison applies the same event sequence to the ZLang native
simulator and generated SystemVerilog. It covers AHB configuration transfers
and queued UB DMA operation.

The formal suite covers the completion queue, DMA fence fault latch, and AXI
read/write fences. See [`../FORMAL_VERIFICATION.md`](../FORMAL_VERIFICATION.md)
for property scope and prerequisites.

Synthesis and physical implementation were not run for this release.
