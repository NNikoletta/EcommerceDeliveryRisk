----------------------------------------------
--CUSTOMERS TABLE
----------------------------------------------
CREATE TABLE IF NOT EXISTS staging.customers (
    customer_id TEXT NOT NULL,
    customer_unique_id TEXT,
    customer_zip_code_prefix TEXT,
    customer_city TEXT,
    customer_state TEXT,

    CONSTRAINT pk_customers PRIMARY KEY (customer_id)
);

----------------------------------------------
--SELLERS TABLE
----------------------------------------------
CREATE TABLE IF NOT EXISTS staging.sellers (
    seller_id TEXT NOT NULL,
    seller_zip_code_prefix TEXT,
    seller_city TEXT,
    seller_state TEXT,

    CONSTRAINT pk_sellers PRIMARY KEY (seller_id)
);

----------------------------------------------
--PRODUCTS TABLE
----------------------------------------------
CREATE TABLE IF NOT EXISTS staging.products (
    product_id TEXT NOT NULL,
    product_category_name TEXT,
    product_name_length INTEGER,
    product_description_length INTEGER,
    product_photos_qty INTEGER,
    product_weight_g INTEGER,
    product_length_cm INTEGER,
    product_height_cm INTEGER,
    product_width_cm INTEGER,

    CONSTRAINT pk_products PRIMARY KEY (product_id)
);

----------------------------------------------
--PRODUCT CATEGORY NAME TRANSLATION TABLE
----------------------------------------------
CREATE TABLE IF NOT EXISTS staging.translations (
    product_category_name TEXT NOT NULL,
    product_category_name_english TEXT,

    CONSTRAINT pk_translations PRIMARY KEY (product_category_name)
);

----------------------------------------------
--GEOLOCATION TABLE
----------------------------------------------
CREATE TABLE IF NOT EXISTS staging.geolocation (
    geolocation_zip_code_prefix TEXT,
    geolocation_lat NUMERIC,
    geolocation_lng NUMERIC,
    geolocation_city TEXT,
    geolocation_state TEXT
);

----------------------------------------------
--ORDERS TABLE
----------------------------------------------
CREATE TABLE IF NOT EXISTS staging.orders (
    order_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    order_status TEXT,
    order_purchase_timestamp TIMESTAMP,
    order_approved_at TIMESTAMP,
    order_delivered_carrier_date TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP,

    CONSTRAINT pk_orders PRIMARY KEY (order_id),

    CONSTRAINT fk_orders_customers FOREIGN KEY (customer_id) REFERENCES staging.customers (customer_id)
);

----------------------------------------------
--ORDER ITEMS TABLE
----------------------------------------------
CREATE TABLE IF NOT EXISTS staging.order_items (
    order_id TEXT NOT NULL,
    order_item_id INTEGER NOT NULL,
    product_id TEXT NOT NULL,
    seller_id TEXT NOT NULL,
    shipping_limit_date TIMESTAMP,
    price NUMERIC(12,2),
    freight_value NUMERIC(12,2),

    CONSTRAINT pk_order_items PRIMARY KEY (order_id, order_item_id),

    CONSTRAINT fk_order_items_orders FOREIGN KEY (order_id) REFERENCES staging.orders (order_id),
    CONSTRAINT fk_order_items_products FOREIGN KEY (product_id) REFERENCES staging.products (product_id),
    CONSTRAINT fk_order_items_sellers FOREIGN KEY (seller_id) REFERENCES staging.sellers (seller_id)
);

----------------------------------------------
--ORDER PAYMENTS TABLE
----------------------------------------------
CREATE TABLE IF NOT EXISTS staging.order_payments (
    order_id TEXT NOT NULL,
    payment_sequential INTEGER NOT NULL,
    payment_type TEXT,
    payment_installments INTEGER,
    payment_value NUMERIC(12,2),

    CONSTRAINT pk_order_payments PRIMARY KEY (order_id, payment_sequential),

    CONSTRAINT fk_order_payments_orders FOREIGN KEY (order_id) REFERENCES staging.orders (order_id)
);

----------------------------------------------
--ORDER REVIEWS TABLE
----------------------------------------------
CREATE TABLE IF NOT EXISTS staging.order_reviews (
    review_id TEXT,
    order_id TEXT,
    review_score INTEGER,
    review_comment_title TEXT,
    review_comment_message TEXT,
    review_creation_date TIMESTAMP,
    review_answer_timestamp TIMESTAMP,

    CONSTRAINT fk_order_reviews_orders FOREIGN KEY (order_id) REFERENCES staging.orders (order_id)
);
