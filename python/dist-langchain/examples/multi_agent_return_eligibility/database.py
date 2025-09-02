"""
Database schema, views, and initialization for the customer service system.
"""

import sqlite3
import os

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), "customer_service.db")

# Define the schema
DB_SCHEMA = """
-- Main customer table
CREATE TABLE IF NOT EXISTS customers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    status TEXT,
    since DATE,
    phone TEXT
);

-- Customer address information
CREATE TABLE IF NOT EXISTS customer_addresses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id TEXT NOT NULL,
    address_type TEXT NOT NULL,  -- 'shipping', 'billing', 'both'
    is_default BOOLEAN DEFAULT 0,
    street_address TEXT NOT NULL,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    postal_code TEXT NOT NULL,
    country TEXT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

-- Customer payment methods
CREATE TABLE IF NOT EXISTS customer_payment_methods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id TEXT NOT NULL,
    payment_type TEXT NOT NULL,  -- 'credit_card', 'paypal', 'store_credit'
    is_default BOOLEAN DEFAULT 0,
    last_four TEXT,  -- Last four digits for cards
    provider TEXT,    -- Card brand or payment provider
    exp_date TEXT,    -- Expiration date if applicable
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

-- Customer return history
CREATE TABLE IF NOT EXISTS customer_returns (
    id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    order_id TEXT NOT NULL,
    return_date DATE NOT NULL,
    reason TEXT,
    return_status TEXT NOT NULL, -- 'completed', 'pending', 'rejected'
    refund_amount REAL,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

-- Create the customer profile view
CREATE VIEW IF NOT EXISTS vw_customer_profile AS
SELECT 
    c.id, 
    c.name, 
    c.email, 
    c.status, 
    c.since,
    c.phone,

    -- Default shipping address
    (SELECT street_address || ', ' || city || ', ' || state || ' ' || postal_code || ', ' || country 
     FROM customer_addresses 
     WHERE customer_id = c.id AND is_default = 1 AND (address_type = 'shipping' OR address_type = 'both')
     LIMIT 1) AS default_shipping_address,

    -- Preferred payment methods
    (SELECT GROUP_CONCAT(payment_type, ', ') 
     FROM customer_payment_methods 
     WHERE customer_id = c.id) AS preferred_payment_methods,

    -- Return history stats
    (SELECT COUNT(*) FROM customer_returns WHERE customer_id = c.id) AS total_returns

FROM customers c;

-- Products
CREATE TABLE IF NOT EXISTS products (
    product_id   INTEGER PRIMARY KEY,
    name         TEXT NOT NULL,
    category     TEXT NOT NULL,
    price        REAL NOT NULL
);

-- Orders
CREATE TABLE IF NOT EXISTS orders (
    order_id    TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(id),
    order_date  DATE NOT NULL,
    order_total REAL NOT NULL
);

-- Order items
CREATE TABLE IF NOT EXISTS order_items (
    order_item_id INTEGER PRIMARY KEY,
    order_id      TEXT    NOT NULL REFERENCES orders(order_id),
    product_id    INTEGER NOT NULL REFERENCES products(product_id),
    quantity      INTEGER NOT NULL,
    unit_price    REAL    NOT NULL
);

-- Purchase history view
CREATE VIEW IF NOT EXISTS vw_customer_purchase_history AS
SELECT
  o.order_id,
  o.customer_id,
  o.order_date,
  o.order_total,
  oi.order_item_id,
  oi.product_id,
  p.name           AS product_name,
  p.category       AS product_category,
  oi.quantity,
  oi.unit_price,
  (oi.quantity * oi.unit_price) AS line_total
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
JOIN products p      ON p.product_id = oi.product_id;

-- Membership tiers
CREATE TABLE IF NOT EXISTS membership_tiers (
    tier_id INTEGER PRIMARY KEY,
    tier_name TEXT NOT NULL,
    discount_percentage INTEGER NOT NULL,
    expedited_shipping BOOLEAN DEFAULT 0,
    extended_returns INTEGER DEFAULT 0,
    exclusive_events BOOLEAN DEFAULT 0
);

-- Customer memberships
CREATE TABLE IF NOT EXISTS customer_memberships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id TEXT NOT NULL,
    tier_id INTEGER NOT NULL,
    enrollment_date DATE NOT NULL,
    renewal_date DATE NOT NULL,
    reward_points_balance INTEGER DEFAULT 0,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (tier_id) REFERENCES membership_tiers(tier_id)
);

-- Membership benefits view
CREATE VIEW IF NOT EXISTS vw_customer_membership_benefits AS
SELECT
    cm.customer_id,
    mt.tier_name AS membership_tier,
    cm.enrollment_date,
    cm.renewal_date,
    mt.discount_percentage,
    mt.expedited_shipping,
    mt.extended_returns,
    mt.exclusive_events,
    cm.reward_points_balance
FROM customer_memberships cm
JOIN membership_tiers mt ON cm.tier_id = mt.tier_id;

-- Product warranties
CREATE TABLE IF NOT EXISTS product_warranties (
    warranty_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id TEXT NOT NULL,
    order_id TEXT NOT NULL,
    product_id INTEGER NOT NULL,
    warranty_type TEXT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    coverage_details TEXT,
    is_active BOOLEAN DEFAULT 1,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- Product warranties view
CREATE VIEW IF NOT EXISTS vw_customer_product_warranties AS
SELECT
    w.warranty_id,
    w.customer_id,
    w.order_id,
    w.product_id,
    p.name AS product_name,
    w.warranty_type,
    w.start_date,
    w.end_date,
    w.coverage_details,
    w.is_active
FROM product_warranties w
JOIN products p ON w.product_id = p.product_id;
"""

