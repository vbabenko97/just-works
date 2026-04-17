"""Generate test datasets for ai-analyst-pipeline evals.

Each dataset embeds a specific analytical pattern the skill should surface:

  - tourism: Simpson's Paradox by island (aggregate flat, subgroups diverge).
  - churn: Root-cause drill-down (churn spike concentrated in one plan + industry).
  - funnel: Composition shift (flat aggregate hides new-user gains + returning-user loss).

Data is deterministic (fixed seed) and small (< 2k rows total) to keep evals fast.
"""

from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).parent
random.seed(42)


def month_iter(start: date, n_months: int):
    y, m = start.year, start.month
    for _ in range(n_months):
        yield date(y, m, 1)
        m += 1
        if m > 12:
            m = 1
            y += 1


def generate_tourism() -> None:
    """24 months of visitor arrivals across 4 Hawaiian islands.

    Pattern (matches the source article):
      - Aggregate looks roughly flat across the 24 months
      - Maui grows ~7% YoY in the final year
      - Oahu declines ~5% YoY in the final year
      - Oahu decline is concentrated in 'hotel' accommodation type
      - Within hotels, the 'luxury' tier has the worst decline

    Columns: month, island, accommodation_type, tier, origin_market, visitor_arrivals
    """
    rows = []
    islands = ["Maui", "Oahu", "Kauai", "Hawaii"]
    accommodations = ["hotel", "vacation_rental", "timeshare"]
    tiers = ["luxury", "mid_market", "budget"]
    origins = ["US_mainland", "Japan", "Canada", "Europe", "Other"]

    base = {
        "Maui": 180_000,
        "Oahu": 420_000,
        "Kauai": 90_000,
        "Hawaii": 120_000,
    }
    accom_share = {"hotel": 0.55, "vacation_rental": 0.30, "timeshare": 0.15}
    tier_share = {"luxury": 0.25, "mid_market": 0.55, "budget": 0.20}
    origin_share = {
        "US_mainland": 0.60, "Japan": 0.18, "Canada": 0.10,
        "Europe": 0.08, "Other": 0.04,
    }

    months = list(month_iter(date(2024, 1, 1), 24))

    for i, m in enumerate(months):
        year2 = i >= 12  # second year, where divergence happens
        months_into_year2 = max(0, i - 11)

        for island in islands:
            # Growth/decline multipliers in year 2
            if island == "Maui" and year2:
                island_mult = 1.0 + 0.07 * (months_into_year2 / 12)
            elif island == "Oahu" and year2:
                island_mult = 1.0 - 0.05 * (months_into_year2 / 12)
            else:
                island_mult = 1.0

            # Seasonality (summer and winter peaks)
            month_num = m.month
            season_mult = 1.0 + 0.15 * (
                1 if month_num in (6, 7, 8, 12) else
                -0.08 if month_num in (4, 5, 9, 10) else 0
            )

            for accom in accommodations:
                for tier in tiers:
                    for origin in origins:
                        accom_mult = 1.0
                        # Oahu hotel decline concentrated in luxury, and luxury decline
                        # concentrated in Japanese origin market
                        if island == "Oahu" and accom == "hotel" and year2:
                            if tier == "luxury":
                                accom_mult = 1.0 - 0.12 * (months_into_year2 / 12)
                                if origin == "Japan":
                                    accom_mult *= 1.0 - 0.08 * (months_into_year2 / 12)
                            elif tier == "mid_market":
                                accom_mult = 1.0 - 0.03 * (months_into_year2 / 12)

                        val = (
                            base[island]
                            * accom_share[accom]
                            * tier_share[tier]
                            * origin_share[origin]
                            * island_mult
                            * season_mult
                            * accom_mult
                            * random.uniform(0.92, 1.08)  # noise
                        )
                        rows.append({
                            "month": m.isoformat(),
                            "island": island,
                            "accommodation_type": accom,
                            "tier": tier,
                            "origin_market": origin,
                            "visitor_arrivals": int(round(val)),
                        })

    out = HERE / "tourism_monthly.csv"
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {out} ({len(rows)} rows)")


