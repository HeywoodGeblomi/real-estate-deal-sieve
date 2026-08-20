#!/usr/bin/env python3
"""
Real-Estate Deal Sieve — CSV → Objective Matrix Adapter

Converts a deal spreadsheet into the N×2 matrix format expected by PrymGyroSort / GyroRank.
Lower values = better after normalization.

EXTERNAL-clean / no-χ. Structural sieve only. promote_ready=false.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import numpy as np

ADAPTER_VERSION = "0.1.0-re-sieve"
PROMOTE_READY = False


def load_csv(path: Path) -> Tuple[List[Dict], List[str]]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        headers = list(reader.fieldnames or [])
    if not rows:
        raise ValueError(f"Empty CSV: {path}")
    return rows, headers


def normalize_column(values: List[float], higher_is_better: bool) -> np.ndarray:
    """Turn a column into 'lower = better' scores in roughly [0, 1]."""
    arr = np.asarray(values, dtype=np.float64)
    if not np.isfinite(arr).all():
        raise ValueError("Column contains NaN or Inf")
    if higher_is_better:
        arr = -arr  # invert so higher original becomes lower (better) score
    min_v, max_v = float(arr.min()), float(arr.max())
    if max_v - min_v > 1e-12:
        arr = (arr - min_v) / (max_v - min_v)
    else:
        arr = np.zeros_like(arr)
    return arr


def build_matrix(
    rows: List[Dict],
    obj1_col: str,
    obj1_higher_better: bool,
    obj2_col: str,
    obj2_higher_better: bool,
    id_cols: Optional[List[str]] = None,
) -> Tuple[np.ndarray, List[str]]:
    """
    Returns:
        matrix: shape (N, 2) float64, lower = better
        deal_ids: list of identifiers for later joining
    """
    if id_cols is None:
        id_cols = ["deal_id", "address", "id", "ticker"]

    deal_ids: List[str] = []
    obj1_vals: List[float] = []
    obj2_vals: List[float] = []

    for i, row in enumerate(rows):
        deal_id = None
        for c in id_cols:
            if c in row and row[c] not in (None, ""):
                deal_id = str(row[c]).strip()
                break
        if deal_id is None:
            deal_id = f"deal_{i}"
        deal_ids.append(deal_id)

        try:
            v1 = float(row[obj1_col])
            v2 = float(row[obj2_col])
        except (KeyError, ValueError, TypeError) as e:
            raise ValueError(
                f"Row {i} (id={deal_id}) missing or invalid values for "
                f"{obj1_col}/{obj2_col}: {e}"
            ) from e

        if not (np.isfinite(v1) and np.isfinite(v2)):
            raise ValueError(f"Row {i} (id={deal_id}) has non-finite objective values")

        obj1_vals.append(v1)
        obj2_vals.append(v2)

    col1 = normalize_column(obj1_vals, higher_is_better=obj1_higher_better)
    col2 = normalize_column(obj2_vals, higher_is_better=obj2_higher_better)

    matrix = np.ascontiguousarray(np.column_stack([col1, col2]), dtype=np.float64)
    return matrix, deal_ids


def save_matrix_bin(matrix: np.ndarray, path: Path) -> None:
    """Save as raw float64 binary (PrymGyroSort contract)."""
    if matrix.ndim != 2 or matrix.shape[1] != 2:
        raise ValueError(f"matrix must be (N,2); got {matrix.shape}")
    if matrix.dtype != np.float64 or not matrix.flags["C_CONTIGUOUS"]:
        matrix = np.ascontiguousarray(matrix, dtype=np.float64)
    matrix.tofile(path)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=f"Real-Estate Deal Sieve CSV → matrix adapter {ADAPTER_VERSION}"
    )
    parser.add_argument("--csv", required=True, help="Input CSV of deals")
    parser.add_argument("--obj1", required=True, help="Column name for objective 1")
    parser.add_argument(
        "--obj1-higher",
        action="store_true",
        help="Set if higher values are better for obj1 (default: lower better)",
    )
    parser.add_argument("--obj2", required=True, help="Column name for objective 2")
    parser.add_argument(
        "--obj2-higher",
        action="store_true",
        help="Set if higher values are better for obj2",
    )
    parser.add_argument("--out-dir", default="output", help="Output directory")
    parser.add_argument(
        "--profile",
        default="custom",
        help="Optional label written into meta (e.g. cashflow, balanced, stress)",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not csv_path.is_file():
        print(f"ERROR: CSV not found: {csv_path}")
        return 2

    rows, headers = load_csv(csv_path)
    print(f"Loaded {len(rows)} deals. Columns: {headers}")

    try:
        matrix, deal_ids = build_matrix(
            rows,
            obj1_col=args.obj1,
            obj1_higher_better=args.obj1_higher,
            obj2_col=args.obj2,
            obj2_higher_better=args.obj2_higher,
        )
    except ValueError as e:
        print(f"ERROR: {e}")
        return 2

    n = int(matrix.shape[0])
    matrix_path = out_dir / "matrix.bin"
    meta_path = out_dir / "meta.json"

    save_matrix_bin(matrix, matrix_path)

    meta = {
        "ok": True,
        "adapter_version": ADAPTER_VERSION,
        "domain": "real_estate",
        "profile": args.profile,
        "n": n,
        "m": 2,
        "deal_ids": deal_ids,
        "obj1": args.obj1,
        "obj1_higher_better": bool(args.obj1_higher),
        "obj2": args.obj2,
        "obj2_higher_better": bool(args.obj2_higher),
        "matrix_file": matrix_path.name,
        "source": str(csv_path),
        "promote_ready": PROMOTE_READY,
        "non_claims": "Structural weak-dominance sieve only. Not investment advice.",
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"Wrote {matrix_path}  (shape {matrix.shape})")
    print(f"Wrote {meta_path}")
    print("Next: feed matrix.bin into PrymGyroSort ranking CLI / Docker or core/ranker.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
