"""Deterministic synthetic data generator (seed=42). Produces a realistic year of trading."""
import random
from datetime import datetime, timedelta

CATEGORIES = ["Starters", "Mains", "Biryani & Rice", "Breads", "Desserts", "Beverages"]
ITEMS = {
    "Starters": [("Paneer Tikka", 220, 85), ("Chicken 65", 260, 95), ("Veg Spring Roll", 180, 60), ("Gobi Manchurian", 190, 65), ("Fish Fingers", 290, 120), ("Mushroom Pepper Fry", 210, 80)],
    "Mains": [("Butter Chicken", 340, 130), ("Paneer Butter Masala", 290, 105), ("Dal Makhani", 240, 70), ("Chettinad Chicken", 330, 125), ("Veg Kurma", 220, 70), ("Mutton Rogan Josh", 420, 190)],
    "Biryani & Rice": [("Chicken Biryani", 320, 115), ("Mutton Biryani", 420, 185), ("Veg Biryani", 260, 85), ("Egg Fried Rice", 200, 60), ("Jeera Rice", 150, 40), ("Curd Rice", 130, 35)],
    "Breads": [("Butter Naan", 55, 14), ("Garlic Naan", 65, 17), ("Tandoori Roti", 35, 9), ("Parotta", 40, 11), ("Lachha Paratha", 60, 16), ("Kulcha", 60, 15)],
    "Desserts": [("Gulab Jamun", 90, 24), ("Rasmalai", 110, 34), ("Brownie Sundae", 160, 55), ("Kulfi", 100, 30), ("Payasam", 95, 28), ("Ice Cream Scoop", 80, 25)],
    "Beverages": [("Masala Chai", 40, 8), ("Filter Coffee", 50, 11), ("Fresh Lime Soda", 70, 14), ("Mango Lassi", 95, 26), ("Cold Coffee", 120, 32), ("Mineral Water", 30, 8)],
}
ROLES = ["manager"] * 2 + ["chef"] * 5 + ["waiter"] * 9 + ["cashier"] * 2 + ["host"] * 2
WEIGHTS_HOUR = {12: 6, 13: 10, 14: 7, 15: 2, 16: 1, 17: 2, 18: 4, 19: 10, 20: 13, 21: 9, 22: 4}


def seed(conn, n_orders=50000, n_customers=5000, days=365, rng_seed=42):
    rng = random.Random(rng_seed)
    start = datetime(2025, 1, 1)
    with conn:
        conn.executemany("INSERT INTO staff(full_name,role,hourly_wage,hired_on) VALUES (?,?,?,?)",
                         [(f"Staff {i+1}", r, round(rng.uniform(90, 400), 2), "2023-06-01") for i, r in enumerate(ROLES)])
        conn.executemany("INSERT INTO customers(full_name,phone,email) VALUES (?,?,?)",
                         [(f"Customer {i+1}", f"9{i:09d}", f"c{i+1}@example.com") for i in range(n_customers)])
        conn.executemany("INSERT INTO dining_tables(label,capacity) VALUES (?,?)",
                         [(f"T{i+1:02d}", rng.choice([2, 2, 4, 4, 4, 6, 8])) for i in range(30)])
        conn.executemany("INSERT INTO suppliers(name,phone,lead_days) VALUES (?,?,?)",
                         [(f"Supplier {i+1}", f"80000{i:05d}", rng.randint(1, 5)) for i in range(8)])
        conn.executemany("INSERT INTO ingredients(name,unit,stock_qty,reorder_level,supplier_id) VALUES (?,?,?,?,?)",
                         [(f"Ingredient {i+1}", rng.choice(["kg", "l", "pcs"]), 1e6, rng.uniform(50, 400), rng.randint(1, 8)) for i in range(40)])
        for c in CATEGORIES:
            conn.execute("INSERT INTO menu_categories(name) VALUES (?)", (c,))
        item_ids = []
        for cid, c in enumerate(CATEGORIES, start=1):
            for name, price, cost in ITEMS[c]:
                cur = conn.execute("INSERT INTO menu_items(category_id,name,price,cost) VALUES (?,?,?,?)", (cid, name, price, cost))
                item_ids.append((cur.lastrowid, price))
                for ing in rng.sample(range(1, 41), rng.randint(3, 5)):
                    conn.execute("INSERT INTO recipe_items VALUES (?,?,?)", (cur.lastrowid, ing, round(rng.uniform(0.02, 0.4), 3)))
        hours = list(WEIGHTS_HOUR); w = list(WEIGHTS_HOUR.values())
        waiters = [r[0] for r in conn.execute("SELECT staff_id FROM staff WHERE role='waiter'")]
        n_tables = 30
        for _ in range(n_orders):
            day = start + timedelta(days=rng.randrange(days))
            ts = day.replace(hour=rng.choices(hours, w)[0], minute=rng.randrange(60), second=rng.randrange(60))
            cust = rng.randint(1, n_customers) if rng.random() < 0.6 else None
            cur = conn.execute("INSERT INTO orders(table_id,customer_id,staff_id,opened_at) VALUES (?,?,?,?)",
                               (rng.randint(1, n_tables), cust, rng.choice(waiters), ts.strftime("%Y-%m-%d %H:%M:%S")))
            oid, subtotal = cur.lastrowid, 0.0
            for iid, price in rng.sample(item_ids, rng.randint(2, 6)):
                q = rng.choice([1, 1, 1, 2, 2, 3])
                conn.execute("INSERT INTO order_items(order_id,item_id,quantity,unit_price) VALUES (?,?,?,?)", (oid, iid, q, price))
                subtotal += q * price
            total = round(subtotal * 1.05, 2)
            paid = ts + timedelta(minutes=rng.randint(35, 90))
            conn.execute("INSERT INTO payments(order_id,method,amount,tip,paid_at) VALUES (?,?,?,?,?)",
                         (oid, rng.choices(["cash", "card", "upi"], [2, 3, 5])[0], total,
                          round(total * rng.choice([0, 0, 0.05, 0.1]), 2), paid.strftime("%Y-%m-%d %H:%M:%S")))
