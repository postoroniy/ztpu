# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Character-level MicroGPT: host checkpoint preparation, ZLang Q16 inference.

Algorithmic reference: https://karpathy.github.io/2026/02/12/microgpt/
Only the host trainer uses floating point. Inference arithmetic runs through
the existing ZTPU command queue, MXU, VMU, unified buffer, and AXI DMA.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import sys
from time import perf_counter
from urllib.request import urlopen

ONE = 1 << 16
ROOT = Path(__file__).resolve().parent
NAMES_URL = "https://raw.githubusercontent.com/karpathy/makemore/master/names.txt"


class Value:
    """Scalar reverse-mode differentiation for checkpoint preparation only."""

    __slots__ = ("data", "grad", "parents")

    def __init__(self, data, parents=()):
        self.data, self.grad, self.parents = float(data), 0.0, parents

    def __add__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        return Value(self.data + other.data, ((self, 1.0), (other, 1.0)))

    def __mul__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        return Value(self.data * other.data, ((self, other.data), (other, self.data)))

    def __pow__(self, power):
        return Value(self.data ** power, ((self, power * self.data ** (power - 1)),))

    __radd__ = __add__
    __rmul__ = __mul__

    def __neg__(self):
        return self * -1

    def __sub__(self, other):
        return self + (-other)

    def __truediv__(self, other):
        return self * (other ** -1)

    def exp(self):
        value = math.exp(self.data)
        return Value(value, ((self, value),))

    def log(self):
        return Value(math.log(self.data), ((self, 1 / self.data),))

    def relu(self):
        return Value(max(0.0, self.data), ((self, float(self.data > 0)),))

    def backward(self):
        order, seen = [], set()

        def visit(node):
            if node not in seen:
                seen.add(node)
                for parent, _ in node.parents:
                    visit(parent)
                order.append(node)

        visit(self)
        self.grad = 1.0
        for node in reversed(order):
            for parent, derivative in node.parents:
                parent.grad += node.grad * derivative


def model_shapes(config, vocab):
    n, block = config["n_embd"], config["block_size"]
    return {"wte": (vocab, n), "wpe": (block, n), "lm_head": (vocab, n),
            "layer0.attn_wq": (n, n), "layer0.attn_wk": (n, n),
            "layer0.attn_wv": (n, n), "layer0.attn_wo": (n, n),
            "layer0.mlp_fc1": (4 * n, n), "layer0.mlp_fc2": (n, 4 * n)}


def float_step(weights, config, token, position, keys, values):
    """Training graph with the original causal attention/RMSNorm/ReLU model."""
    def linear(x, name):
        return [sum(a * b for a, b in zip(row, x)) for row in weights[name]]

    def norm(x):
        scale = (sum(v * v for v in x) / len(x) + 1e-5) ** -0.5
        return [v * scale for v in x]

    x = norm([a + b for a, b in zip(weights["wte"][token], weights["wpe"][position])])
    residual, normalized = x, norm(x)
    q, k, v = [linear(normalized, "layer0.attn_w" + part) for part in "qkv"]
    keys.append(k)
    values.append(v)
    head_dim = config["n_embd"] // config["n_head"]
    attention = []
    for head in range(config["n_head"]):
        start = head * head_dim
        scores = [sum(q[start + j] * key[start + j] for j in range(head_dim))
                  / math.sqrt(head_dim) for key in keys]
        probs = float_softmax(scores)
        attention.extend(sum(p * value[start + j] for p, value in zip(probs, values))
                         for j in range(head_dim))
    x = [a + b for a, b in zip(linear(attention, "layer0.attn_wo"), residual)]
    residual = x
    hidden = [v.relu() for v in linear(norm(x), "layer0.mlp_fc1")]
    x = [a + b for a, b in zip(linear(hidden, "layer0.mlp_fc2"), residual)]
    return linear(x, "lm_head")


def float_softmax(logits):
    largest = max(v.data for v in logits)
    exps = [(v - largest).exp() for v in logits]
    total = sum(exps)
    return [v / total for v in exps]


