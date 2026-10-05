SELECT
	order_status,
	COUNT(*) AS order_count_by_status,
	COUNT(*) filter (
	WHERE order_approved_at IS NOT NULL) AS approved_order_count,
	COUNT(*) filter (
	WHERE order_delivered_customer_date IS NOT NULL) AS delivered_order_count
FROM
	staging.orders
GROUP BY
	order_status
ORDER BY
	order_count_by_status DESC;

WITH classified_orders AS (
    SELECT
        order_id,
        CASE
            WHEN order_approved_at IS NULL
                THEN 'ineligible_not_approved'

            WHEN order_status = 'delivered'
                AND order_delivered_customer_date IS NOT NULL
                THEN 'delivered_observed'

            WHEN order_status IN ('canceled', 'unavailable')
                THEN 'confirmed_non_delivery'

            ELSE 'censored_unresolved'
        END AS outcome_group
    FROM staging.orders
)
SELECT
    outcome_group,
    COUNT(*) AS order_count
FROM classified_orders
GROUP BY outcome_group
ORDER BY outcome_group;

SELECT
    CASE
        WHEN order_delivered_customer_date > order_estimated_delivery_date
            THEN 1
        ELSE 0
    END AS late_delivery_label,
    COUNT(*) AS order_count
FROM staging.orders
WHERE order_approved_at IS NOT NULL
AND order_status = 'delivered'
AND order_delivered_customer_date IS NOT NULL
AND order_estimated_delivery_date IS NOT NULL
GROUP BY late_delivery_label
ORDER BY late_delivery_label;


SELECT
    'approval_before_purchase' AS check_name,
    COUNT(*) AS invalid_row_count
FROM staging.orders
WHERE order_approved_at < order_purchase_timestamp

UNION ALL

SELECT
    'carrier_before_approval',
    COUNT(*)
FROM staging.orders
WHERE order_delivered_carrier_date < order_approved_at

UNION ALL

SELECT
    'customer_delivery_before_carrier',
    COUNT(*)
FROM staging.orders
WHERE order_delivered_customer_date < order_delivered_carrier_date

UNION ALL

SELECT
    'estimated_delivery_before_purchase',
    COUNT(*)
FROM staging.orders
WHERE order_estimated_delivery_date < order_purchase_timestamp

UNION ALL

SELECT
    'delivered_status_without_delivery_date',
    COUNT(*)
FROM staging.orders
WHERE order_status = 'delivered'
AND order_delivered_customer_date IS NULL;

WITH item_counts AS (
    SELECT order_id, COUNT(*) AS records_per_order
    FROM staging.order_items
    GROUP BY order_id
),
payment_counts AS (
    SELECT order_id, COUNT(*) AS records_per_order
    FROM staging.order_payments
    GROUP BY order_id
),
review_counts AS (
    SELECT order_id, COUNT(*) AS records_per_order
    FROM staging.order_reviews
    GROUP BY order_id
)
SELECT
    'order_items' AS source_table,
    COUNT(*) AS represented_orders,
    COUNT(*) FILTER(
        WHERE records_per_order > 1
    ) AS orders_with_multiple_records,
    MAX(records_per_order) AS maximum_records_per_order
FROM item_counts

UNION ALL

SELECT
    'order_payments',
    COUNT(*),
    COUNT(*) FILTER(
        WHERE records_per_order > 1
    ),
    MAX(records_per_order)
FROM payment_counts

UNION ALL

SELECT
    'order_reviews',
    COUNT(*),
    COUNT(*) FILTER (
        WHERE records_per_order > 1
    ),
    MAX(records_per_order)
FROM review_counts;

SELECT
    'negative_item_price' AS check_name,
    COUNT(*) AS invalid_row_count
FROM staging.order_items
WHERE price < 0

UNION ALL

SELECT
    'negative_freight_value',
    COUNT(*)
FROM staging.order_items
WHERE freight_value < 0

UNION ALL

SELECT
    'negative_payment_value',
    COUNT(*)
FROM staging.order_payments
WHERE payment_value < 0

UNION ALL

SELECT
    'negative_payment_installments',
    COUNT(*)
FROM staging.order_payments
WHERE payment_installments < 0

UNION ALL

SELECT
    'invalid_review_score',
    COUNT(*)
FROM staging.order_reviews
WHERE review_score NOT BETWEEN 1 AND 5;


WITH zip_counts AS (
    SELECT
        geolocation_zip_code_prefix,
        COUNT(*) AS location_count,
        COUNT(DISTINCT geolocation_city) AS city_count,
        COUNT(DISTINCT geolocation_state) AS state_count
    FROM staging.geolocation
    GROUP BY geolocation_zip_code_prefix
)
SELECT
    COUNT(*) AS unique_zip_code_prefixes,
    COUNT(*) FILTER (
        WHERE location_count > 1
    ) AS zip_code_prefixes_with_multiple_coordinates,
    COUNT(*) FILTER (
        WHERE city_count > 1
    ) AS zip_code_prefixes_with_multiple_cities,
    COUNT(*) FILTER (
        WHERE state_count > 1
    ) AS zip_code_prefixes_with_multiple_states,
    MAX(location_count) AS maximum_locations_per_zip
FROM zip_counts;