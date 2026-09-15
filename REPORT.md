# StockSimulator Report

StockSimulator is a Bursa Malaysia paper-trading web application with registration, login, trading, portfolio tracking, news, and AI Chinese summaries.

## Architecture

User -> Flask Web App -> SQLite / Simulated Bursa Data / News APIs / OpenAI -> Flask Web App -> User.

## API

`GET /api/quote/<ticker>`, `GET /api/history/<ticker>`, `GET /api/search?q=1155.KL`, and `GET /api/news/<ticker>`.

## Future work

Add pytest, admin competition reset, a larger Bursa Malaysia symbol catalogue, export reports, and risk metrics.
