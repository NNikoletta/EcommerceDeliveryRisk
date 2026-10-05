CREATE TABLE IF NOT EXISTS curated.order_features (
    order_id TEXT NOT NULL,
    customer_unique_id TEXT NOT NULL,

    order_purchase_timestamp TIMESTAMP NOT NULL,
    order_approved_at TIMESTAMP NOT NULL,

    customer_state TEXT NOT NULL,
    customer_zip_code_prefix TEXT NOT NULL,

    purchase_hour SMALLINT NOT NULL,
    purchase_day_of_week SMALLINT NOT NULL,
    purchase_month SMALLINT NOT NULL,

    approval_delay_hours NUMERIC(12, 2) NOT NULL,
    promised_delivery_days NUMERIC(12, 2) NOT NULL,

    item_count INTEGER,
    distinct_product_count INTEGER,
    distinct_category_count INTEGER,
    seller_count INTEGER,

    total_item_value NUMERIC(12, 2),
    total_freight_value NUMERIC(12, 2),
    average_item_price NUMERIC(12, 2),
    total_product_weight_g NUMERIC(12, 2),

    payment_count INTEGER,
    payment_type_count INTEGER,
    total_payment_value NUMERIC(12, 2),
    maximum_payment_installments INTEGER,

    has_credit_card_payment BOOLEAN,
    has_boleto_payment BOOLEAN,
    has_voucher_payment BOOLEAN,
    has_debit_card_payment BOOLEAN,

    CONSTRAINT pk_curated_order_features PRIMARY KEY (order_id)
);

CREATE TABLE IF NOT EXISTS curated.order_targets(
    order_id TEXT NOT NULL,
    non_delivery_label SMALLINT,
    late_delivery_label SMALLINT,

    CONSTRAINT pk_curated_order_targets PRIMARY KEY (order_id),

    CONSTRAINT fk_curated_order_targets_features FOREIGN KEY (order_id) REFERENCES curated.order_features (order_id),
    CONSTRAINT chk_non_delivery_label CHECK (non_delivery_label IN (0,1)),
    CONSTRAINT chk_late_delivery_label CHECK (late_delivery_label IN (0,1))
);

CREATE OR REPLACE VIEW curated.non_delivery_dataset AS
SELECT
    features.*,
    targets.non_delivery_label AS target
FROM curated.order_features AS features
JOIN curated.order_targets AS targets
    USING (order_id)
WHERE targets.non_delivery_label IS NOT NULL;

CREATE OR REPLACE VIEW curated.late_delivery_dataset AS
SELECT
    features.*,
    targets.late_delivery_label AS target
FROM curated.order_features AS features
JOIN curated.order_targets AS targets
    USING (order_id)
WHERE targets.late_delivery_label IS NOT NULL;