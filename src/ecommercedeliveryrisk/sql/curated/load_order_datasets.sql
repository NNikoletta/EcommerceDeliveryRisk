TRUNCATE TABLE
    curated.order_targets,
    curated.order_features;

WITH zip_geolocation AS (
    SELECT
        geolocation_zip_code_prefix,

        PERCENTILE_CONT(0.5) WITHIN GROUP (
            ORDER BY geolocation_lat::DOUBLE PRECISION
        ) AS latitude,

        PERCENTILE_CONT(0.5) WITHIN GROUP (
            ORDER BY geolocation_lng::DOUBLE PRECISION
        ) AS longitude

    FROM staging.geolocation
    GROUP BY geolocation_zip_code_prefix
),
item_details AS (
    SELECT
        order_items.order_id,
        order_items.order_item_id,
        order_items.product_id,
        products.product_category_name,
        order_items.seller_id,
        sellers.seller_state,
        customers.customer_state,
        order_items.price,
        order_items.freight_value,
        products.product_weight_g,

        CASE
            WHEN customer_location.latitude IS NULL
                OR customer_location.longitude IS NULL
                OR seller_location.latitude IS NULL
                OR seller_location.longitude IS NULL
            THEN NULL

            ELSE
                2.0 * 6371.0088 * ASIN(
                    SQRT(
                        GREATEST(
                            0.0,
                            LEAST(
                                1.0,
                                POWER(
                                    SIN(
                                        RADIANS(
                                            (
                                                seller_location.latitude -
                                                customer_location.latitude
                                            ) / 2.0
                                        )
                                    ),
                                    2
                                )
                                + COS(
                                    RADIANS(customer_location.latitude)
                                )
                                * COS(
                                    RADIANS(seller_location.latitude)
                                )
                                *
                                POWER(
                                    SIN(
                                        RADIANS(
                                            (
                                                seller_location.longitude -
                                                customer_location.longitude
                                            ) / 2.0
                                        )
                                    ),
                                    2
                                )
                            )
                        )
                    )
                )
        END AS seller_distance_km
    FROM staging.order_items AS order_items

    JOIN staging.orders AS orders
        ON orders.order_id = order_items.order_id

    JOIN staging.customers AS customers
        ON customers.customer_id = orders.customer_id

    JOIN staging.sellers AS sellers
        ON sellers.seller_id = order_items.seller_id

    JOIN staging.products AS products
        ON products.product_id = order_items.product_id

    LEFT JOIN zip_geolocation AS customer_location
        ON customer_location.geolocation_zip_code_prefix
            = customers.customer_zip_code_prefix

    LEFT JOIN zip_geolocation AS seller_location
        ON seller_location.geolocation_zip_code_prefix
            = sellers.seller_zip_code_prefix
),
item_features AS (
    SELECT
        order_id,
        COUNT(*)::INTEGER AS item_count,
        COUNT(DISTINCT product_id)::INTEGER AS distinct_product_count,
        COUNT(DISTINCT product_category_name)::INTEGER AS distinct_category_count,
        COUNT(DISTINCT seller_id)::INTEGER AS seller_count,
        COUNT(DISTINCT seller_state)::INTEGER AS distinct_seller_state_count,
        BOOL_OR(seller_state <> customer_state) AS has_cross_state_seller,
        SUM(price)::NUMERIC(12, 2) AS total_item_value,
        SUM(freight_value)::NUMERIC(12, 2) AS total_freight_value,
        AVG(price)::NUMERIC(12, 2) AS average_item_price,
        SUM(product_weight_g)::NUMERIC(12, 2) AS total_product_weight_g,
        ROUND(AVG(seller_distance_km)::NUMERIC, 2) AS average_seller_distance_km,
        ROUND(MAX(seller_distance_km)::NUMERIC, 2) AS maximum_seller_distance_km
    FROM item_details
    GROUP BY order_id
),
payment_features AS (
    SELECT
        order_id,
        COUNT(*)::INTEGER AS payment_count,
        COUNT(DISTINCT payment_type)::INTEGER AS payment_type_count,
        SUM(payment_value)::NUMERIC(12, 2) AS total_payment_value,
        MAX(payment_installments)::INTEGER AS maximum_payment_installments,
        BOOL_OR(payment_type = 'credit_card') AS has_credit_card_payment,
        BOOL_OR(payment_type = 'boleto') AS has_boleto_payment,
        BOOL_OR(payment_type = 'voucher') AS has_voucher_payment,
        BOOL_OR(payment_type = 'debit_card') AS has_debit_card_payment
    FROM staging.order_payments
    GROUP BY order_id
)
INSERT INTO curated.order_features(
    order_id,
    customer_unique_id,
    order_purchase_timestamp,
    order_approved_at,
    customer_state,
    customer_zip_code_prefix,
    customer_latitude,
    customer_longitude,
    purchase_hour,
    purchase_day_of_week,
    purchase_month,
    approval_delay_hours,
    promised_delivery_days,
    item_count,
    distinct_product_count,
    distinct_category_count,
    seller_count,
    distinct_seller_state_count,
    has_cross_state_seller,
    average_seller_distance_km,
    maximum_seller_distance_km,
    total_item_value,
    total_freight_value,
    average_item_price,
    total_product_weight_g,
    payment_count,
    payment_type_count,
    total_payment_value,
    maximum_payment_installments,
    has_credit_card_payment,
    has_boleto_payment,
    has_voucher_payment,
    has_debit_card_payment
)
SELECT
    orders.order_id,
    customers.customer_unique_id,
    orders.order_purchase_timestamp,
    orders.order_approved_at,
    customers.customer_state,
    customers.customer_zip_code_prefix,
    customer_location.latitude,
    customer_location.longitude,

    EXTRACT(
        HOUR FROM orders.order_purchase_timestamp
    )::SMALLINT AS purchase_hour,
    EXTRACT(
        DOW FROM orders.order_purchase_timestamp
    )::SMALLINT AS purchase_day_of_week,
    EXTRACT(
        MONTH FROM orders.order_purchase_timestamp
    )::SMALLINT AS purchase_month,

    ROUND(
        (
            EXTRACT(
                EPOCH FROM (
                    orders.order_approved_at - orders.order_purchase_timestamp
                )
            ) / 3600
        )::NUMERIC,
        2
    ) AS approval_delay_hours,

    ROUND(
        (
            EXTRACT(
                EPOCH FROM (
                    orders.order_estimated_delivery_date - orders.order_approved_at
                )
            ) / 86400
        )::NUMERIC,
        2
    ) AS promised_delivery_days,

    item_features.item_count,
    item_features.distinct_product_count,
    item_features.distinct_category_count,
    item_features.seller_count,
    item_features.distinct_seller_state_count,
    item_features.has_cross_state_seller,
    item_features.average_seller_distance_km,
    item_features.maximum_seller_distance_km,

    item_features.total_item_value,
    item_features.total_freight_value,
    item_features.average_item_price,
    item_features.total_product_weight_g,

    payment_features.payment_count,
    payment_features.payment_type_count,
    payment_features.total_payment_value,
    payment_features.maximum_payment_installments,
    payment_features.has_credit_card_payment,
    payment_features.has_boleto_payment,
    payment_features.has_voucher_payment,
    payment_features.has_debit_card_payment

