# Phase 2 — Full Automation Architecture

## System Architecture

```
                        ┌─────────────┐
                        │  FastAPI App │
                        └──────┬──────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
   ┌──────▼──────┐    ┌────────▼────────┐  ┌───────▼────────┐
   │ Market Data │    │  Signal Engine  │  │  Risk Engine   │
   │  Service    │    │  (Strategies)   │  │  (Kill Switch) │
   └──────┬──────┘    └────────┬────────┘  └───────┬────────┘
          │                    │                    │
          └────────────────────▼────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   Order Executor     │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Broker Interface    │
                    │  Binance | AngelOne  │
                    └──────────┬──────────┘
                               │
               ┌───────────────┼───────────────┐
               │               │               │
         ┌─────▼────┐   ┌──────▼──────┐  ┌────▼──────┐
         │PostgreSQL│   │    Redis     │  │ Telegram  │
         │(trades)  │   │  (caching)   │  │  (alerts) │
         └──────────┘   └─────────────┘  └───────────┘
```

## Scaling to SaaS

### Step 1 — Multi-user support
- Add user auth (JWT)
- Per-user API key storage (encrypted)
- Per-user risk limits and strategies

### Step 2 — Strategy marketplace
- Let users add custom strategies via UI
- Add backtest runner per user

### Step 3 — Subscription tiers
- Free: Paper trading only, 1 strategy
- Pro: Live trading, 3 strategies, Telegram alerts
- Enterprise: Custom strategies, white-label

### Step 4 — Infrastructure
- Kubernetes for scaling
- Separate microservices per broker
- Event-driven with Kafka
- Time-series DB (TimescaleDB) for market data

## Common Mistakes to Avoid

1. Going live without paper trading for 1+ week
2. Not testing SL/TP execution separately
3. Missing API rate limits (Binance = 1200 req/min)
4. No reconnect logic on WebSocket disconnect
5. Storing API keys in code or git
6. Not having a circuit breaker / kill switch
7. Optimizing strategy only on recent data (overfitting)
8. Ignoring exchange fees in backtests (~0.1% per trade on Binance)