def generate_churn() -> None:
    """Customer-level churn data across 6 quarters.

    Pattern:
      - Overall churn rose from ~4% to ~7% in the final quarter (Q2 2026)
      - Rise is concentrated in 'Pro' plan tier (4% -> 11%)
      - Within Pro plan, 'Retail' industry drives most of it (3% -> 18%)
      - Other plan tiers (Starter, Enterprise) and industries stable

    Columns: customer_id, signup_quarter, churn_quarter (or 'active'), plan_tier,
             industry, arr_usd, tenure_months
    """
    rows = []
    plans = ["Starter", "Pro", "Enterprise"]
    industries = ["Retail", "SaaS", "Finance", "Healthcare", "Manufacturing"]

    # Base churn rates per quarter (per-customer probability)
    quarters = [
        "2025Q1", "2025Q2", "2025Q3", "2025Q4", "2026Q1", "2026Q2"
    ]

    arr_by_plan = {"Starter": 1_200, "Pro": 8_400, "Enterprise": 48_000}
    plan_share = {"Starter": 0.5, "Pro": 0.35, "Enterprise": 0.15}

    n_customers = 1500
    customer_id = 1001
    for _ in range(n_customers):
        plan = random.choices(plans, weights=[plan_share[p] for p in plans])[0]
        industry = random.choice(industries)
        signup_q = random.choice(quarters[:3])  # all signed up in first 3 quarters
        signup_idx = quarters.index(signup_q)

        # Figure out when/if they churn
        churn_q = "active"
        for q_idx in range(signup_idx + 1, len(quarters)):
            q_name = quarters[q_idx]
            # Base churn probability by plan
            base_p = {"Starter": 0.06, "Pro": 0.04, "Enterprise": 0.02}[plan]

            # The Q2 2026 anomaly: Pro + Retail has massive churn
            if q_name == "2026Q2":
                if plan == "Pro" and industry == "Retail":
                    base_p = 0.18
                elif plan == "Pro":
                    base_p = 0.07

            if random.random() < base_p:
                churn_q = q_name
                break

        tenure_months = 0
        if churn_q == "active":
            tenure_months = (len(quarters) - signup_idx) * 3
        else:
            tenure_months = (quarters.index(churn_q) - signup_idx) * 3

        rows.append({
            "customer_id": f"C{customer_id:05d}",
            "signup_quarter": signup_q,
            "churn_quarter": churn_q,
            "plan_tier": plan,
            "industry": industry,
            "arr_usd": arr_by_plan[plan],
            "tenure_months": tenure_months,
        })
        customer_id += 1

    out = HERE / "customer_churn.csv"
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {out} ({len(rows)} rows)")


def generate_funnel() -> None:
    """Marketing funnel events across 6 months, 4 channels, new vs returning users.

    Pattern:
      - Overall conversion rate looks ~flat (8.5% -> 8.4%)
      - New-user conversion rose from 5.0% -> 7.5% (strong improvement)
      - Returning-user conversion fell from 14.0% -> 10.0% (regression)
      - Mix shift: returning-user share grew, masking the regression

    Columns: month, channel, user_type, visits, signups, conversions
    """
    rows = []
    channels = ["paid_search", "organic", "email", "referral"]
    user_types = ["new", "returning"]

    months = list(month_iter(date(2026, 1, 1), 6))

    for i, m in enumerate(months):
        # Month index 0..5
        for channel in channels:
            for utype in user_types:
                # Base visits by channel
                base_visits = {
                    "paid_search": 25_000,
                    "organic": 18_000,
                    "email": 8_000,
                    "referral": 5_000,
                }[channel]

                # Type split shifting over time (returning gets larger)
                if utype == "new":
                    type_share = 0.6 - 0.03 * i  # 60% -> 45%
                else:
                    type_share = 0.4 + 0.03 * i  # 40% -> 55%

                visits = int(base_visits * type_share * random.uniform(0.95, 1.05))

                # Conversion rates: new improves, returning regresses
                if utype == "new":
                    conv_rate = 0.050 + 0.005 * i  # 5.0% -> 7.5%
                else:
                    conv_rate = 0.140 - 0.008 * i  # 14.0% -> ~10.0%
                # Small noise
                conv_rate *= random.uniform(0.92, 1.08)

                conversions = int(visits * conv_rate)
                signups = int(conversions * random.uniform(1.5, 2.2))  # upstream step

                rows.append({
                    "month": m.isoformat(),
                    "channel": channel,
                    "user_type": utype,
                    "visits": visits,
                    "signups": signups,
                    "conversions": conversions,
                })

    out = HERE / "funnel_monthly.csv"
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {out} ({len(rows)} rows)")


if __name__ == "__main__":
    generate_tourism()
    generate_churn()
    generate_funnel()
