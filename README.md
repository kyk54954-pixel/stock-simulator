# StockSimulator

Flask + SQLite Bursa Malaysia paper-trading system with user accounts, buy/sell trading, portfolio valuation, delayed Yahoo Finance market data, Chart.js charts, Malaysia finance news, AI Chinese summaries, leaderboard, sortable tables, and a responsive UI.

Run locally: create and activate a virtual environment, install `requirements.txt`, then run `app.py`. Open http://127.0.0.1:5000. Add `NEWS_API_KEY` and `OPENAI_API_KEY` in `.env` when available.

## Publish a public link (Render)

This is a Flask application, so it needs a Python web-service host rather than GitHub Pages.

1. Create a **new private GitHub repository** and upload this project. Do not upload `.env`, `database.db`, or `instance/`; `.gitignore` excludes them.
2. In Render, create a PostgreSQL database and copy its **Internal Database URL**.
3. Create a Web Service from the GitHub repository. Render can use `render.yaml`, or set the build command to `pip install -r requirements.txt` and the start command to `gunicorn "app:create_app()"`.
4. In the Web Service's environment variables, set `DATABASE_URL` to the PostgreSQL URL. Set `SECRET_KEY` to a long random value. Add `NEWS_API_KEY`, `FINNHUB_API_KEY`, and `OPENAI_API_KEY` only if those features are needed.
5. Deploy. The application creates its tables automatically at first start. Render will show the public `https://...onrender.com` URL.

The database is intentionally not committed to GitHub. A cloud PostgreSQL database preserves accounts and paper-trading history across redeployments.

## Delayed Bursa Malaysia Data

Quotes and charts are retrieved from Yahoo Finance through `yfinance` for the supported Bursa Malaysia symbols (for example, `1155.KL`). This is for personal coursework only: it is not an official Bursa feed, its timing and availability are not guaranteed, and it must not be used for live trading or redistributed commercially. The free feed does not reliably provide bid/ask values.

## Paper Trading UI

The app remains a paper-trading simulator and does not place real brokerage orders. The displayed order price is the latest available delayed quote.
