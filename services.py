"""Business operations. Invariants live in SQL triggers; this layer orchestrates transactions."""
from datetime import datetime


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def place_order(conn, table_id, staff_id, items, customer_id=None, opened_at=None):
    """items: list of (item_id, quantity). Atomic: all lines succeed or none do."""
    if not items:
        raise ValueError("order must contain at least one item")
    with conn:  # single transaction
        cur = conn.execute(
            "INSERT INTO orders(table_id, customer_id, staff_id, opened_at) VALUES (?,?,?,?)",
            (table_id, customer_id, staff_id, opened_at or _now()))
        oid = cur.lastrowid
        for item_id, qty in items:
            price = conn.execute("SELECT price FROM menu_items WHERE item_id=?", (item_id,)).fetchone()
            if price is None:
                raise KeyError(f"unknown menu item {item_id}")
            conn.execute(
                "INSERT INTO order_items(order_id,item_id,quantity,unit_price) VALUES (?,?,?,?)",
                (oid, item_id, qty, price["price"]))
        conn.execute("UPDATE dining_tables SET status='occupied' WHERE table_id=?", (table_id,))
    return oid


def order_total(conn, order_id, gst_rate=0.05):
    row = conn.execute(
        "SELECT COALESCE(SUM(quantity*unit_price),0) AS s FROM order_items WHERE order_id=?",
        (order_id,)).fetchone()
    subtotal = round(row["s"], 2)
    tax = round(subtotal * gst_rate, 2)
    return {"subtotal": subtotal, "gst": tax, "total": round(subtotal + tax, 2)}


def pay_order(conn, order_id, method, tip=0.0, paid_at=None):
    total = order_total(conn, order_id)["total"]
    if total <= 0:
        raise ValueError("cannot pay an empty order")
    with conn:
        conn.execute("INSERT INTO payments(order_id,method,amount,tip,paid_at) VALUES (?,?,?,?,?)",
                     (order_id, method, total, tip, paid_at or _now()))
        tid = conn.execute("SELECT table_id FROM orders WHERE order_id=?", (order_id,)).fetchone()["table_id"]
        conn.execute("UPDATE dining_tables SET status='free' WHERE table_id=?", (tid,))
    return total


def reserve_table(conn, customer_id, table_id, party_size, reserved_for):
    with conn:
        cur = conn.execute(
            "INSERT INTO reservations(customer_id,table_id,party_size,reserved_for) VALUES (?,?,?,?)",
            (customer_id, table_id, party_size, reserved_for))
    return cur.lastrowid


def low_stock(conn):
    return [dict(r) for r in conn.execute("SELECT * FROM v_low_stock ORDER BY stock_qty - reorder_level")]