def train_checkpoint(text, config, steps, seed):
    docs = [line.strip() for line in text.splitlines() if line.strip()]
    if not docs:
        raise ValueError("input must contain at least one nonempty document")
    chars = sorted(set("".join(docs)))
    if len(chars) > 63:
        raise ValueError("this demo supports at most 63 characters plus BOS")
    rng = random.Random(seed)
    rng.shuffle(docs)
    weights = {name: [[Value(rng.gauss(0, 0.08)) for _ in range(cols)]
                      for _ in range(rows)]
               for name, (rows, cols) in model_shapes(config, len(chars) + 1).items()}
    params = [v for matrix in weights.values() for row in matrix for v in row]
    first, second = [0.0] * len(params), [0.0] * len(params)
    tokens = {char: i for i, char in enumerate(chars)}
    bos = len(chars)
    print(f"num docs: {len(docs)}\nvocab size: {bos + 1}\nnum params: {len(params)}", flush=True)
    for step in range(steps):
        sequence = [bos] + [tokens[c] for c in docs[step % len(docs)]] + [bos]
        length = min(config["block_size"], len(sequence) - 1)
        keys, values, losses = [], [], []
        for pos in range(length):
            probs = float_softmax(float_step(weights, config, sequence[pos], pos, keys, values))
            losses.append(-probs[sequence[pos + 1]].log())
        loss = sum(losses) / length
        loss.backward()
        for i, p in enumerate(params):
            first[i] = 0.85 * first[i] + 0.15 * p.grad
            second[i] = 0.99 * second[i] + 0.01 * p.grad ** 2
            m = first[i] / (1 - 0.85 ** (step + 1))
            v = second[i] / (1 - 0.99 ** (step + 1))
            p.data -= 0.01 * (1 - step / steps) * m / (math.sqrt(v) + 1e-8)
            p.grad = 0.0
        if step == 0 or (step + 1) % 100 == 0 or step + 1 == steps:
            print(f"step {step + 1:4d} / {steps:4d} | loss {loss.data:.4f}", flush=True)
    return {"format": "ztpu-microgpt-1", "config": config, "chars": chars,
            "state_dict": {name: [[p.data for p in row] for row in matrix]
                           for name, matrix in weights.items()},
            "training": {"steps": steps, "seed": seed,
                         "input_sha256": hashlib.sha256(text.encode()).hexdigest()},
            "random_state": rng.getstate()}


def validate_checkpoint(checkpoint):
    if not isinstance(checkpoint, dict) or checkpoint.get("format") != "ztpu-microgpt-1":
        raise ValueError("unsupported checkpoint format")
    config, chars = checkpoint["config"], checkpoint["chars"]
    n, heads, block = config["n_embd"], config["n_head"], config["block_size"]
    if any(type(v) is not int for v in (n, heads, block)) or config.get("n_layer", 1) != 1:
        raise ValueError("this demo requires one layer and integer model dimensions")
    if not (2 <= n <= 16 and 1 <= heads <= n and n % heads == 0 and 1 <= block <= 16):
        raise ValueError("require n_embd=2..16 divisible by n_head, block_size=1..16")
    if not chars or any(not isinstance(c, str) or len(c) != 1 for c in chars):
        raise ValueError("invalid character vocabulary")
    if len(chars) > 63 or chars != sorted(set(chars)):
        raise ValueError("invalid character vocabulary")
    shapes = model_shapes(config, len(chars) + 1)
    if set(checkpoint["state_dict"]) != set(shapes):
        raise ValueError("checkpoint must contain exactly the one-layer MicroGPT weights")
    for name, (rows, cols) in shapes.items():
        matrix = checkpoint["state_dict"][name]
        if len(matrix) != rows or any(len(row) != cols for row in matrix):
            raise ValueError(f"invalid shape for {name}")
        if any(not math.isfinite(v) or not -32768 <= v < 32768 for row in matrix for v in row):
            raise ValueError(f"invalid Q16 weight in {name}")


def q16(value):
    return max(-0x80000000, min(0x7fffffff, round(value * ONE)))


def signed(value):
    return value if value < 0x80000000 else value - 0x100000000


