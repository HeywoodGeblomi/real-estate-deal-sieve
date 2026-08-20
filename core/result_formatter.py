#!/usr/bin/env python3
"""Join ranks back to deal rows, flag non-dominated, produce clean table / JSON."""
from __future__ import annotations
import csv
import json
from pathlib import Path
from typing import List, Dict, Any
import numpy as np

def load_original_rows(csv_path: Path) -> List[Dict[str, str]]:
    with open(csv_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def format_results(
    deal_ids: List[str],
    ranks: np.ndarray,
    original_rows: List[Dict[str, str]] | None = None,
    key_metrics: List[str] | None = None,
) -> List[Dict[str, Any]]:
    n = len(deal_ids)
    if ranks.shape[0] != n:
        raise ValueError("ranks length mismatch")
    key_metrics = key_metrics or ["cap_rate", "cash_on_cash", "risk_score", "liquidity_score"]
    results = []
    id_to_row = {}
    if original_rows:
        for row in original_rows:
            did = row.get("deal_id") or row.get("address") or row.get("id")
            if did:
                id_to_row[did] = row
    for i, did in enumerate(deal_ids):
        r = int(ranks[i])
        entry = {
            "deal_id": did,
            "rank": r,
            "non_dominated": r == 1,
            "layer": r,
        }
        src = id_to_row.get(did, {})
        for k in key_metrics:
            if k in src:
                try:
                    entry[k] = float(src[k])
                except (TypeError, ValueError):
                    entry[k] = src[k]
        for extra in ("address", "location_score", "vacancy_risk", "days_on_market"):
            if extra in src and extra not in entry:
                entry[extra] = src[extra]
        results.append(entry)
    results.sort(key=lambda x: (x["rank"], x["deal_id"]))
    return results

def write_results_csv(results: List[Dict], path: Path):
    if not results:
        return
    fieldnames = list(results[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(results)

def write_results_json(results: List[Dict], path: Path, meta: dict | None = None):
    payload = {
        "ok": True,
        "promote_ready": False,
        "n": len(results),
        "n_non_dominated": sum(1 for r in results if r["non_dominated"]),
        "results": results,
        "non_claims": [
            "Structural weak-dominance sieve only",
            "Not investment advice",
            "Not a prediction or valuation model",
        ],
    }
    if meta:
        payload["meta"] = {k: meta[k] for k in ("obj1", "obj2", "n", "profile") if k in meta}
    path.write_text(json.dumps(payload, indent=2))

def print_summary(results: List[Dict], top_k: int = 15):
    nd = [r for r in results if r["non_dominated"]]
    print(f"Non-dominated (rank-1) deals: {len(nd)} / {len(results)}")
    print("-" * 72)
    cols = ["rank", "deal_id", "non_dominated", "cap_rate", "cash_on_cash", "risk_score"]
    header = "  ".join(f"{c:>14}" for c in cols)
    print(header)
    for r in results[:top_k]:
        line = "  ".join(f"{str(r.get(c, ''))[:14]:>14}" for c in cols)
        print(line)
    if len(results) > top_k:
        print(f"... ({len(results) - top_k} more)")
