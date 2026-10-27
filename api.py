"""Flask REST API: 9 endpoints over the service layer."""
import sqlite3
from flask import Flask, jsonify, request, g
from . import db, services


def create_app(db_path="restaurant.db"):
    app = Flask(__name__)
    app.config["DB_PATH"] = db_path

    def conn():
        if "conn" not in g:
            g.conn = db.connect(app.config["DB_PATH"])
        return g.conn

    @app.teardown_appcontext
    def _close(_):
        c = g.pop("conn", None)
        if c is not None:
            c.close()

    @app.errorhandler(sqlite3.IntegrityError)
    def _integrity(e):
        return jsonify(error=str(e)), 409

    @app.errorhandler(ValueError)
    @app.errorhandler(KeyError)
    def _bad(e):
        return jsonify(error=str(e)), 400

    @app.get("/menu")
    def menu():
        rows = conn().execute("SELECT * FROM v_item_margin ORDER BY category, name").fetchall()
        return jsonify([dict(r) for r in rows])

    @app.post("/orders")
    def create_order():
        b = request.get_json(force=True)
        oid = services.place_order(conn(), b["table_id"], b["staff_id"],
                                   [(i["item_id"], i["quantity"]) for i in b["items"]], b.get("customer_id"))
        return jsonify(order_id=oid, **services.order_total(conn(), oid)), 201

    @app.get("/orders/<int:oid>")
    def get_order(oid):
        lines = conn().execute("SELECT m.name, oi.quantity, oi.unit_price FROM order_items oi "
                               "JOIN menu_items m USING(item_id) WHERE order_id=?", (oid,)).fetchall()
        if not lines:
            return jsonify(error="not found"), 404
        return jsonify(order_id=oid, lines=[dict(l) for l in lines], **services.order_total(conn(), oid))

    @app.post("/orders/<int:oid>/pay")
    def pay(oid):
        b = request.get_json(force=True)
        total = services.pay_order(conn(), oid, b["method"], b.get("tip", 0))
        return jsonify(order_id=oid, paid=total)

    @app.post("/reservations")
    def reserve():
        b = request.get_json(force=True)
        rid = services.reserve_table(conn(), b["customer_id"], b["table_id"], b["party_size"], b["reserved_for"])
        return jsonify(reservation_id=rid), 201

    @app.get("/inventory/low-stock")
    def low():
        return jsonify(services.low_stock(conn()))

    @app.get("/reports/daily")
    def daily():
        rows = conn().execute("SELECT * FROM v_daily_revenue ORDER BY day DESC LIMIT ?",
                              (int(request.args.get("days", 7)),)).fetchall()
        return jsonify([dict(r) for r in rows])

    @app.get("/reports/<name>")
    def report(name):
        q = db.analytics_queries().get(name)
        if q is None:
            return jsonify(error="unknown report", available=list(db.analytics_queries())), 404
        return jsonify([dict(r) for r in conn().execute(q).fetchall()])

    @app.get("/health")
    def health():
        return jsonify(status="ok", tables=conn().execute(
            "SELECT COUNT(*) c FROM sqlite_master WHERE type='table'").fetchone()["c"])

    return app


if __name__ == "__main__":
    create_app().run(debug=False, port=5000)
