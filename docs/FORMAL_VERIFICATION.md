# Formal Verification

ZTPU uses ZLang's source-level properties for a focused control and safety
suite. These checks complement simulation; they are not a claim that the full
accelerator or its numerical algorithms have been proven.

## Scope

The machine-readable target list is
[`contracts/formal_targets.json`](../contracts/formal_targets.json). The
current suite verifies:

- completion-queue occupancy, ready/valid consistency, capacity reachability,
  and overflow reachability;
- the invariant that a recorded repeated DMA fence fault implies a valid first
  fault;
- read/write fence rejection isolation, fault qualification, and generated
  error responses.

All named safety properties require an unbounded `proven` result. Covers must
be witnessed at the target's recorded bounded depth. A23 also generates and
proves applicable register-safety obligations.

## Direct ZLang Use

The compiler discovers `zlang.toml` and the committed `zlang.lock` while
walking up from the source file. The `portable` profile is selected from the
manifest; no Makefile participates in this command.

```bash
mkdir -p build/formal
.venv/bin/zlang src/storage.zhl \
  --top ZtpuCompletionQueue8 \
  --profile portable \
  --verify --verify-require proven \
  --formal-depth 16 --formal-timeout 90 \
  --verification-work-dir build/formal/work/completion_queue \
  --verification-report build/formal/completion_queue.json \
  --verification-format json \
  --verification-bundle build/formal/bundles/completion_queue \
  --contracts-sva build/formal/sva/completion_queue.sv
```

Replay the immutable bundle independently of ZLang source compilation:

```bash
.venv/bin/zlang verify build/formal/bundles/completion_queue \
  --mode prove --depth 16 --timeout 90 \
  --work-dir build/formal/replay/completion_queue
```

SymbiYosys, Yosys, `yosys-smtbmc`, and Z3 must be on `PATH`. Production
SystemVerilog does not contain the formal gates; properties are lowered only
into the verification artifact or optional bindable SVA output.

## Complete Suite

The suite runner executes every target, validates each result, and writes
reports, bundles, work directories, and SVA under ignored `build/formal/`:

```bash
.venv/bin/python tools/formal_verify.py
```

The Makefile also provides a `formal` target for CI.

## Limits

The initial suite does not prove AXI liveness, end-to-end command completion,
arithmetic equivalence, VMU transcendental error bounds, or complete workload
execution. These are covered by simulation tests. Future properties should
state protocol assumptions and distinguish bounded liveness from unbounded
safety.
