# Real-Estate Deal Sieve

**Thin multi-objective ranking filter for real-estate and private-market deals.**

Isolates the weak-dominance (non-dominated) frontier from competing objectives such as cap rate / cash-on-cash versus risk / liquidity / stress.

Powered by [PrymGyroSort](https://github.com/HeywoodGeblomi/PrymGyroSort) + [GyroRank](https://github.com/HeywoodGeblomi/GyroRank).

## What it does

1. Take a CSV of deals (cap_rate, cash_on_cash, risk_score, liquidity_score, vacancy_risk, …).
2. Map selected columns into an N×2 objective matrix (lower = better after normalization).
3. Rank by exact weak dominance.
4. Return ranked list + non-dominated flag + deterministic stress view.

Deliberately narrow. No portfolio optimization, no ML predictions, no scraping, no χ layers.

## Honesty (mandatory)

See **[NON_CLAIMS.md](NON_CLAIMS.md)**.

- Structural execution sieve only.
- Not investment advice. Not a valuation model. Not alpha. Not a “best deal” oracle.
- Does not predict future returns, occupancy, or exit multiples.
- EXTERNAL-clean / no-χ. Ranking is pure weak-dominance on the supplied objectives.
- `promote_ready = false` for any commercial “recommended investment” claim.

## Two ways to use it

### 1. Self-serve (Streamlit)

```bash
git clone https://github.com/HeywoodGeblomi/real-estate-deal-sieve
cd real-estate-deal-sieve
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

Or deploy to Streamlit Community Cloud / Railway — see **[DEPLOY.md](DEPLOY.md)**.

### 2. Concierge (manual ranking service)

See **[CONCIERGE.md](CONCIERGE.md)**.

Send a deal CSV → receive ranked non-dominated list + stress view ($49 / $99). Faster path to first revenue.

### Local CLI / verification

```bash
python scripts/verify.py          # must PASS
python scripts/run_local_demo.py  # sample deals → ranked table + stress
```

## Profiles

- cashflow / cash_on_cash focused
- balanced
- appreciation
- stress_resistant
- liquidity
- custom (any two columns)

## Stack

- Ranking: pure-Python exact 2-obj weak-dominance (optional native GyroRank)
- Web: Streamlit
- No re-implementation of the ranking kernel

## Credits

Ranking kernel: GyroRank / PrymGyroSort (Heywood Geblomi / THE BEASTIE BOYZ)  
Real-estate domain adapter + web + concierge: THE BEASTIE BOYZ

## License

MIT