SAMPLE_DATA = """
-- Insert sample customers
INSERT OR IGNORE INTO customers 
(id, name, email, status, since, phone)
VALUES
('C12345', 'Jane Doe', 'jane.doe@example.com', 'active', '2021-03-15', '555-123-4567'),
('C12346', 'John Smith', 'john.smith@example.com', 'active', '2020-09-10', '555-987-6543'),
('C12347', 'Alice Johnson', 'alice.j@example.com', 'inactive', '2022-01-20', '555-789-0123');

-- Insert sample addresses
INSERT OR IGNORE INTO customer_addresses
(customer_id, address_type, is_default, street_address, city, state, postal_code, country)
VALUES
('C12345', 'shipping', 1, '123 Main St, Apt 4B', 'Anytown', 'ST', '12345', 'US'),
('C12345', 'billing', 0, '123 Main St, Apt 4B', 'Anytown', 'ST', '12345', 'US'),
('C12346', 'both', 1, '456 Oak Ave', 'Somewhere', 'ST', '67890', 'US'),
('C12347', 'shipping', 1, '789 Pine Rd', 'Nowhere', 'ST', '54321', 'US');

-- Insert sample payment methods
INSERT OR IGNORE INTO customer_payment_methods
(customer_id, payment_type, is_default, last_four, provider, exp_date)
VALUES
('C12345', 'credit_card', 1, '4567', 'Visa', '05/26'),
('C12345', 'paypal', 0, NULL, 'PayPal', NULL),
('C12346', 'credit_card', 1, '8901', 'Mastercard', '09/25'),
('C12347', 'paypal', 1, NULL, 'PayPal', NULL);

-- Insert sample returns
INSERT OR IGNORE INTO customer_returns
(id, customer_id, order_id, return_date, reason, return_status, refund_amount)
VALUES
('R1001', 'C12345', 'ORD-8765', '2023-01-15', 'Wrong size', 'completed', 49.99),
('R1002', 'C12345', 'ORD-9432', '2022-11-10', 'Defective', 'completed', 129.99),
('R1003', 'C12347', 'ORD-7654', '2023-03-20', 'Changed mind', 'completed', 89.99);

-- Sample products
INSERT OR IGNORE INTO products (product_id, name, category, price) VALUES
  (1, 'Headphones',     'Electronics', 99.99),
  (2, 'Laptop Sleeve',  'Accessories', 19.99),
  (3, 'Smart TV',       'Electronics', 599.99),
  (4, 'Bluetooth Speaker', 'Electronics', 79.99),
  (5, 'Wireless Earbuds', 'Electronics', 129.99);  -- New product for Case 3

-- Sample membership tiers
INSERT OR IGNORE INTO membership_tiers (tier_id, tier_name, discount_percentage, expedited_shipping, extended_returns, exclusive_events) VALUES
  (1, 'Bronze', 5, 0, 30, 0),
  (2, 'Silver', 10, 1, 45, 0),
  (3, 'Gold', 15, 1, 60, 1);

-- Sample customer memberships
INSERT OR IGNORE INTO customer_memberships (customer_id, tier_id, enrollment_date, renewal_date, reward_points_balance) VALUES
  ('C12345', 3, '2022-01-15', '2023-01-15', 2500),  -- Jane Doe has Gold
  ('C12346', 2, '2022-03-10', '2023-03-10', 1200),  -- John Smith has Silver
  ('C12347', 1, '2022-06-20', '2023-06-20', 450);   -- Alice has Bronze

-- Sample orders with dates aligned with test case narratives
INSERT OR IGNORE INTO orders (order_id, customer_id, order_date, order_total) VALUES
  ('ORD-1001', 'C12345', '2023-06-13', 99.99),   -- Case 1: Headphones "bought last week"
  ('ORD-1002', 'C12345', '2023-06-05', 19.99),   -- Case 6: Laptop Sleeve (for multiple items test)
  ('ORD-1003', 'C12345', '2023-06-10', 599.99),  -- Case 4: Smart TV "purchased last month"
  ('ORD-1004', 'C12346', '2023-06-01', 79.99),   -- Case 7: Bluetooth Speaker (Silver Member)
  ('ORD-1005', 'C12345', '2023-04-15', 129.99),  -- Case 3: Wireless Earbuds (for warranty test)
  ('ORD-1006', 'C12345', '2023-05-11', 99.99),   -- Case 2: Headphones "40 days ago" (Gold member)
  ('ORD-1007', 'C12345', '2022-12-20', 19.99);   -- Case 5: Laptop Sleeve "6 months ago"

-- Sample order items
INSERT OR IGNORE INTO order_items (order_item_id, order_id, product_id, quantity, unit_price) VALUES
  (1001, 'ORD-1001', 1, 1, 99.99),    -- Headphones for Case 1
  (1002, 'ORD-1002', 2, 1, 19.99),    -- Laptop Sleeve for Case 6
  (1003, 'ORD-1003', 3, 1, 599.99),   -- Smart TV for Case 4
  (1004, 'ORD-1004', 4, 1, 79.99),    -- Bluetooth Speaker for Case 7
  (1005, 'ORD-1005', 5, 1, 129.99),   -- Wireless Earbuds for Case 3
  (1006, 'ORD-1006', 1, 1, 99.99),    -- Headphones for Case 2
  (1007, 'ORD-1007', 2, 1, 19.99);    -- Laptop Sleeve for Case 5

-- Sample product warranties
INSERT OR IGNORE INTO product_warranties (customer_id, order_id, product_id, warranty_type, start_date, end_date, coverage_details, is_active) VALUES
  ('C12345', 'ORD-1001', 1, 'Standard', '2023-06-13', '2024-06-13', 'Covers manufacturing defects', 1),
  ('C12345', 'ORD-1003', 3, 'Extended', '2023-06-10', '2026-06-10', 'Full coverage including panel replacement', 1),
  ('C12346', 'ORD-1004', 4, 'Standard', '2023-06-01', '2024-06-01', 'Covers manufacturing defects only', 1),
  ('C12345', 'ORD-1005', 5, 'Extended', '2023-04-15', '2025-04-15', 'Covers manufacturing defects and sound issues', 1),
  ('C12345', 'ORD-1006', 1, 'Extended', '2023-05-11', '2025-05-11', 'Covers manufacturing defects and accidental damage', 1);
"""


def init_database(force_init=False) -> None:
    """Initialize the database with schema and sample data."""

    # Check if database already exists
    db_exists = os.path.exists(DB_PATH)

    # If database exists and we're not forcing reinitialization, just return
    if db_exists and not force_init:
        return

    # Ensure database directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create schema
    cursor.executescript(DB_SCHEMA)

    # Insert sample data
    cursor.executescript(SAMPLE_DATA)

    # Print debug information to verify database is created
    print(f"Database initialized at: {DB_PATH}")

    # Verify views were created
    cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
    views = cursor.fetchall()
    print(f"Created views: {views}")

    conn.commit()
    conn.close()
