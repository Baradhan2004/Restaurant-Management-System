-- Business rules enforced inside the database, not the application.

-- 1. Deduct ingredient stock via the recipe (bill of materials) when an item is ordered.
CREATE TRIGGER trg_deduct_stock AFTER INSERT ON order_items
BEGIN
  UPDATE ingredients
     SET stock_qty = stock_qty - NEW.quantity *
         (SELECT r.qty_per_unit FROM recipe_items r
           WHERE r.item_id = NEW.item_id AND r.ingredient_id = ingredients.ingredient_id)
   WHERE ingredient_id IN (SELECT ingredient_id FROM recipe_items WHERE item_id = NEW.item_id);
END;

-- 2. Paying an order closes it.
CREATE TRIGGER trg_close_order AFTER INSERT ON payments
BEGIN
  UPDATE orders SET status = 'paid', closed_at = NEW.paid_at WHERE order_id = NEW.order_id;
END;

-- 3. Loyalty: 1 point per 10 currency units paid.
CREATE TRIGGER trg_loyalty AFTER INSERT ON payments
BEGIN
  UPDATE customers
     SET loyalty_points = loyalty_points + CAST(NEW.amount / 10 AS INTEGER)
   WHERE customer_id = (SELECT customer_id FROM orders WHERE order_id = NEW.order_id);
END;

-- 4. Party must fit the table.
CREATE TRIGGER trg_party_fits BEFORE INSERT ON reservations
WHEN NEW.party_size > (SELECT capacity FROM dining_tables WHERE table_id = NEW.table_id)
BEGIN
  SELECT RAISE(ABORT, 'party size exceeds table capacity');
END;

-- 5. No double booking: same table within 90 minutes of an existing confirmed reservation.
CREATE TRIGGER trg_no_double_booking BEFORE INSERT ON reservations
WHEN EXISTS (
  SELECT 1 FROM reservations r
   WHERE r.table_id = NEW.table_id AND r.status = 'confirmed'
     AND ABS(julianday(r.reserved_for) - julianday(NEW.reserved_for)) * 1440 < 90)
BEGIN
  SELECT RAISE(ABORT, 'table already reserved within 90 minutes');
END;

-- 6. Cannot sell an unavailable menu item.
CREATE TRIGGER trg_item_available BEFORE INSERT ON order_items
WHEN (SELECT is_available FROM menu_items WHERE item_id = NEW.item_id) = 0
BEGIN
  SELECT RAISE(ABORT, 'menu item is unavailable');
END;
