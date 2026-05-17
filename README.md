# Swift Type Checking Benchmarks

Small Swift type-checking benchmarks focused on compile-time type inference, overload resolution, and constraint-solver performance.

The original script comes from this [Swift Forums discussion](https://forums.swift.org/t/regarding-swift-type-inference-compile-time-performance/49748/3).

## Requirements

- Python 3
- [`hyperfine`](https://github.com/sharkdp/hyperfine)

Install `hyperfine` with Homebrew:

```sh
brew install hyperfine
```

## Usage

```sh
python3 run.py <benchmark_name> <number_of_iterations> [--warmup N] [--runs N]
```

List the available benchmark names:

```sh
python3 run.py --list
```

For example:

```sh
python3 run.py flatmap-chain 100
```

To run each variant with 3 warmup runs and exactly 20 timed runs:

```sh
python3 run.py overloaded-box-init 300 --warmup 3 --runs 20
```

The script writes all generated Swift files for the selected benchmark into the repository root, then benchmarks them together with one `hyperfine` run. Each generated file is checked with:

```sh
xcrun swiftc -typecheck <file>.swift
```

## Benchmarks

| Benchmark | What it exercises |
| --- | --- |
| `contextual-init` | Inferred `.init` passed to a function with a concrete argument type. |
| `flatmap-chain` | Closure parameter and return inference through `flatMap` and `reduce`. |
| `overloaded-box-init` | Inferred `.init` in overloaded box-read calls. |
| `closure-flatmap-many-init` | Inferred `.init` inside a larger array returned from a `flatMap` closure. |
| `overloaded-inits` | One nominal type with several initializer overloads. |
| `overloaded-literals` | Overloaded array and numeric literals. |

## Observed Results

These results are from one local run. They are useful for comparing the benchmark variants on this machine, but they are not universal Swift performance rules.

### Benchmark Protocol

```sh
python3 run.py <benchmark_name> 300 --warmup 1 --runs 10
```

### Environment

| Field | Value |
| --- | --- |
| Date | 2026-05-17 |
| Machine | Apple M1 Pro |
| CPU count | 8 |
| Memory | 32 GiB |
| OS | macOS 26.3.1 (25D771280a) |
| Swift | Apple Swift 6.3 (`swiftlang-6.3.0.123.5 clang-2100.0.123.102`) |
| Target | `arm64-apple-macosx26.0` |
| hyperfine | 1.19.0 |

### Results

All benchmark rows below were run under this protocol.

| Benchmark | Inferred | Explicit | Result |
| --- | --- | --- | --- |
| `contextual-init` | `doSomething(viewModel: .init(...))` — 152.3 ms | `doSomething(viewModel: ViewModel(...))` — 174.2 ms | Inferred was 1.14x faster. |
| `flatmap-chain` | inferred `flatMap` closure/result — 3.649 s | explicit closure/result types — 378.9 ms | Explicit was 9.63x faster. |
| `overloaded-box-init` | `read(.init(...))` — 1.227 s | `read(IntBox(...))` — 321.5 ms | Explicit was 3.82x faster. |
| `closure-flatmap-many-init` | `flatMap { [.init(...), ...] }` — 4.843 s | `flatMap { [Cell(...), ...] }` — 1.017 s | Explicit was 4.76x faster. |
| `overloaded-inits` | inferred `.init` with overloaded initializers — 316.0 ms | explicit `Quantity(Int(...))` — 417.5 ms | Inferred was 1.32x faster. |
| `overloaded-literals` | inferred overloaded array literals — 300.0 ms | explicit `Int` array literals — 403.2 ms | Inferred was 1.34x faster. |
