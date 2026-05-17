#!/usr/bin/env python3
import argparse
import subprocess

VIEW_MODEL_PRELUDE = """
struct ViewModel {
    let value: String
}
func doSomething(viewModel: ViewModel) -> String {
    return viewModel.value
}
"""

BOX_OVERLOAD_PRELUDE = """
struct IntBox {
    let value: Int
}

struct ShortBox {
    let value: Int
}

struct DecimalBox {
    let value: Int
}

func read(_ box: IntBox) -> Int {
    return box.value
}

func read(_ box: ShortBox) -> Int16 {
    return Int16(box.value)
}

func read(_ box: DecimalBox) -> Double {
    return Double(box.value)
}
"""

CLOSURE_MODEL_PRELUDE = """
struct Cell {
    let value: Int
    let label: String
}

func renderCells(_ cells: [Cell]) -> Int {
    return cells.count
}

let numbers = [1, 2, 3, 4, 5]
"""

OVERLOADED_INIT_PRELUDE = """
struct Quantity {
    let value: Int

    init(_ value: Int) {
        self.value = value
    }

    init(_ value: Int8) {
        self.value = Int(value)
    }

    init(_ value: Int16) {
        self.value = Int(value)
    }

    init(_ value: Int32) {
        self.value = Int(value)
    }

    init(_ value: Double) {
        self.value = Int(value)
    }
}
func measure(_ quantity: Quantity) -> Int {
    return quantity.value
}
"""

OVERLOADED_LITERAL_PRELUDE = """
func total(_ values: [Int]) -> Int {
    return values.reduce(0, +)
}
func total(_ values: [Int8]) -> Int8 {
    return values.reduce(0, +)
}
func total(_ values: [Int16]) -> Int16 {
    return values.reduce(0, +)
}
func total(_ values: [Int32]) -> Int32 {
    return values.reduce(0, +)
}
func total(_ values: [Double]) -> Double {
    return values.reduce(0, +)
}
"""

EXAMPLES = {
    "contextual-init": {
        "summary": "shorthand .init with a concrete function-argument context",
        "prelude": VIEW_MODEL_PRELUDE,
        "variants": [
            (
                "explicit ViewModel initializer argument",
                "a",
                'let a{} = doSomething(viewModel: ViewModel(value: "test"))',
            ),
            (
                "shorthand .init argument",
                "b",
                'let b{} = doSomething(viewModel: .init(value: "test"))',
            ),
        ],
    },
    "flatmap-chain": {
        "summary": "closure parameter and result inference through flatMap/reduce",
        "prelude": "",
        "variants": [
            (
                "inferred flatMap closure/result",
                "a",
                'let a{} = [1, 2, 3].flatMap {{ value in [value, value + 1] }}.reduce(0, +)',
            ),
            (
                "explicit flatMap closure/result",
                "b",
                'let b{}: Int = [1, 2, 3].flatMap {{ (value: Int) -> [Int] in [value, value + 1] }}.reduce(0, +)',
            ),
        ],
    },
    "overloaded-box-init": {
        "summary": "shorthand .init while resolving overloaded box-read calls",
        "prelude": BOX_OVERLOAD_PRELUDE,
        "variants": [
            (
                "explicit IntBox initializer",
                "a",
                "let a{} = read(IntBox(value: 1)) + read(IntBox(value: 2)) + 1",
            ),
            (
                "shorthand .init IntBox",
                "b",
                "let b{} = read(.init(value: 1)) + read(.init(value: 2)) + 1",
            ),
        ],
    },
    "closure-flatmap-many-init": {
        "summary": "shorthand .init inside a larger array returned from flatMap",
        "prelude": CLOSURE_MODEL_PRELUDE,
        "variants": [
            (
                "explicit Cell initializers in flatMap",
                "a",
                'let a{} = renderCells(numbers.flatMap {{ [Cell(value: $0, label: "\\($0)"), Cell(value: $0 + 1, label: "\\($0 + 1)"), Cell(value: $0 + 2, label: "\\($0 + 2)"), Cell(value: $0 + 3, label: "\\($0 + 3)")] }})',
            ),
            (
                "shorthand .init in flatMap",
                "b",
                'let b{} = renderCells(numbers.flatMap {{ [.init(value: $0, label: "\\($0)"), .init(value: $0 + 1, label: "\\($0 + 1)"), .init(value: $0 + 2, label: "\\($0 + 2)"), .init(value: $0 + 3, label: "\\($0 + 3)")] }})',
            ),
        ],
    },
    "overloaded-inits": {
        "summary": "one nominal type with several initializer overloads",
        "prelude": OVERLOADED_INIT_PRELUDE,
        "variants": [
            (
                "shorthand .init with overloaded initializers",
                "a",
                'let a{} = measure(.init(1)) + measure(.init(2)) + measure(.init(3))',
            ),
            (
                "explicit Quantity initializer and Int literals",
                "b",
                'let b{} = measure(Quantity(Int(1))) + measure(Quantity(Int(2))) + measure(Quantity(Int(3)))',
            ),
        ],
    },
    "overloaded-literals": {
        "summary": "overloaded array and numeric literals",
        "prelude": OVERLOADED_LITERAL_PRELUDE,
        "variants": [
            (
                "inferred overloaded array literals",
                "a",
                'let a{} = total([1, 2, 3]) + total([4, 5, 6]) + 1',
            ),
            (
                "explicit Int array literals",
                "b",
                'let b{}: Int = total([Int(1), Int(2), Int(3)]) + total([Int(4), Int(5), Int(6)]) + 1',
            ),
        ],
    },
}


