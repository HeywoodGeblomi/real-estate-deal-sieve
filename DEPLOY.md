# Deploy / Run Real-Estate Deal Sieve

## Local Streamlit

```bash
git clone https://github.com/HeywoodGeblomi/real-estate-deal-sieve
cd real-estate-deal-sieve
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

Open the local URL shown in the terminal (usually http://localhost:8501).

## Streamlit Community Cloud (free)

1. Fork or connect this repo at https://share.streamlit.io
2. Main file path: `app/streamlit_app.py`
3. Python version: 3.10+
4. Deploy.

Free tier is sufficient for the MVP. Add a simple free-deal limit in the app if you want to gate larger files later.

## Railway / Render / Fly.io

Any of these work with a basic Dockerfile or native Python buildpack. Keep the ranking pure-Python for zero native-binding friction on free tiers.

## Concierge path

See [CONCIERGE.md](CONCIERGE.md). No deploy required — run the CLI / demo path on client CSVs and return results manually.

## Honesty reminder

`promote_ready = false`. Structural weak-dominance sieve only. Not investment advice. EXTERNAL-clean / no-χ.
