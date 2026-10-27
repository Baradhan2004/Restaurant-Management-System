# Restaurant Management System

A relational backend for a dine-in restaurant: ordering, bill-of-materials inventory, reservations, payments, loyalty and analytics.
Business rules live **inside the database** (6 triggers, 12 CHECK/FK-constrained tables), with a Python service layer and a 9-endpoint Flask REST API on top.
Stack: **SQL (SQLite) · Python · Flask · Figma (UI prototypes)**

## Architecture
```
Figma prototypes ──> Flask REST API (rms/api.py) ──> service layer (rms/services.py, atomic transactions)
                                                         │
                         SQLite: 12 tables · 6 triggers · 4 views · 8 indexes · window-function reports
```

## Schema (3NF)
`staff, customers, dining_tables, menu_categories, menu_items, suppliers, ingredients, recipe_items (BOM), reservations, orders, order_items, payments`

| Trigger | Rule enforced in-database |
|---|---|
| `trg_deduct_stock` | ordering an item deducts every recipe ingredient × quantity |
| `trg_close_order` | payment marks the order `paid` and stamps `closed_at` |
| `trg_loyalty` | 1 loyalty point per 10 currency units paid |
| `trg_party_fits` | party size must not exceed table capacity |
| `trg_no_double_booking` | no two confirmed bookings on one table within 90 min |
| `trg_item_available` | unavailable menu items cannot be sold (whole order rolls back) |

## API
`GET /menu` · `POST /orders` · `GET /orders/<id>` · `POST /orders/<id>/pay` · `POST /reservations` · `GET /inventory/low-stock` · `GET /reports/daily` · `GET /reports/<name>` · `GET /health`
Errors: `400` bad input, `404` unknown, `409` constraint/trigger violation. GST (5%) is applied at billing.

## Run
```bash
pip install -r requirements.txt
python -m unittest discover -s tests -v        # 10 tests
python scripts/benchmark.py 50000              # index benchmark on 50k orders
python scripts/run_reports.py                  # window-function analytics
python -c "from rms import db, seed; c=db.connect('restaurant.db'); db.init_db(c); seed.seed(c); c.close()"
python -m rms.api                              # http://localhost:5000
```

## Measured results (seeded synthetic year: 50,000 orders · 200,413 order lines · 5,000 customers; this machine)
| Query | Full scan | Indexed | Speed-up | Plan change |
|---|---|---|---|---|
| items of one order | 7.33 ms | 0.004 ms | **~2,058×** | SCAN → SEARCH `idx_order_items_order` |
| one customer's history | 2.90 ms | 0.004 ms | **~687×** | SCAN → COVERING INDEX |
| one day's orders | 3.55 ms | 0.006 ms | **~563×** | SCAN → range SEARCH on `opened_at` |
| revenue for a month | 4.19 ms | 1.65 ms | 3× | SCAN → range SEARCH |
| sales of one item | 8.60 ms | 2.31 ms | 4× | SCAN → SEARCH |

Seeding 250k+ rows with all triggers firing took 10.2 s; building 8 indexes took 259 ms. Timings vary by machine; rerun `scripts/benchmark.py`. Full logs in `docs/`.
Analytics (`sql/05_analytics.sql`): per-category top-3 by revenue (`RANK() OVER PARTITION`), 7-day moving average, peak hours, RFM quartiles (`NTILE`), waiter leaderboard. All five report queries run in 29-130 ms on 50k orders.

## Tests (10, all passing)
Trigger behaviour (stock deduction, loyalty, double-booking incl. exact 90-minute boundary, capacity, unavailable-item atomic rollback), FK enforcement, GST maths, revenue reconciliation between `payments` and `v_daily_revenue`, and the REST flow (create → pay → double-pay `409` → unknown order `404`).

## UI design (Figma)
See `docs/ui-design.md` for the screen inventory and flows to prototype in Figma; add your Figma link here.
