#!/usr/bin/env python3
"""Estimate long-term impact of annual fees on an investment balance.

This helper is intentionally simple. It compares gross compounding against
compounding after an annual percentage fee, plus optional one-time entry and
exit fees.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass


@dataclass(frozen=True)
class FeeDragResult:
    gross_final: float
    net_final: float
    total_drag: float
    drag_pct_of_gross: float


def estimate_fee_drag(
    principal: float,
    annual_return_pct: float,
    annual_fee_pct: float,
    years: int,
    entry_fee_pct: float = 0.0,
    exit_fee_pct: float = 0.0,
) -> FeeDragResult:
    if principal < 0:
        raise ValueError("principal must be non-negative")
    if years < 0:
        raise ValueError("years must be non-negative")
    for name, value in {
        "annual_return_pct": annual_return_pct,
        "annual_fee_pct": annual_fee_pct,
        "entry_fee_pct": entry_fee_pct,
        "exit_fee_pct": exit_fee_pct,
    }.items():
        if value < -100:
            raise ValueError(f"{name} cannot be below -100")

    gross_rate = annual_return_pct / 100.0
    fee_rate = annual_fee_pct / 100.0
    entry_fee_rate = entry_fee_pct / 100.0
    exit_fee_rate = exit_fee_pct / 100.0

    gross_final = principal * ((1.0 + gross_rate) ** years)
    net_start = principal * (1.0 - entry_fee_rate)
    net_final_before_exit = net_start * ((1.0 + gross_rate - fee_rate) ** years)
    net_final = net_final_before_exit * (1.0 - exit_fee_rate)
    total_drag = gross_final - net_final
    drag_pct = (total_drag / gross_final * 100.0) if gross_final else 0.0
    return FeeDragResult(gross_final, net_final, total_drag, drag_pct)


def main() -> None:
    parser = argparse.ArgumentParser(description="Estimate investment fee drag.")
    parser.add_argument("--principal", type=float, required=True)
    parser.add_argument("--annual-return-pct", type=float, required=True)
    parser.add_argument("--annual-fee-pct", type=float, required=True)
    parser.add_argument("--years", type=int, required=True)
    parser.add_argument("--entry-fee-pct", type=float, default=0.0)
    parser.add_argument("--exit-fee-pct", type=float, default=0.0)
    parser.add_argument("--currency", default="")
    args = parser.parse_args()

    result = estimate_fee_drag(
        principal=args.principal,
        annual_return_pct=args.annual_return_pct,
        annual_fee_pct=args.annual_fee_pct,
        years=args.years,
        entry_fee_pct=args.entry_fee_pct,
        exit_fee_pct=args.exit_fee_pct,
    )
    prefix = f"{args.currency} " if args.currency else ""
    print(f"gross_final: {prefix}{result.gross_final:,.2f}")
    print(f"net_final: {prefix}{result.net_final:,.2f}")
    print(f"total_fee_drag: {prefix}{result.total_drag:,.2f}")
    print(f"drag_pct_of_gross: {result.drag_pct_of_gross:.2f}%")


if __name__ == "__main__":
    main()
