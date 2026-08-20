#!/usr/bin/env python3
"""
Real-Estate Deal Sieve — Minimal Streamlit MVP

CSV upload → column mapping → weak-dominance ranking → results table + stress view.

EXTERNAL-clean / no-χ / promote_ready=false.
Structural ranking sieve only. Not investment advice.
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import numpy as np
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from adapter.csv_to_matrix import build_matrix, load_csv, save_matrix_bin  # noqa: E402
from adapter.column_mapper import PROFILES, resolve_profile  # noqa: E402
from core.ranker import pure_python_weak_dominance  # noqa: E402
from core.result_formatter import format_results, print_summary  # noqa: E402

st.set_page_config(
    page_title="Real-Estate Deal Sieve",
    page_icon="🏠",
    layout="wide",
)

st.title("Real-Estate Deal Sieve")
st.caption(
    "Multi-objective weak-dominance ranking of real-estate deals. "
    "Structural sieve only — not investment advice. promote_ready=false."
)

with st.expander("Honesty / Non-claims", expanded=False):
    st.markdown(
        """
- This tool isolates deals that are **not weakly dominated** on the objectives you choose.
- It does **not** predict returns, appraise properties, or recommend investments.
- Stress view is a **deterministic re-mapping** of your input features, not a forecast.
- Ranking powered by pure weak-dominance (GyroRank / PrymGyroSort lineage).
- EXTERNAL-clean / no-χ.
        """
    )

# --- Sidebar: profile + limits ---
st.sidebar.header("Settings")
profile_name = st.sidebar.selectbox(
    "Profile",
    options=list(PROFILES.keys()) + ["custom"],
    index=0,
    help="Preset column pairs (cashflow, balanced, stress_resistant, …)",
)

max_deals = st.sidebar.number_input("Max deals (free tier)", min_value=5, max_value=200, value=50)

# --- Upload ---
uploaded = st.file_uploader("Upload deal CSV", type=["csv"])

if uploaded is None:
    st.info("Upload a CSV with columns such as cap_rate, cash_on_cash, risk_score, liquidity_score, vacancy_risk, …")
    st.markdown("**Sample columns expected:** `deal_id`, `cap_rate`, `cash_on_cash`, `risk_score`, `liquidity_score`, `vacancy_risk`, `interest_sensitivity`, `exit_multiple_proxy`")
    if st.button("Load sample deals"):
        sample_path = ROOT / "data" / "sample_deals.csv"
        if sample_path.is_file():
            st.session_state["sample_bytes"] = sample_path.read_bytes()
            st.rerun()
    st.stop()

# Handle sample load
if "sample_bytes" in st.session_state and uploaded is None:
    raw = st.session_state["sample_bytes"]
else:
    raw = uploaded.getvalue()

# Parse CSV
try:
    import csv
    text = raw.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    headers = list(reader.fieldnames or [])
except Exception as e:
    st.error(f"Failed to parse CSV: {e}")
    st.stop()

if len(rows) == 0:
    st.error("CSV is empty")
    st.stop()

if len(rows) > max_deals:
    st.warning(f"Truncating to first {max_deals} deals (free-tier limit).")
    rows = rows[:max_deals]

st.success(f"Loaded {len(rows)} deals. Columns: {', '.join(headers)}")

# --- Column mapping ---
st.subheader("Objective mapping")

if profile_name != "custom":
    try:
        obj1, h1, obj2, h2 = resolve_profile(profile_name)
        st.write(f"Profile **{profile_name}**: `{obj1}` ({'higher better' if h1 else 'lower better'}) vs `{obj2}` ({'higher better' if h2 else 'lower better'})")
        use_obj1, use_h1, use_obj2, use_h2 = obj1, h1, obj2, h2
    except KeyError:
        st.error("Unknown profile")
        st.stop()
else:
    col1, col2 = st.columns(2)
    with col1:
        use_obj1 = st.selectbox("Objective 1 column", options=headers, index=0)
        use_h1 = st.checkbox("Higher is better (obj1)", value=True)
    with col2:
        use_obj2 = st.selectbox("Objective 2 column", options=headers, index=min(1, len(headers)-1))
        use_h2 = st.checkbox("Higher is better (obj2)", value=False)

# --- Run ranking ---
if st.button("Run Sieve", type="primary"):
    try:
        matrix, deal_ids = build_matrix(
            rows,
            obj1_col=use_obj1,
            obj1_higher_better=use_h1,
            obj2_col=use_obj2,
            obj2_higher_better=use_h2,
        )
        ranks = pure_python_weak_dominance(matrix)
        n_nd = int((ranks == 1).sum())

        results = format_results(
            deal_ids,
            ranks,
            original_rows=rows,
            key_metrics=[use_obj1, use_obj2, "cash_on_cash", "liquidity_score", "vacancy_risk"],
        )

        st.subheader(f"Results — {n_nd} non-dominated (rank-1) of {len(results)}")
        st.caption("Rank 1 = not weakly dominated on the chosen objectives. Lower rank number is better.")

        import pandas as pd
        df = pd.DataFrame(results)

        def highlight_nd(row):
            return ["background-color: #d4edda" if row.get("non_dominated") else "" for _ in row]

        st.dataframe(
            df.style.apply(highlight_nd, axis=1),
            use_container_width=True,
            height=400,
        )

        csv_buf = io.StringIO()
        df.to_csv(csv_buf, index=False)
        st.download_button(
            "Download ranked CSV",
            data=csv_buf.getvalue(),
            file_name="ranked_deals.csv",
            mime="text/csv",
        )

        st.subheader("Stress view (deterministic re-mapping)")
        st.caption(
            "Illustrative pressure: +200 bp rate sensitivity weight + vacancy pressure + exit-multiple pressure. "
            "Not a forecast or Monte-Carlo."
        )
        stress_rows = []
        for row in rows:
            try:
                base = float(row.get("risk_score", 0.5))
                sens = float(row.get("interest_sensitivity", 0.3))
                vac = float(row.get("vacancy_risk", 0.1))
                exit_m = float(row.get("exit_multiple_proxy", 1.2))
                stressed = min(1.0, max(0.0, base + 0.15 * sens + 0.20 * vac + 0.10 * max(0.0, 1.3 - exit_m)))
                stress_rows.append({
                    "deal_id": row.get("deal_id") or row.get("address"),
                    "base_risk": round(base, 3),
                    "stressed_risk": round(stressed, 3),
                    "delta": round(stressed - base, 3),
                })
            except Exception:
                continue
        if stress_rows:
            stress_df = pd.DataFrame(stress_rows).sort_values("stressed_risk")
            st.dataframe(stress_df, use_container_width=True, height=300)

        st.markdown("---")
        st.markdown(
            "**promote_ready=false** · EXTERNAL-clean · no-χ · Structural weak-dominance sieve only. "
            "Not investment advice."
        )

    except Exception as e:
        st.error(f"Ranking failed: {type(e).__name__}: {e}")
        st.exception(e)
