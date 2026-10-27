-- Secondary indexes (SQLite does not index foreign keys automatically).
CREATE INDEX idx_order_items_order  ON order_items(order_id);
CREATE INDEX idx_order_items_item   ON order_items(item_id);
CREATE INDEX idx_orders_opened_at   ON orders(opened_at);
CREATE INDEX idx_orders_customer    ON orders(customer_id);
CREATE INDEX idx_orders_table       ON orders(table_id);
CREATE INDEX idx_payments_paid_at   ON payments(paid_at);
CREATE INDEX idx_menu_items_cat     ON menu_items(category_id);
CREATE INDEX idx_resv_table_time    ON reservations(table_id, reserved_for);
