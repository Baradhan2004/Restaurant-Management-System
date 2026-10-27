# Restaurant Management System | Flask + SQLite

A small REST backend for restaurant menu browsing and order creation, backed by a normalized relational schema. It includes synthetic seed data, constraints and indexes, transaction-backed order creation, API tests, and a Docker image.

## Features
- Seven related tables: customers, dining tables, menu items, reservations, orders, order items, and payments.
- Foreign keys, check constraints, unique constraints, and indexes for reservation/time and customer/order lookups.
- `GET /menu`, `POST /orders`, `GET /orders/<id>`, and `GET /health`.
- Order totals are calculated from database prices, not client-supplied amounts; order and line items are inserted in one SQLite transaction.
- Pytest integration tests for menu, order totals, invalid quantity, and unknown customer.

## Run locally
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate | macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -c "import app; app.init_db()"
python -c "import sqlite3; c=sqlite3.connect('restaurant.db'); c.executescript(open('sql/seed.sql').read()); c.commit()"
python app.py
pytest -q
```
API base URL: `http://127.0.0.1:5000`. Example:
```bash
curl http://127.0.0.1:5000/menu
curl -X POST http://127.0.0.1:5000/orders -H 'Content-Type: application/json' -d '{"customer_id":1,"items":[{"item_id":2,"quantity":2}]}'
```

## Docker
```bash
docker build -t restaurant-api .
docker run --rm -p 5000:5000 -v restaurant-data:/data restaurant-api
```

## Scope and next steps
This is a portfolio/demo backend, not a production POS. Reservations schema is present but conflict prevention endpoints are not implemented; payment records are schema-only and no real payment provider is connected. Before production, add authentication/roles, request rate limits, idempotency keys, migrations, audit logs, reservation overlap constraints in a transaction, and secure payment-provider integration. All seeded people and transactions are synthetic.
