# ZTPU

A fixed-point hardware implementation of the compute path in Andrej
Karpathy's [MicroGPT](https://karpathy.github.io/2026/02/12/microgpt/), written
in [ZLang HDL](https://github.com/postoroniy/zlang-hdl).

MicroGPT expresses a small transformer in scalar Python. ZTPU implements its
matrix, vector, and optimizer operations as queued hardware engines sharing
a unified buffer. The single-file demo supplies character tokens, weights,
and queued commands, then samples generated names from hardware probabilities.

## Model Operations

| MicroGPT operation | ZTPU implementation |
| --- | --- |
| Linear projections and attention products | Tiled MXU matrix operations |
| RMSNorm, softmax, ReLU, residual arithmetic | Fixed-point VMU operations |
| Adam parameter updates | ADAM engine |
| Tensor and KV-cache movement | Unified buffer, layout engine, AXI DMA |

The main integration modules are `ZtpuQueuedQ16AhbTop` and
`ZtpuQueuedQ16AhbTop4x4` in
[`src/queued_q16_ahb_top.zhl`](src/queued_q16_ahb_top.zhl). They expose AHB-Lite
configuration, AXI memory ports, completion queues, interrupts, and counters.
The design supports 2x2 and 4x4 matrix tiles and 256-word or 1024-word buffers.

Q16 is the reference arithmetic. It is not bit-identical to MicroGPT's Python
floating-point calculations. Q8 and W4A8 static-weight modes are experimental.

## Run

Use Python 3.12 and ZLang HDL `0.1.0a24`. The commands below pin the compiler
source and its matching Linux x86-64 native simulator:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install \
  https://github.com/postoroniy/zlang-hdl/archive/85138c88bb818d4554a6ce6a5ef771501f751f90.tar.gz \
  'https://raw.githubusercontent.com/postoroniy/zlang-hdl/85138c88bb818d4554a6ce6a5ef771501f751f90/release/native-wheels/zlang_native_sim-0.1.0a24-cp312-abi3-manylinux_2_28_x86_64.whl#sha256=6e17c01f69fe39e2081fb7c4dcd73cc13c63e7dcd23d2803107b019a2df5c571'

zlang lock update --project zlang.toml
zlang src/queued_q16_ahb_top.zhl --top ZtpuQueuedQ16AhbTop \
  --profile portable --check
```

Run the MicroGPT demo:

```bash
python microgpt.py
```

The first run downloads the original names dataset and prepares a checkpoint
with 1,000 host-side floating-point training steps. Subsequent runs reuse the
cached checkpoint. Inference runs the existing queued Q16 MXU and VMU in
ZLang's native simulator, including causal attention, RMSNorm, ReLU, and
softmax. The host manages tokenization, cached K/V tensors, tensor movement,
and sampling; there is no software arithmetic fallback for inference.

The defaults follow MicroGPT: one layer, 16 embedding channels, four heads,
16 token positions, temperature 0.5, seed 42, and 20 generated names. Q16
rounding and lookup-table approximations change probabilities and sampled
names relative to the original floating-point program. This is cycle-level
hardware simulation, not real-time inference; the first native compilation
and generating 20 names can take substantial time.

For a smaller run or an offline dataset (one name per line):

```bash
python microgpt.py --samples 1
python microgpt.py --input input.txt --steps 100 --embd 4 --heads 1 \
  --block-size 8 --samples 1
```

To skip training and network access, reuse a checkpoint JSON from
`build/microgpt/`:

```bash
python microgpt.py --checkpoint build/microgpt/checkpoint-HASH.json --samples 1
```

The checkpoint contains `chars`, the model dimensions in `config`, and
row-major floating-point matrices in `state_dict` using MicroGPT's names
(`wte`, `wpe`, `lm_head`, `layer0.attn_wq`, and so on). Weights are quantized
once to Q16 before hardware execution. The simulation wrapper in
`src/microgpt_demo.zhl` adds bounded AXI memory and a host-loading port; it
does not add a new compute datapath or bypass the command queue.

Try the multiply-accumulate processing element (`3 * 4 + 5 = 17`):

```bash
zlang sim src/pe.zhl --top ZtpuPeQ16 --clock clk --cycles 1 \
  --set input_v=3 --set input_w=4 --set input_acc=5 --json
```

Generate SystemVerilog and check it with Verilator installed:

```bash
mkdir -p build
zlang src/queued_q16_ahb_top.zhl --top ZtpuQueuedQ16AhbTop \
  --profile portable --systemverilog build/ZtpuQueuedQ16AhbTop.sv \
  --verilator-lint
```

`zlang.toml` defines the project and `zlang.lock` records dependency resolution.
Generated output, downloaded data, and checkpoints stay in `build/`. No
pretrained weights, datasets, silicon results, or timing-closure claims are
included in the repository.

## License

PolyForm Noncommercial 1.0.0; see [LICENSE](LICENSE) and [NOTICE](NOTICE).
[Commercial licensing](COMMERCIAL-LICENSE.md) is available separately.
MicroGPT is the algorithmic reference; no upstream Python code is bundled.
