import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from rms import db, seed

conn = db.connect(":memory:"); db.init_db(conn); seed.seed(conn, n_orders=50000)
for name, q in db.analytics_queries().items():
    t = time.perf_counter(); rows = conn.execute(q).fetchall(); ms = (time.perf_counter() - t) * 1000
    print(f"\n== {name}  ({len(rows)} rows, {ms:.0f} ms)")
    for r in rows[:6]:
        print("  ", dict(r))
print("\nLow-stock ingredients:", conn.execute("SELECT COUNT(*) FROM v_low_stock").fetchone()[0])
print("Revenue:", conn.execute("SELECT ROUND(SUM(amount),2) FROM payments").fetchone()[0])
