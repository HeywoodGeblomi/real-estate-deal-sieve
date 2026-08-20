#!/usr/bin/env python3
"""End-to-end local demo for Real-Estate Deal Sieve.
CSV → matrix → ranks → formatted results + simple stress view.
promote_ready=false. EXTERNAL-clean / no-χ.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from adapter.csv_to_matrix import build_matrix, load_csv, save_matrix_bin
from core.ranker import pure_python_weak_dominance
from core.result_formatter import (
    format_results,
    load_original_rows,
    print_summary,
    write_results_csv,
    write_results_json,
)

def run_demo(
    csv_path: Path = ROOT / "data" / "sample_deals.csv",
    out_dir: Path = ROOT / "output",
    obj1: str = "cap_rate",
    obj1_higher: bool = True,
    obj2: str = "risk_score",
    obj2_higher: bool = False,
):
    out_dir.mkdir(parents=True, exist_ok=True)
    rows, headers = load_csv(csv_path)
    print(f"[demo] Loaded {len(rows)} deals from {csv_path.name}")

    matrix, deal_ids = build_matrix(
        rows, obj1, obj1_higher, obj2, obj2_higher
    )
    save_matrix_bin(matrix, out_dir / "matrix.bin")
    meta = {
        "ok": True,
        "n": len(deal_ids),
        "m": 2,
        "deal_ids": deal_ids,
        "obj1": obj1,
        "obj2": obj2,
        "profile": "cashflow",
        "promote_ready": False,
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2))
    print(f"[demo] Wrote matrix.bin shape={matrix.shape}")

    # Force pure-Python for reproducible public demo
    ranks = pure_python_weak_dominance(matrix)
    n_nd = int((ranks == 1).sum())
    print(f"[demo] Ranking complete — {n_nd} non-dominated (rank-1)")

    original = load_original_rows(csv_path)
    results = format_results(deal_ids, ranks, original)
    write_results_csv(results, out_dir / "ranked_deals.csv")
    write_results_json(results, out_dir / "ranked_deals.json", meta)
    print_summary(results, top_k=12)

    # Simple deterministic stress view (not a forecast)
    stress_rows = []
    for row in original:
        try:
            base_risk = float(row.get("risk_score", 0.5))
            sens = float(row.get("interest_sensitivity", 0.3))
            vac = float(row.get("vacancy_risk", 0.1))
            exit_m = float(row.get("exit_multiple_proxy", 1.3))
            # +200bp rates / +5pp vacancy / -0.10 exit pressure (illustrative linear map)
            stressed_risk = np.clip(
                base_risk + 0.15 * sens + 0.20 * vac + 0.10 * max(0.0, 1.4 - exit_m),
                0.0,
                1.0,
            )
            stress_rows.append({
                "deal_id": row.get("deal_id"),
                "base_risk": round(base_risk, 3),
                "stressed_risk": round(float(stressed_risk), 3),
                "delta": round(float(stressed_risk - base_risk), 3),
            })
        except Exception:
            continue
    stress_path = out_dir / "stress_view.json"
    stress_payload = {
        "ok": True,
        "description": "Deterministic re-mapping only. Not a forecast or Monte-Carlo.",
        "assumptions": "+200 bp rate sensitivity weight, +5 pp vacancy weight, -0.10 exit multiple pressure",
        "promote_ready": False,
        "rows": stress_rows,
    }
    stress_path.write_text(json.dumps(stress_payload, indent=2))
    print(f"[demo] Wrote {stress_path.name} (deterministic stress view)")
    print("[demo] promote_ready=false | EXTERNAL-clean | no-χ | structural sieve only")
    return 0

if __name__ == "__main__":
    raise SystemExit(run_demo())
