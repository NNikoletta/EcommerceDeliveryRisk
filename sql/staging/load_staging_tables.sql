TRUNCATE TABLE
    staging.order_items,
    staging.order_payments,
    staging.order_reviews,
    staging.orders,
    staging.products,
    staging.customers,
    staging.sellers,
    staging.geolocation,
    staging.product_category_name_translation;

----------------------------------------------
--CUSTOMERS TABLE
----------------------------------------------
INSERT INTO staging.customers (
    customer_id,
    customer_unique_id,
    customer_zip_code_prefix,
    customer_city,
    customer_state
)
SELECT
    NULLIF(TRIM(customer_id), ''),
    NULLIF(TRIM(customer_unique_id), ''),
    NULLIF(TRIM(customer_zip_code_prefix), ''),
    NULLIF(TRIM(customer_city), ''),
    NULLIF(TRIM(customer_state), '')
FROM raw.customers;

----------------------------------------------
--SELLERS TABLE
----------------------------------------------
INSERT INTO staging.sellers (
    seller_id,
    seller_zip_code_prefix,
    seller_city,
    seller_state
)
SELECT
    NULLIF(TRIM(seller_id), ''),
    NULLIF(TRIM(seller_zip_code_prefix), ''),
    NULLIF(TRIM(seller_city), ''),
    NULLIF(TRIM(seller_state), '')
FROM raw.sellers;


----------------------------------------------
--PRODUCTS TABLE
----------------------------------------------
INSERT INTO staging.products (
    product_id,
    product_category_name,
    product_name_length,
    product_description_length,
    product_photos_qty,
    product_weight_g,
    product_length_cm,
    product_height_cm,
    product_width_cm
)
SELECT
    NULLIF(TRIM(product_id), ''),
    NULLIF(TRIM(product_category_name), ''),
    NULLIF(TRIM(product_name_length), '')::INTEGER,
    NULLIF(TRIM(product_description_length), '')::INTEGER,
    NULLIF(TRIM(product_photos_qty), '')::INTEGER,
    NULLIF(TRIM(product_weight_g), '')::INTEGER,
    NULLIF(TRIM(product_length_cm), '')::INTEGER,
    NULLIF(TRIM(product_height_cm), '')::INTEGER,
    NULLIF(TRIM(product_width_cm), '')::INTEGER
FROM raw.products;

----------------------------------------------
--PRODUCT CATEGORY NAME TRANSLATION TABLE
----------------------------------------------
INSERT INTO staging.product_category_name_translation (
    product_category_name,
    product_category_name_english
)
SELECT
    NULLIF(TRIM(product_category_name), ''),
    NULLIF(TRIM(product_category_name_english), '')
FROM raw.product_category_name_translation;

----------------------------------------------
--GEOLOCATION TABLE
----------------------------------------------
INSERT INTO staging.geolocation (
    geolocation_zip_code_prefix,
    geolocation_lat,
    geolocation_lng,
    geolocation_city,
    geolocation_state
)
SELECT
    NULLIF(TRIM(geolocation_zip_code_prefix), ''),
    NULLIF(TRIM(geolocation_lat), '')::NUMERIC,
    NULLIF(TRIM(geolocation_lng), '')::NUMERIC,
    NULLIF(TRIM(geolocation_city), ''),
    NULLIF(TRIM(geolocation_state), '')
FROM raw.geolocation;

----------------------------------------------
--ORDERS TABLE
----------------------------------------------
INSERT INTO staging.orders (
    order_id,
    customer_id,
    order_status,
    order_purchase_timestamp,
    order_approved_at,
    order_delivered_carrier_date,
    order_delivered_customer_date,
    order_estimated_delivery_date
)
SELECT
    NULLIF(TRIM(order_id), ''),
    NULLIF(TRIM(customer_id), ''),
    NULLIF(TRIM(order_status), ''),
    NULLIF(TRIM(order_purchase_timestamp), '')::TIMESTAMP,
    NULLIF(TRIM(order_approved_at), '')::TIMESTAMP,
    NULLIF(TRIM(order_delivered_carrier_date), '')::TIMESTAMP,
    NULLIF(TRIM(order_delivered_customer_date), '')::TIMESTAMP,
    NULLIF(TRIM(order_estimated_delivery_date), '')::TIMESTAMP
FROM raw.orders;

----------------------------------------------
--ORDER ITEMS TABLE
----------------------------------------------
INSERT INTO staging.order_items (
    order_id,
    order_item_id,
    product_id,
    seller_id,
    shipping_limit_date,
    price,
    freight_value
)
SELECT
    NULLIF(TRIM(order_id), ''),
    NULLIF(TRIM(order_item_id), '')::INTEGER,
    NULLIF(TRIM(product_id), ''),
    NULLIF(TRIM(seller_id), ''),
    NULLIF(TRIM(shipping_limit_date), '')::TIMESTAMP,
    NULLIF(TRIM(price), '')::NUMERIC,
    NULLIF(TRIM(freight_value), '')::NUMERIC
FROM raw.order_items;

----------------------------------------------
--ORDER PAYMENTS TABLE
----------------------------------------------
INSERT INTO staging.order_payments (
    order_id,
    payment_sequential,
    payment_type,
    payment_installments,
    payment_value
)
SELECT
    NULLIF(TRIM(order_id), ''),
    NULLIF(TRIM(payment_sequential), '')::INTEGER,
    NULLIF(TRIM(payment_type), ''),
    NULLIF(TRIM(payment_installments), '')::INTEGER,
    NULLIF(TRIM(payment_value), '')::NUMERIC
FROM raw.order_payments;

----------------------------------------------
--ORDER REVIEWS TABLE
----------------------------------------------
INSERT INTO staging.order_reviews (
    review_id,
    order_id,
    review_score,
    review_comment_title,
    review_comment_message,
    review_creation_date,
    review_answer_timestamp
)
SELECT
    NULLIF(TRIM(review_id), ''),
    NULLIF(TRIM(order_id), ''),
    NULLIF(TRIM(review_score), '')::INTEGER,
    NULLIF(TRIM(review_comment_title), ''),
    NULLIF(TRIM(review_comment_message), ''),
    NULLIF(TRIM(review_creation_date), '')::TIMESTAMP,
    NULLIF(TRIM(review_answer_timestamp), '')::TIMESTAMP
FROM raw.order_reviews;