def positive_int(value):
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return parsed


def non_negative_int(value):
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be at least 0")
    return parsed


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate Swift type-checking benchmarks and compare them with hyperfine."
    )
    parser.add_argument("example_name", nargs="?", choices=sorted(EXAMPLES.keys()))
    parser.add_argument("number_of_iterations", nargs="?", type=positive_int)
    parser.add_argument(
        "--list",
        action="store_true",
        help="list available benchmark names and exit",
    )
    parser.add_argument(
        "--warmup",
        type=non_negative_int,
        default=1,
        help="number of hyperfine warmup runs before timing each command (default: 1)",
    )
    parser.add_argument(
        "--runs",
        type=positive_int,
        help="exact number of timed hyperfine runs for each command",
    )
    args = parser.parse_args()

    if args.list:
        for name, example in EXAMPLES.items():
            print("{}: {}".format(name, example["summary"]))
        raise SystemExit(0)

    if args.example_name is None:
        parser.error("the following argument is required: example_name")

    if args.number_of_iterations is None:
        parser.error("the following argument is required: number_of_iterations")

    return args


def write_swift_file(filename, prelude, code, number_of_iterations):
    with open(filename + ".swift", "w") as f:
        f.write(prelude)
        if prelude and not prelude.endswith("\n"):
            f.write("\n")

        for j in range(number_of_iterations):
            f.write((code + "\n").format(j))


def main():
    args = parse_args()
    example = EXAMPLES[args.example_name]
    commands = []
    command_names = []

    for (label, filename, code) in example["variants"]:
        benchmark_label = "{} ({}.swift)".format(label, filename)
        write_swift_file(filename, example["prelude"], code, args.number_of_iterations)
        print("Generated:", benchmark_label, "=>", code.format("{}"), flush=True)
        command_names.extend(["--command-name", benchmark_label])
        commands.append("xcrun swiftc -typecheck {}".format(filename + ".swift"))

    hyperfine_args = ["hyperfine", "--warmup", str(args.warmup)]
    if args.runs is not None:
        hyperfine_args.extend(["--runs", str(args.runs)])

    subprocess.run([*hyperfine_args, *command_names, *commands], check=True)


if __name__ == "__main__":
    main()
