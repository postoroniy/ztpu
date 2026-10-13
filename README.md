# ZTPU

ZTPU is a TPU-style accelerator written in ZLang HDL. The design provides a
queued command path for tensor layout, memory transfer, matrix operations,
vector operations, and ADAM updates.

The main integration modules are `ZtpuQueuedQ16AhbTop` and
`ZtpuQueuedQ16AhbTop4x4` in
[`src/queued_q16_ahb_top.zhl`](src/queued_q16_ahb_top.zhl).

## Features

- Queued opcodes 1 through 8 for layout, UB DMA, MXU, VMU, ADAM, and strided
  DRAM copies.
- Exact Q16 matrix execution with 2x2 and 4x4 tiles.
- Experimental Q8 and W4A8 static-weight modes.
- VMU operations 0 through 14, including fixed-point softmax and RMSNorm.
- AHB-Lite and APB configuration interfaces.
- AXI4 DMA, address-range fences, arbitration, completion queues, IRQ, and
  performance counters.
- 256-word and 1024-word unified-buffer configurations.

Q16 is the functional correctness contract. Q8 and W4A8 are experimental and
do not replace Q16 validation.

## Architecture

```text
AHB-Lite or APB
       |
       v
CSR banks -> descriptor DMA -> command queue -> completion queue / IRQ
                                      |
             +------------------------+----------------------+
             |               |               |               |
          UB DMA             MXU             VMU             ADAM
             |               |               |               |
             +------------ unified buffer -------------------+
                                      |
                         AXI fences and arbiters
                                      |
                              external memory

Layout remapper / tiler -> Layout DMA -> shared AXI ports
```

The AHB-Lite interface uses ZLang's typed `AHBLite` protocol and
`AHBLiteToRegBus` bridge. Generated SystemVerilog exposes `ahb_H*` pins,
supports `HREADYOUT` stalls, and returns the standard two-cycle ERROR response.

## Toolchain

ZTPU 0.1.0-alpha.1 uses ZLang HDL `v0.1.0a23`:

- release: <https://github.com/postoroniy/zlang-hdl/releases/tag/v0.1.0a23>
- commit: `f773a89aa7ebfe3539b8834d339b072b35a0e562`
- compiler wheel SHA256:
  `f74e49f3c1b3a0cc9980d423b327f79c56e7376de48d9a9cff3de1d41d63a0f6`
- native simulator wheel SHA256:
  `e491a03fcb62d2c55b23bc904d3837a43b4a094fe91214cf5a308e1164006c97`

The complete pin is in [`contracts/toolchain.json`](contracts/toolchain.json).

## Build

Create a Python 3.12 virtual environment and install `pytest` and the two ZLang
wheels from the release above. Verilator is required for generated RTL checks;
some tests also use Icarus Verilog.

```bash
python3 -m venv .venv
.venv/bin/pip install pytest \
  https://github.com/postoroniy/zlang-hdl/releases/download/v0.1.0a23/zlang_hdl-0.1.0a23-py3-none-any.whl \
  https://github.com/postoroniy/zlang-hdl/releases/download/v0.1.0a23/zlang_native_sim-0.1.0a23-cp312-abi3-manylinux_2_28_x86_64.whl
```

Check the top-level design:

```bash
.venv/bin/zlang src/queued_q16_ahb_top.zhl \
  --top ZtpuQueuedQ16AhbTop --profile portable --check
```

Generate and lint SystemVerilog:

```bash
mkdir -p build
.venv/bin/zlang src/queued_q16_ahb_top.zhl \
  --top ZtpuQueuedQ16AhbTop --profile portable \
  --systemverilog build/ZtpuQueuedQ16AhbTop.sv --verilator-lint
```

Run the tests and simulator comparison:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python tools/simulator_diff.py
```

`zlang.toml` defines the source tree and implementation profile. `zlang.lock`
pins dependency resolution. Update the lock after changing dependencies:

```bash
.venv/bin/zlang lock update --project zlang.toml
git diff -- zlang.toml zlang.lock
```

Generated files are written below ignored `build/`; see
[`docs/GENERATED_OUTPUT.md`](docs/GENERATED_OUTPUT.md). Formal verification is
described in [`docs/FORMAL_VERIFICATION.md`](docs/FORMAL_VERIFICATION.md).

## Repository Layout

- `src/`: ZLang RTL.
- `contracts/`: interface, behavior, and toolchain definitions.
- `tests/`: functional and generated-SystemVerilog tests.
- `tools/`: simulation, formal, and release utilities.
- `docs/`: design, verification, and licensing notes.

## Release Scope

- This alpha release is intended for evaluation and experimentation.
- No timing-closure, silicon, TOPS, synthesis, PnR, or GDS result is claimed.
- No pretrained weights or datasets are included.
- Q8 and W4A8 support is limited to the documented static-weight paths.

## License

ZTPU is available under the PolyForm Noncommercial License 1.0.0. Commercial
use requires a separate license. ZLang HDL is an independent Apache-2.0
project. See [`docs/LICENSING.md`](docs/LICENSING.md) and
[`COMMERCIAL-LICENSE.md`](COMMERCIAL-LICENSE.md).