class Hardware:
    """No arithmetic fallback: every tensor operation uses queued RTL engines."""

    def __init__(self, checkpoint):
        from zlang import sim

        validate_checkpoint(checkpoint)
        print("Preparing ZLang native simulator...", file=sys.stderr, flush=True)
        program = sim.compile(ROOT / "src/microgpt_demo.zhl", top="ZtpuMicroGptDemo",
                              project=ROOT / "zlang.toml")
        self.machine = program.create()
        command_type = next(p.type for p in program.module.ports if p.name == "command")
        self.empty = {field.name: 0 for field in command_type.fields}
        self.machine.set("command", self.empty)
        self.machine.reset("rst", asserted=True)
        self.machine.tick("clk")
        self.machine.reset("rst", asserted=False)
        self.commands = 0
        self.config = checkpoint["config"]
        self.weights = {name: [[q16(v) for v in row] for row in matrix]
                        for name, matrix in checkpoint["state_dict"].items()}
        self.matrices = {}
        cursor = 0
        for name, matrix in self.weights.items():
            if name in ("wte", "wpe"):
                continue
            padded = matrix + ([[0] * len(matrix[0])] if len(matrix) % 2 else [])
            words = [v for row in padded for v in row]
            if cursor + 4 * len(words) > 0x7000:
                raise ValueError("model exceeds demo weight memory")
            self.upload(cursor, words)
            self.matrices[name] = (cursor, len(matrix), len(matrix[0]))
            cursor += 4 * len(words)

    def upload(self, address, words):
        if address % 4 or address < 0 or address + 4 * len(words) > 65536:
            raise ValueError("unaligned or out-of-range memory upload")
        self.machine.set("host_write", 1)
        for i, word in enumerate(words):
            self.machine.set("host_address", address // 4 + i)
            self.machine.set("host_data", int(word) & 0xffffffff)
            self.machine.tick("clk")
        self.machine.set("host_write", 0)

    def read(self, address, count):
        result = []
        for i in range(count):
            self.machine.set("host_address", address // 4 + i)
            result.append(signed(self.machine.eval()["host_result"]))
        return result

    def command(self, opcode, **fields):
        self.machine.set("command", {**self.empty, "tag": 1, "opcode": opcode, **fields})
        if not self.machine.eval()["command_ready"]:
            raise RuntimeError("command queue unexpectedly blocked")
        self.machine.set("command_valid", 1)
        self.machine.tick("clk")
        self.machine.set("command_valid", 0)
        self.commands += 1
        for _ in range(2048):
            state = self.machine.run_cycles("clk", 32)
            if state["errors"]:
                raise RuntimeError(f"RTL error after command {self.commands}, opcode {opcode}")
            if state["completed"] == self.commands:
                return
        raise TimeoutError(f"RTL timeout: command {self.commands}, opcode {opcode}")

    def load(self, address, ub, count):
        self.command(3, address=address, auxiliary=ub, length=count * 4)

    def store(self, ub, count):
        self.command(4, address=0x9000, auxiliary=ub, length=count * 4)
        return self.read(0x9000, count)

    def vector(self, op, x, y=None, scalar0=0, scalar1=0):
        if not 1 <= len(x) <= 256 or (y is not None and len(y) != len(x)):
            raise ValueError("invalid vector shape")
        self.upload(0x8000, x)
        self.load(0x8000, 0, len(x))
        if y is not None:
            self.upload(0x8400, y)
            self.load(0x8400, 1024, len(y))
        self.command(7, address=0, auxiliary=2048, source1_base=1024,
                     length=(op << 12) | len(x), scalar0=scalar0 & 0xffffffff,
                     scalar1=scalar1 & 0xffffffff)
        return self.store(2048, len(x))

    def norm(self, x):
        return self.vector(6, x, scalar0=q16(1e-5), scalar1=ONE // len(x))

    def linear(self, x, weights):
        if isinstance(weights, str):
            address, rows, cols = self.matrices[weights]
        else:
            rows, cols, address = len(weights), len(x), 0x7000
            padded = weights + ([[0] * cols] if rows % 2 else [])
            if not rows or any(len(row) != cols for row in weights) or len(padded) * cols > 1024:
                raise ValueError("dynamic matrix exceeds its reserved memory region")
            self.upload(address, [v for row in padded for v in row])
        if cols != len(x) or not 1 <= cols <= 64:
            raise ValueError("invalid linear shape")
        self.upload(0x8800, [v for value in x for v in (value, 0)])
        self.load(0x8800, 1024, 2 * cols)
        result = []
        for row in range(0, rows, 2):
            self.load(address + row * cols * 4, 0, 2 * cols)
            self.command(5, mxu_valid=1, mxu_a_base=0, mxu_b_base=1024,
                         mxu_c_base=2048, mxu_a_stride=cols * 4, mxu_b_stride=8,
                         mxu_k_dim=cols, mxu_acc_clear=1, mxu_mode=3)
            tile = self.store(2048, 4)
            result.extend((tile[0], tile[2]))
        return result[:rows]

    def token(self, token, position, keys, values):
        if not 0 <= position < self.config["block_size"] or len(keys) != position or len(values) != position:
            raise ValueError("KV cache length must match the token position")
        x = self.norm(self.vector(11, self.weights["wte"][token], self.weights["wpe"][position]))
        residual, normalized = x, self.norm(x)
        q, k, v = [self.linear(normalized, "layer0.attn_w" + part) for part in "qkv"]
        keys.append(k)
        values.append(v)
        dim = self.config["n_embd"] // self.config["n_head"]
        attention = []
        for head in range(self.config["n_head"]):
            start = head * dim
            scores = self.linear(q[start:start + dim], [key[start:start + dim] for key in keys])
            scores = self.vector(12, scores, scalar0=q16(1 / math.sqrt(dim)))
            probs = self.vector(4, scores)
            attention.extend(self.linear(probs, [[row[start + j] for row in values] for j in range(dim)]))
        x = self.vector(11, self.linear(attention, "layer0.attn_wo"), residual)
        residual = x
        hidden = self.vector(9, self.linear(self.norm(x), "layer0.mlp_fc1"))
        x = self.vector(11, self.linear(hidden, "layer0.mlp_fc2"), residual)
        return self.linear(x, "lm_head")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="one training document per line; defaults to the original names dataset")
    parser.add_argument("--checkpoint", type=Path, help="reuse an exported demo JSON checkpoint without training or network access")
    parser.add_argument("--steps", type=int, default=1000, help="host checkpoint training steps (default: 1000)")
    parser.add_argument("--samples", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--temperature", type=float, default=0.5)
    parser.add_argument("--embd", type=int, default=16)
    parser.add_argument("--heads", type=int, default=4)
    parser.add_argument("--block-size", type=int, default=16)
    args = parser.parse_args()
    if args.steps < 1 or args.samples < 1 or not math.isfinite(args.temperature) or args.temperature <= 0:
        parser.error("steps, samples, and temperature must be positive")
    config = {"n_embd": args.embd, "n_head": args.heads, "block_size": args.block_size}
    if not (2 <= args.embd <= 16 and 1 <= args.heads <= args.embd and args.embd % args.heads == 0
            and 1 <= args.block_size <= 16):
        parser.error("require embd=2..16 divisible by heads, block-size=1..16")
    cache = ROOT / "build/microgpt"
    cache.mkdir(parents=True, exist_ok=True)
    if args.checkpoint:
        checkpoint = json.loads(args.checkpoint.read_text())
    else:
        source = args.input or cache / "names.txt"
        if not source.exists() and args.input is None:
            print(f"Downloading {NAMES_URL}", file=sys.stderr, flush=True)
            with urlopen(NAMES_URL, timeout=30) as response:
                data = response.read(4 * 1024 * 1024 + 1)
            if len(data) > 4 * 1024 * 1024:
                raise ValueError("dataset exceeds 4 MiB")
            source.write_bytes(data)
        text = source.read_text(encoding="utf-8")
        identity = hashlib.sha256(json.dumps([text, config, args.steps, args.seed]).encode()).hexdigest()[:16]
        checkpoint_path = cache / f"checkpoint-{identity}.json"
        if checkpoint_path.exists():
            checkpoint = json.loads(checkpoint_path.read_text())
        else:
            checkpoint = train_checkpoint(text, config, args.steps, args.seed)
            validate_checkpoint(checkpoint)
            checkpoint_path.write_text(json.dumps(checkpoint, allow_nan=False) + "\n")
        print(f"Checkpoint: {checkpoint_path}", file=sys.stderr, flush=True)
    validate_checkpoint(checkpoint)
    rng = random.Random(args.seed)
    if checkpoint["training"]["seed"] == args.seed:
        state = checkpoint["random_state"]
        rng.setstate((state[0], tuple(state[1]), state[2]))
    hardware = Hardware(checkpoint)
    chars, count = checkpoint["chars"], 0
    print("\n--- inference (Q16, ZLang native simulator) ---", flush=True)
    first_cycle = hardware.machine.eval()["cycles"]
    started = perf_counter()
    for sample in range(args.samples):
        token, keys, values, output = len(chars), [], [], []
        for position in range(checkpoint["config"]["block_size"]):
            print(f"sample {sample + 1}: token {position + 1}/{checkpoint['config']['block_size']}",
                  end="\r", file=sys.stderr, flush=True)
            logits = hardware.token(token, position, keys, values)
            logits = hardware.vector(12, logits, scalar0=q16(1 / args.temperature))
            probs = hardware.vector(4, logits)
            if any(p < 0 for p in probs) or sum(probs) <= 0:
                raise RuntimeError("invalid RTL probability distribution")
            token = rng.choices(range(len(chars) + 1), weights=probs, k=1)[0]
            count += 1
            if token == len(chars):
                break
            output.append(chars[token])
        print(file=sys.stderr)
        print(f"sample {sample + 1:2d}: {''.join(output)}", flush=True)
    state = hardware.machine.eval()
    print(f"{count} tokens, {hardware.commands} queued commands, {state['cycles'] - first_cycle} inference cycles, "
          f"{perf_counter() - started:.2f}s inference", file=sys.stderr)
    hardware.machine.close()


if __name__ == "__main__":
    try:
        main()
    except (ValueError, TypeError, KeyError, OSError, RuntimeError) as error:
        raise SystemExit(f"microgpt: {error}") from error
