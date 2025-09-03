import sys
import argparse

from bbpy.bitbabbler import BitBabbler


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read entropy from BitBabbler and print as hex and binary."
    )
    parser.add_argument(
        "-b",
        "--bits",
        type=int,
        default=2048,
        help="Number of bits to read (must be a positive multiple of 8). Default: 2048",
    )
    parser.add_argument(
        "-f",
        "--folds",
        type=int,
        default=0,
        help="Number of folds to apply (>= 0). Default: 0",
    )
    return parser.parse_args()


def main() -> int:
    try:
        args = parse_args()
        bits = args.bits
        folds = args.folds

        if bits <= 0 or bits % 8 != 0:
            raise ValueError("bits must be a positive multiple of 8")
        if folds < 0:
            raise ValueError("folds must be >= 0")

        num_bytes = bits // 8

        bb = BitBabbler.open()
        data = bb.read_entropy_folded(num_bytes, folds=folds)

        # Print as hex
        print("hex:", data.hex())

        # Print as N-bit binary number (zero-padded)
        n = int.from_bytes(data, byteorder="big", signed=False)
        print("bin:", format(n, f"0{bits}b"))
        return 0
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
