# Real-Estate Deal Sieve

**Thin multi-objective ranking filter for real-estate and private-market deals.**

Isolates the weak-dominance (non-dominated) frontier from competing objectives such as cap rate / cash-on-cash versus risk / liquidity / stress.

Powered by [PrymGyroSort](https://github.com/HeywoodGeblomi/PrymGyroSort) + [GyroRank](https://github.com/HeywoodGeblomi/GyroRank).

## What the MVP does

1. Upload or provide a CSV of deals (cap_rate, cash_on_cash, risk_score, liquidity_score, vacancy_risk, etc.).
2. Map selected columns into an N×2 objective matrix (lower = better after normalization).
3. Rank by exact weak dominance.
4. Return ranked list + non-dominated flag + basic stress view + (later) Pareto visualization.

Deliberately narrow. No portfolio optimization, no machine-learning predictions, no automatic scraping, no χ layers.

## Honesty (mandatory)

See **[NON_CLAIMS.md](NON_CLAIMS.md)**.

- Structural execution sieve only.
- Not investment advice. Not a valuation model. Not alpha. Not a “best deal” oracle.
- Does not predict future returns, occupancy, or exit multiples.
- EXTERNAL-clean / no-χ. Ranking is pure weak-dominance on the supplied objectives.
- `promote_ready = false` for any commercial “recommended investment” claim.

## Quick start (local CLI)

```bash
# From the real-estate-deal-sieve/ root

# Full end-to-end demo (adapter → rank → format → stress view)
python scripts/run_local_demo.py

# Or step-by-step
python adapter/csv_to_matrix.py \
  --csv data/sample_deals.csv \
  --obj1 cap_rate --obj1-higher \
  --obj2 risk_score \
  --out-dir output --profile cashflow

# Ranking uses pure-Python weak-dominance by default (exact for M=2).
# Optional: set PRYM_GYRO_SORT_ROOT to a sibling PrymGyroSort checkout for native GyroRank.
```

## Profiles (via column_mapper)

- cashflow / cash_on_cash focused
- balanced
- appreciation
- stress_resistant (rates / vacancy / exit pressure)
- liquidity

## Stack

- Adapter + presentation: Python
- Ranking core: existing PrymGyroSort / GyroRank (or pure-Python fallback)
- Web (next): Streamlit or FastAPI + HTMX
- No re-implementation of the ranking kernel.

## Credits

Ranking kernel: GyroRank / PrymGyroSort (Heywood Geblomi / THE BEASTIE BOYZ)  
Real-estate domain adapter: THE BEASTIE BOYZ

## License

MIT
