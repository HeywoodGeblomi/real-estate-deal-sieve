#!/usr/bin/env python3
"""Thin ranking wrapper for Real-Estate Deal Sieve.
Prefer native GyroRank via PrymGyroSort; pure-Python weak-dominance fallback for zero-dep MVP.
EXTERNAL-clean / no-χ. promote_ready=false.
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple
import numpy as np

def pure_python_weak_dominance(X: np.ndarray) -> np.ndarray:
    """Exact 2-obj weak-dominance layers. Lower values better. rank 1 = non-dominated."""
    n = X.shape[0]
    ranks = np.zeros(n, dtype=np.int32)
    remaining = np.ones(n, dtype=bool)
    layer = 1
    while remaining.any():
        idx = np.flatnonzero(remaining)
        front = []
        for i in idx:
            dominated = False
            for j in idx:
                if i == j:
                    continue
                if (X[j, 0] <= X[i, 0] and X[j, 1] <= X[i, 1]) and (
                    X[j, 0] < X[i, 0] or X[j, 1] < X[i, 1]
                ):
                    dominated = True
                    break
            if not dominated:
                front.append(i)
        if not front:
            ranks[remaining] = layer
            break
        for i in front:
            ranks[i] = layer
            remaining[i] = False
        layer += 1
    return ranks

def load_matrix_and_meta(out_dir: Path) -> Tuple[np.ndarray, dict]:
    matrix_path = out_dir / "matrix.bin"
    meta_path = out_dir / "meta.json"
    if not matrix_path.is_file() or not meta_path.is_file():
        raise FileNotFoundError(f"Missing matrix.bin or meta.json in {out_dir}")
    meta = json.loads(meta_path.read_text())
    n = int(meta["n"])
    raw = np.fromfile(matrix_path, dtype=np.float64)
    if raw.size != n * 2:
        raise ValueError(f"Size mismatch: {raw.size} floats vs expected {n*2}")
    X = raw.reshape(n, 2)
    if not np.isfinite(X).all():
        raise ValueError("matrix contains NaN/Inf")
    return np.ascontiguousarray(X, dtype=np.float64), meta

def rank_via_prym_cli(matrix_path: Path, n: int, prym_root: Optional[Path] = None) -> Optional[np.ndarray]:
    candidates = []
    if prym_root:
        candidates.append(prym_root)
    env = os.environ.get("PRYM_GYRO_SORT_ROOT")
    if env:
        candidates.append(Path(env))
    here = Path(__file__).resolve().parents[1]
    candidates.append(here.parent / "PrymGyroSort")
    candidates.append(Path.home() / "projects" / "PrymGyroSort")

    for root in candidates:
        cli = root / "python" / "prym_sieve_cli.py"
        if cli.is_file():
            try:
                out_tmp = matrix_path.parent / "_rank_tmp"
                out_tmp.mkdir(exist_ok=True)
                cmd = [
                    sys.executable, str(cli),
                    "--matrix", str(matrix_path),
                    "--n", str(n),
                    "--no-prefilter",
                    "--top-frac", "1.0",
                    "--out", str(out_tmp),
                    "--json",
                ]
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                ranks_path = out_tmp / "ranks.npy"
                if ranks_path.is_file():
                    ranks = np.load(ranks_path)
                    return ranks.astype(np.int32)
            except Exception:
                continue
    return None

def rank_matrix(X: np.ndarray, matrix_path: Optional[Path] = None, prefer_native: bool = True) -> np.ndarray:
    if prefer_native and matrix_path is not None:
        ranks = rank_via_prym_cli(matrix_path, X.shape[0])
        if ranks is not None and ranks.shape[0] == X.shape[0]:
            return ranks
    return pure_python_weak_dominance(X)

def rank_from_adapter_output(out_dir: Path, prefer_native: bool = True) -> Tuple[np.ndarray, dict]:
    X, meta = load_matrix_and_meta(out_dir)
    ranks = rank_matrix(X, matrix_path=out_dir / "matrix.bin", prefer_native=prefer_native)
    return ranks, meta
