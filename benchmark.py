"""Measure the effect of secondary indexes on analytical queries (median of 5 runs)."""
import statistics, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from rms import db, seed

QUERIES = {
    "order lookup by id's items": "SELECT SUM(quantity*unit_price) FROM order_items WHERE order_id = 31337",
    "customer order history": "SELECT COUNT(*), SUM(p.amount) FROM orders o JOIN payments p USING(order_id) WHERE o.customer_id = 1234",
    "one day's orders": "SELECT COUNT(*) FROM orders WHERE opened_at >= '2025-06-15' AND opened_at < '2025-06-16'",
    "revenue for June": "SELECT SUM(amount) FROM payments WHERE paid_at >= '2025-06-01' AND paid_at < '2025-07-01'",
    "item sales rollup": "SELECT item_id, SUM(quantity) FROM order_items WHERE item_id = 17 GROUP BY item_id",
}


def timeit(conn, sql, runs=5):
    ts = []
    for _ in range(runs):
        t = time.perf_counter(); conn.execute(sql).fetchall(); ts.append((time.perf_counter() - t) * 1000)
    return statistics.median(ts)


def plan(conn, sql):
    return " | ".join(r[3] for r in conn.execute("EXPLAIN QUERY PLAN " + sql))


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 50000
    conn = db.connect(":memory:")
    db.init_db(conn, with_indexes=False)
    t = time.perf_counter(); seed.seed(conn, n_orders=n); seed_s = time.perf_counter() - t
    counts = {t_: conn.execute(f"SELECT COUNT(*) FROM {t_}").fetchone()[0] for t_ in
              ["orders", "order_items", "payments", "customers", "menu_items"]}
    print(f"Seeded in {seed_s:.1f}s (triggers fired on every insert): {counts}")
    before = {k: (timeit(conn, q), plan(conn, q)) for k, q in QUERIES.items()}
    t = time.perf_counter(); db.add_indexes(conn); idx_s = time.perf_counter() - t
    print(f"Built 8 indexes in {idx_s*1000:.0f} ms\n")
    print(f"{'query':32s} {'no index':>10s} {'indexed':>10s} {'speedup':>9s}")
    for k, q in QUERIES.items():
        a, pa = before[k]; b = timeit(conn, q); pb = plan(conn, q)
        print(f"{k:32s} {a:9.2f}ms {b:9.3f}ms {a/b:8.0f}x")
        print(f"    plan before: {pa}\n    plan after : {pb}")
