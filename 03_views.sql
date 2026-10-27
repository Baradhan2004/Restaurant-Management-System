CREATE VIEW v_order_totals AS
SELECT o.order_id, o.opened_at, o.status, o.table_id, o.staff_id, o.customer_id,
       SUM(oi.quantity * oi.unit_price) AS subtotal,
       SUM(oi.quantity) AS item_count
  FROM orders o JOIN order_items oi ON oi.order_id = o.order_id
 GROUP BY o.order_id;

CREATE VIEW v_daily_revenue AS
SELECT date(p.paid_at) AS day, COUNT(*) AS orders, ROUND(SUM(p.amount),2) AS revenue,
       ROUND(AVG(p.amount),2) AS avg_ticket, ROUND(SUM(p.tip),2) AS tips
  FROM payments p GROUP BY date(p.paid_at);

CREATE VIEW v_low_stock AS
SELECT i.ingredient_id, i.name, i.stock_qty, i.reorder_level, s.name AS supplier, s.lead_days
  FROM ingredients i JOIN suppliers s ON s.supplier_id = i.supplier_id
 WHERE i.stock_qty <= i.reorder_level;

CREATE VIEW v_item_margin AS
SELECT m.item_id, m.name, c.name AS category, m.price, m.cost,
       ROUND((m.price - m.cost) * 100.0 / m.price, 1) AS margin_pct
  FROM menu_items m JOIN menu_categories c ON c.category_id = m.category_id;
