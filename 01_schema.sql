-- Restaurant Management System: normalized (3NF) SQLite schema
PRAGMA foreign_keys = ON;

CREATE TABLE staff (
  staff_id    INTEGER PRIMARY KEY,
  full_name   TEXT NOT NULL,
  role        TEXT NOT NULL CHECK (role IN ('manager','chef','waiter','cashier','host')),
  hourly_wage REAL NOT NULL CHECK (hourly_wage > 0),
  hired_on    TEXT NOT NULL
);

CREATE TABLE customers (
  customer_id    INTEGER PRIMARY KEY,
  full_name      TEXT NOT NULL,
  phone          TEXT NOT NULL UNIQUE,
  email          TEXT UNIQUE,
  loyalty_points INTEGER NOT NULL DEFAULT 0 CHECK (loyalty_points >= 0),
  created_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE dining_tables (
  table_id INTEGER PRIMARY KEY,
  label    TEXT NOT NULL UNIQUE,
  capacity INTEGER NOT NULL CHECK (capacity BETWEEN 1 AND 20),
  status   TEXT NOT NULL DEFAULT 'free' CHECK (status IN ('free','occupied','reserved'))
);

CREATE TABLE menu_categories (
  category_id INTEGER PRIMARY KEY,
  name        TEXT NOT NULL UNIQUE
);

CREATE TABLE menu_items (
  item_id      INTEGER PRIMARY KEY,
  category_id  INTEGER NOT NULL REFERENCES menu_categories(category_id),
  name         TEXT NOT NULL UNIQUE,
  price        REAL NOT NULL CHECK (price > 0),
  cost         REAL NOT NULL CHECK (cost >= 0),
  is_available INTEGER NOT NULL DEFAULT 1 CHECK (is_available IN (0,1))
);

CREATE TABLE suppliers (
  supplier_id INTEGER PRIMARY KEY,
  name        TEXT NOT NULL UNIQUE,
  phone       TEXT,
  lead_days   INTEGER NOT NULL DEFAULT 2 CHECK (lead_days >= 0)
);

CREATE TABLE ingredients (
  ingredient_id INTEGER PRIMARY KEY,
  name          TEXT NOT NULL UNIQUE,
  unit          TEXT NOT NULL,
  stock_qty     REAL NOT NULL,
  reorder_level REAL NOT NULL CHECK (reorder_level >= 0),
  supplier_id   INTEGER NOT NULL REFERENCES suppliers(supplier_id)
);

CREATE TABLE recipe_items (          -- bill of materials: menu item -> ingredients
  item_id       INTEGER NOT NULL REFERENCES menu_items(item_id) ON DELETE CASCADE,
  ingredient_id INTEGER NOT NULL REFERENCES ingredients(ingredient_id),
  qty_per_unit  REAL NOT NULL CHECK (qty_per_unit > 0),
  PRIMARY KEY (item_id, ingredient_id)
);

CREATE TABLE reservations (
  reservation_id INTEGER PRIMARY KEY,
  customer_id    INTEGER NOT NULL REFERENCES customers(customer_id),
  table_id       INTEGER NOT NULL REFERENCES dining_tables(table_id),
  party_size     INTEGER NOT NULL CHECK (party_size > 0),
  reserved_for   TEXT NOT NULL,
  status         TEXT NOT NULL DEFAULT 'confirmed' CHECK (status IN ('confirmed','seated','cancelled','no_show'))
);

CREATE TABLE orders (
  order_id    INTEGER PRIMARY KEY,
  table_id    INTEGER NOT NULL REFERENCES dining_tables(table_id),
  customer_id INTEGER REFERENCES customers(customer_id),
  staff_id    INTEGER NOT NULL REFERENCES staff(staff_id),
  status      TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open','paid','cancelled')),
  opened_at   TEXT NOT NULL,
  closed_at   TEXT
);

CREATE TABLE order_items (
  order_item_id INTEGER PRIMARY KEY,
  order_id      INTEGER NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
  item_id       INTEGER NOT NULL REFERENCES menu_items(item_id),
  quantity      INTEGER NOT NULL CHECK (quantity > 0),
  unit_price    REAL NOT NULL CHECK (unit_price > 0)
);

CREATE TABLE payments (
  payment_id INTEGER PRIMARY KEY,
  order_id   INTEGER NOT NULL UNIQUE REFERENCES orders(order_id),
  method     TEXT NOT NULL CHECK (method IN ('cash','card','upi')),
  amount     REAL NOT NULL CHECK (amount > 0),
  tip        REAL NOT NULL DEFAULT 0 CHECK (tip >= 0),
  paid_at    TEXT NOT NULL
);