FROM staging.orders AS orders

JOIN staging.customers AS customers
    ON customers.customer_id = orders.customer_id

LEFT JOIN zip_geolocation AS customer_location
    ON customer_location.geolocation_zip_code_prefix
        = customers.customer_zip_code_prefix

LEFT JOIN item_features
    ON item_features.order_id = orders.order_id

LEFT JOIN payment_features
    ON payment_features.order_id = orders.order_id

WHERE orders.order_approved_at IS NOT NULL;

INSERT INTO curated.order_targets (
    order_id,
    non_delivery_label,
    late_delivery_label
)
SELECT
    order_features.order_id,

    CASE
        WHEN orders.order_status IN (
            'canceled',
            'unavailable'
        )
        THEN 1

        WHEN orders.order_status = 'delivered'
            AND orders.order_delivered_customer_date IS NOT NULL
        THEN 0
        ELSE NULL
    END::SMALLINT AS non_delivery_label,

    CASE
        WHEN orders.order_status = 'delivered'
            AND orders.order_delivered_customer_date IS NOT NULL
        THEN
            CASE
                WHEN orders.order_delivered_customer_date
                    > orders.order_estimated_delivery_date
                THEN 1
                ELSE 0
            END

        ELSE NULL
    END::SMALLINT AS late_delivery_label
FROM curated.order_features AS order_features

JOIN staging.orders AS orders
    ON orders.order_id = order_features.order_id;