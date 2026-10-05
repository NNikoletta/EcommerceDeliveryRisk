TRUNCATE TABLE
    curated.order_targets,
    curated.order_features;

WITH item_features AS (
    SELECT
        items.order_id,
        COUNT(*)::INTEGER AS item_count,
        COUNT(DISTINCT items.product_id)::INTEGER
            AS distinct_product_count,
        COUNT(DISTINCT products.product_category_name)::INTEGER
            AS distinct_category_count,
        COUNT(DISTINCT items.seller_id)::INTEGER
            AS seller_count,
        SUM(items.price)::NUMERIC(12, 2)
            AS total_item_value,
        SUM(items.freight_value)::NUMERIC(12, 2)
            AS total_freight_value,
        AVG(items.price)::NUMERIC(12, 2)
            AS average_item_price,
        SUM(products.product_weight_g)::NUMERIC(12, 2)
            AS total_product_weight_g
    FROM staging.order_items AS items
    LEFT JOIN staging.products AS products
        ON products.product_id = items.product_id
    GROUP BY items.order_id
),
payment_features AS (
    SELECT
        order_id,
        COUNT(*)::INTEGER AS payment_count,
        COUNT(DISTINCT payment_type)::INTEGER
            AS payment_type_count,
        SUM(payment_value)::NUMERIC(12, 2)
            AS total_payment_value,
        MAX(payment_installments)::INTEGER
            AS maximum_payment_installments,
        BOOL_OR(payment_type = 'credit_card')
            AS has_credit_card_payment,
        BOOL_OR(payment_type = 'boleto')
            AS has_boleto_payment,
        BOOL_OR(payment_type = 'voucher')
            AS has_voucher_payment,
        BOOL_OR(payment_type = 'debit_card')
            AS has_debit_card_payment
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
    purchase_hour,
    purchase_day_of_week,
    purchase_month,
    approval_delay_hours,
    promised_delivery_days,
    item_count,
    distinct_product_count,
    distinct_category_count,
    seller_count,
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
    EXTRACT(
        HOUR FROM orders.order_purchase_timestamp
    )::SMALLINT,
    EXTRACT(
        DOW FROM orders.order_purchase_timestamp
    )::SMALLINT,
    EXTRACT(
        MONTH FROM orders.order_purchase_timestamp
    )::SMALLINT,
    ROUND(
        (
            EXTRACT(
                EPOCH FROM (
                    orders.order_approved_at - orders.order_purchase_timestamp
                )
            ) / 3600
        )::NUMERIC,
        2
    ),

    ROUND(
        (
            EXTRACT(
                EPOCH FROM (
                    orders.order_estimated_delivery_date - orders.order_approved_at
                )
            ) / 86400
        )::NUMERIC,
        2
    ),

    item_features.item_count,
    item_features.distinct_product_count,
    item_features.distinct_category_count,
    item_features.seller_count,
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
    features.order_id,

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
    END AS non_delivery_label,

    CASE
        WHEN orders.order_status = 'delivered'
            AND orders.order_delivered_customer_date IS NOT NULL
            THEN (
                orders.order_delivered_customer_date > orders.order_estimated_delivery_date
            )::INTEGER

        ELSE NULL
    END AS late_delivery_label
FROM curated.order_features AS features

JOIN staging.orders AS orders
    ON orders.order_id = features.order_id;