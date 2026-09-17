----------------------------------------------
--CUSTOMERS TABLE
----------------------------------------------
CREATE TABLE staging.customers AS
SELECT
    customer_id,
    customer_unique_id,
    customer_zip_code_prefix,
    customer_city,
    customer_state
FROM raw.customers;

ALTER TABLE staging.customers ADD CONSTRAINT pk_customers PRIMARY KEY (customer_id);

----------------------------------------------
--SELLERS TABLE
----------------------------------------------
CREATE TABLE staging.sellers AS
SELECT
    seller_id,
    seller_zip_code_prefix,
    seller_city,
    seller_state
FROM raw.sellers;

ALTER TABLE staging.sellers ADD CONSTRAINT pk_sellers PRIMARY KEY (seller_id);

----------------------------------------------
--PRODUCTS TABLE
----------------------------------------------
CREATE TABLE staging.products AS
SELECT
    product_id,
    product_category_name,
    NULLIF(product_name_length, '')::INTEGER
    NULLIF(product_description_length, '')::INTEGER,
    NULLIF(product_photos_qty, '')::INTEGER,
    NULLIF(product_weight_g, '')::INTEGER,
    NULLIF(product_length_cm, '')::INTEGER,
    NULLIF(product_height_cm, '')::INTEGER,
    NULLIF(product_width_cm, '')::INTEGER
FROM raw.products;

ALTER TABLE staging.products ADD CONSTRAINT pk_products PRIMARY KEY (product_id);

----------------------------------------------
--PRODUCT CATEGORY NAME TRANSLATION TABLE
----------------------------------------------
CREATE TABLE staging.product_category_name_translation AS
    product_category_name,
    product_category_name_english
FROM raw.product_category_name_translation;

----------------------------------------------
--GEOLOCATION TABLE
----------------------------------------------
CREATE TABLE staging.geolocation AS
SELECT
    geolocation_zip_code_prefix,
    NULLIF(geolocation_lat, '')::NUMERIC,
    NULLIF(geolocation_lng, '')::NUMERIC,
    geolocation_city,
    geolocation_state
FROM raw.geolocation;

----------------------------------------------
--ORDERS TABLE
----------------------------------------------
CREATE TABLE staging.orders AS
SELECT
    order_id,
    customer_id,
    order_status,
    NULLIF(order_purchase_timestamp, '')::TIMESTAMP
        AS order_purchase_timestamp,
    NULLIF(order_approved_at, '')::TIMESTAMP
        AS order_approved_at,
    NULLIF(order_delivered_carrier_date, '')::TIMESTAMP
        AS order_delivered_carrier_date,
    NULLIF(order_delivered_customer_date, '')::TIMESTAMP
        AS order_delivered_customer_date,
    NULLIF(order_estimated_delivery_date, '')::TIMESTAMP
        AS order_estimated_delivery_date
FROM raw.orders;

ALTER TABLE staging.orders ADD CONSTRAINT pk_orders PRIMARY KEY (order_id);

ALTER TABLE staging.orders
    ADD CONSTRAINT orders_customers_fk
     FOREIGN KEY ( customer_id )
        REFERENCES staging.customers ( customer_id );

----------------------------------------------
--ORDER ITEMS TABLE
----------------------------------------------
CREATE TABLE staging.order_items AS
SELECT
    order_id,
    NULLIF(order_item_id, '')::INTEGER,
    product_id,
    seller_id,
    NULLIF(shipping_limit_date, '')::TIMESTAMP,
    NULLIF(price, '')::NUMERIC,
    NULLIF(freight_value, '')::NUMERIC
FROM raw.order_items;

ALTER TABLE staging.order_items ADD CONSTRAINT pk_order_items PRIMARY KEY (order_id, order_item_id);

ALTER TABLE staging.order_items
    ADD CONSTRAINT orders_items_orders_fk
     FOREIGN KEY ( order_id )
        REFERENCES staging.orders ( order_id );

ALTER TABLE staging.order_items
    ADD CONSTRAINT orders_items_products_fk
     FOREIGN KEY ( product_id )
        REFERENCES staging.products ( product_id );

ALTER TABLE staging.order_items
    ADD CONSTRAINT orders_items_sellers_fk
     FOREIGN KEY ( seller_id )
        REFERENCES staging.sellers ( seller_id );

----------------------------------------------
--ORDER PAYMENTS TABLE
----------------------------------------------
CREATE TABLE staging.order_payments AS
SELECT
    order_id,
    NULLIF(payment_sequential, '')::INTEGER,
    payment_type,
    NULLIF(payment_installments, '')::INTEGER,
    NULLIF(payment_value, '')::NUMERIC
FROM raw.order_payments;

----------------------------------------------
--ORDER REVIEWS TABLE
----------------------------------------------
CREATE TABLE staging.order_reviews AS
SELECT
    review_id,
    order_id,
    NULLIF(review_score, '')::INTEGER
    review_comment_title,
    review_comment_message,
    NULLIF(review_creation_date, '')::TIMESTAMP
    NULLIF(review_answer_timestamp, '')::TIMESTAMP
FROM raw.order_reviews;
