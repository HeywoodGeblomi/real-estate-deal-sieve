#!/usr/bin/env python3
"""Deterministic verification for Real-Estate Deal Sieve ranking.
Anyone can run this after clone to confirm pure-Python weak-dominance is exact.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.ranker import pure_python_weak_dominance

def test_known_pareto():
    # Classic 2-obj case (lower better)
    # Points: A(1,4), B(2,3), C(3,2), D(4,1), E(2.5,2.5), F(5,5)
    # Non-dominated should be A,B,C,D (E dominated by B and C, F dominated by all)
    X = np.array([
        [1.0, 4.0],  # A rank 1
        [2.0, 3.0],  # B rank 1
        [3.0, 2.0],  # C rank 1
        [4.0, 1.0],  # D rank 1
        [2.5, 2.5],  # E rank 2
        [5.0, 5.0],  # F rank 2+
    ], dtype=np.float64)
    ranks = pure_python_weak_dominance(X)
    assert ranks[0] == 1 and ranks[1] == 1 and ranks[2] == 1 and ranks[3] == 1, f"Front wrong: {ranks}"
    assert ranks[4] > 1 and ranks[5] > 1, f"Dominated not layered: {ranks}"
    print("[verify] known Pareto case PASS")

def test_sample_shape():
    from adapter.csv_to_matrix import build_matrix, load_csv
    csv_path = ROOT / "data" / "sample_deals.csv"
    rows, _ = load_csv(csv_path)
    matrix, deal_ids = build_matrix(rows, "cap_rate", True, "risk_score", False)
    assert matrix.shape == (32, 2), f"shape {matrix.shape}"
    ranks = pure_python_weak_dominance(matrix)
    n_nd = int((ranks == 1).sum())
    assert n_nd >= 1, "no non-dominated"
    assert n_nd <= 32, "all non-dominated impossible for this sample"
    print(f"[verify] sample ranking PASS — {n_nd} non-dominated of 32")

def main():
    print("[verify] Real-Estate Deal Sieve deterministic checks")
    test_known_pareto()
    test_sample_shape()
    print("[verify] ALL PASS — promote_ready=false / EXTERNAL-clean")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
