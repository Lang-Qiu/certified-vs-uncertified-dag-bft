#!/usr/bin/env python
import argparse
import sys
from pathlib import Path


def verify_no_paper_mutation(root):
    root = Path(root)
    errors = []
    final_paper = root / "final" / "final_paper.md"
    if not final_paper.exists():
        errors.append(f"missing expected final paper path: {final_paper}")
    stage8 = root / "stage8_paper_integration"
    if stage8.exists():
        errors.append(f"stage8_paper_integration exists and must not be written without explicit approval: {stage8}")
    return errors


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Verify paper integration paths were not touched/created.")
    parser.add_argument("--root", default=".")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    errors = verify_no_paper_mutation(args.root)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("paper mutation guard passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
