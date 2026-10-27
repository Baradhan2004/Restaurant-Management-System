import sqlite3, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from rms import db, services, seed
from rms.api import create_app


def fresh(n=0):
    c = db.connect(":memory:"); db.init_db(c)
    seed.seed(c, n_orders=n, n_customers=50)
    return c


class TestTriggers(unittest.TestCase):
    def setUp(self):
        self.c = fresh()

    def test_stock_deducted_via_recipe(self):
        item = 1
        ing, qty = self.c.execute("SELECT ingredient_id, qty_per_unit FROM recipe_items WHERE item_id=?", (item,)).fetchone()
        before = self.c.execute("SELECT stock_qty FROM ingredients WHERE ingredient_id=?", (ing,)).fetchone()[0]
        services.place_order(self.c, 1, 3, [(item, 3)])
        after = self.c.execute("SELECT stock_qty FROM ingredients WHERE ingredient_id=?", (ing,)).fetchone()[0]
        self.assertAlmostEqual(before - after, 3 * qty, places=6)

    def test_payment_closes_order_and_awards_loyalty(self):
        oid = services.place_order(self.c, 1, 3, [(1, 2)], customer_id=5)
        total = services.pay_order(self.c, oid, "card")
        self.assertEqual(self.c.execute("SELECT status FROM orders WHERE order_id=?", (oid,)).fetchone()[0], "paid")
        self.assertEqual(self.c.execute("SELECT loyalty_points FROM customers WHERE customer_id=5").fetchone()[0], int(total // 10))

    def test_double_booking_rejected(self):
        services.reserve_table(self.c, 1, 1, 2, "2025-07-01 20:00:00")
        with self.assertRaises(sqlite3.IntegrityError):
            services.reserve_table(self.c, 2, 1, 2, "2025-07-01 21:00:00")
        services.reserve_table(self.c, 2, 1, 2, "2025-07-01 21:30:00")  # exactly 90 min later is allowed

    def test_party_too_large_rejected(self):
        cap = self.c.execute("SELECT capacity FROM dining_tables WHERE table_id=1").fetchone()[0]
        with self.assertRaises(sqlite3.IntegrityError):
            services.reserve_table(self.c, 1, 1, cap + 1, "2025-07-02 20:00:00")

    def test_unavailable_item_rejected_and_order_rolled_back(self):
        self.c.execute("UPDATE menu_items SET is_available=0 WHERE item_id=2"); self.c.commit()
        n = self.c.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        with self.assertRaises(sqlite3.IntegrityError):
            services.place_order(self.c, 1, 3, [(1, 1), (2, 1)])
        self.assertEqual(self.c.execute("SELECT COUNT(*) FROM orders").fetchone()[0], n)  # atomic rollback

    def test_fk_enforced(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.c.execute("INSERT INTO orders(table_id,staff_id,opened_at) VALUES (999,1,'2025-01-01')")

    def test_gst(self):
        oid = services.place_order(self.c, 1, 3, [(1, 1)])
        t = services.order_total(self.c, oid)
        self.assertAlmostEqual(t["total"], round(t["subtotal"] * 1.05, 2), places=2)


class TestAnalyticsAndApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = fresh(2000)

    def test_all_reports_run(self):
        for name, q in db.analytics_queries().items():
            self.assertGreater(len(self.c.execute(q).fetchall()), 0, name)

    def test_revenue_reconciles(self):
        a = self.c.execute("SELECT ROUND(SUM(amount),2) FROM payments").fetchone()[0]
        b = self.c.execute("SELECT ROUND(SUM(revenue),2) FROM v_daily_revenue").fetchone()[0]
        self.assertAlmostEqual(a, b, places=1)

    def test_api_flow(self):
        import tempfile, os
        path = os.path.join(tempfile.mkdtemp(), "t.db")
        c = db.connect(path); db.init_db(c); seed.seed(c, n_orders=0, n_customers=20); c.close()
        cl = create_app(path).test_client()
        self.assertEqual(cl.get("/health").get_json()["tables"], 12)
        r = cl.post("/orders", json={"table_id": 1, "staff_id": 10, "items": [{"item_id": 1, "quantity": 2}]})
        self.assertEqual(r.status_code, 201)
        oid = r.get_json()["order_id"]
        self.assertEqual(cl.post(f"/orders/{oid}/pay", json={"method": "upi", "tip": 20}).status_code, 200)
        self.assertEqual(cl.post(f"/orders/{oid}/pay", json={"method": "upi"}).status_code, 409)  # double pay
        self.assertEqual(cl.get("/orders/99999").status_code, 404)
        self.assertEqual(cl.get("/reports/nope").status_code, 404)


if __name__ == "__main__":
    unittest.main(verbosity=2)
