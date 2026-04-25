#!/usr/bin/env python3
"""Validate custom size strings for gpt-image-2.

Usage:
    python scripts/validate_gpt_image_2_size.py 1536x1024
    python scripts/validate_gpt_image_2_size.py 3824x2144
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass


MIN_PIXELS = 655_360
MAX_PIXELS = 8_294_400
MAX_EDGE_EXCLUSIVE = 3840
MULTIPLE = 16
MAX_RATIO = 3.0
RELIABILITY_PIXELS = 2560 * 1440


@dataclass(frozen=True)
class SizeReport:
    width: int
    height: int
    valid: bool
    messages: list[str]


def parse_size(size: str) -> tuple[int, int]:
    match = re.fullmatch(r"(\d+)x(\d+)", size.strip().lower())
    if not match:
        raise ValueError("size must look like WIDTHxHEIGHT, for example 1536x1024")
    return int(match.group(1)), int(match.group(2))


def validate_size(width: int, height: int) -> SizeReport:
    messages: list[str] = []

    if width <= 0 or height <= 0:
        messages.append("width and height must be positive")

    if max(width, height) >= MAX_EDGE_EXCLUSIVE:
        messages.append("maximum edge must be less than 3840px")

    if width % MULTIPLE != 0 or height % MULTIPLE != 0:
        messages.append("both edges must be multiples of 16")

    short = min(width, height)
    long = max(width, height)
    if short and long / short > MAX_RATIO:
        messages.append("long edge / short edge ratio must not exceed 3:1")

    pixels = width * height
    if pixels < MIN_PIXELS:
        messages.append("total pixels must be at least 655,360")
    if pixels > MAX_PIXELS:
        messages.append("total pixels must not exceed 8,294,400")

    if not messages and pixels > RELIABILITY_PIXELS:
        messages.append("valid, but above 2560x1440; treat as more variable/experimental")

    return SizeReport(width=width, height=height, valid=not any(not m.startswith("valid,") for m in messages), messages=messages)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a gpt-image-2 size string.")
    parser.add_argument("size", help="size as WIDTHxHEIGHT, e.g. 1536x1024")
    args = parser.parse_args()

    try:
        width, height = parse_size(args.size)
    except ValueError as exc:
        raise SystemExit(f"invalid: {exc}") from exc

    report = validate_size(width, height)
    pixels = width * height
    print(f"size: {width}x{height}")
    print(f"pixels: {pixels:,}")
    print(f"valid: {str(report.valid).lower()}")
    for message in report.messages:
        print(f"- {message}")


if __name__ == "__main__":
    main()
