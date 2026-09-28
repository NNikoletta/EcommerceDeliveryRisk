import json
import os

import psycopg
import pytest
from psycopg import sql

from ecommercedeliveryrisk.config import Settings
from ecommercedeliveryrisk.ingest_data import RAW_TABLES, connect_to_database, run_ingestion

pytestmark = pytest.mark.integration

FIXTURE_CSVS = {
    "customers": (
        "olist_customers_dataset.csv",
        (
            "customer_id,customer_unique_id,customer_zip_code_prefix,"
            "customer_city,customer_state\n"
            "customer-1,unique-1,12345,sao paulo,SP\n"
        ),
    ),
    "geolocation": (
        "olist_geolocation_dataset.csv",
        (
            "geolocation_zip_code_prefix,geolocation_lat,geolocation_lng,"
            "geolocation_city,geolocation_state\n"
            "12345,-23.5,-46.6,sao paulo,SP\n"
        ),
    ),
    "order_items": (
        "olist_order_items_dataset.csv",
        (
            "order_id,order_item_id,product_id,seller_id,"
            "shipping_limit_date,price,freight_value\n"
            "order-1,1,product-1,seller-1,"
            "2018-01-02 12:00:00,10.50,2.00\n"
        ),
    ),
    "order_payments": (
        "olist_order_payments_dataset.csv",
        (
            "order_id,payment_sequential,payment_type,"
            "payment_installments,payment_value\n"
            "order-1,1,credit_card,1,12.50\n"
        ),
    ),
    "order_reviews": (
        "olist_order_reviews_dataset.csv",
        (
            "review_id,order_id,review_score,review_comment_title,"
            "review_comment_message,review_creation_date,"
            "review_answer_timestamp\n"
            "review-1,order-1,5,great,excellent,"
            "2018-01-04 10:00:00,2018-01-05 10:00:00\n"
        ),
    ),
    "orders": (
        "olist_orders_dataset.csv",
        (
            "order_id,customer_id,order_status,order_purchase_timestamp,"
            "order_approved_at,order_delivered_carrier_date,"
            "order_delivered_customer_date,order_estimated_delivery_date\n"
            "order-1,customer-1,delivered,"
            "2018-01-01 09:00:00,2018-01-01 10:00:00,"
            "2018-01-02 10:00:00,2018-01-03 10:00:00,"
            "2018-01-04 10:00:00\n"
        ),
    ),
    "products": (
        "olist_products_dataset.csv",
        (
            "product_id,product_category_name,product_name_lenght,"
            "product_description_lenght,product_photos_qty,"
            "product_weight_g,product_length_cm,product_height_cm,"
            "product_width_cm\n"
            "product-1,category-1,10,20,1,500,10,5,8\n"
        ),
    ),
    "sellers": (
        "olist_sellers_dataset.csv",
        (
            "seller_id,seller_zip_code_prefix,seller_city,seller_state\n"
            "seller-1,12345,sao paulo,SP\n"
        ),
    ),
    "translations": (
        "product_category_name_translation.csv",
        ("product_category_name,product_category_name_english\ncategory-1,category one\n"),
    ),
}


@pytest.fixture
def integration_settings(tmp_path) -> Settings:
    if os.getenv("RUN_POSTGRES_INTEGRATION") != "1":
        pytest.skip("PostgreSQL integration testing is disabled.")

    database_name = os.getenv("POSTGRES_DB", "").strip()

    if database_name != "ecommerce_test":
        pytest.fail(
            "Refusing to run PostgreSQL integraion test:"
            "POSTGRES+DB must be 'ecommerce_test',"
            f"but received {database_name!r}.",
            pytrace=False,
        )

    raw_data_dir = tmp_path / "raw"
    manifests_data_dir = tmp_path / "manifests"

    raw_data_dir.mkdir()
    manifests_data_dir.mkdir()

    manifest = {}

    for table_name, (file_name, csv_content) in FIXTURE_CSVS.items():
        csv_path = raw_data_dir / file_name
        csv_path.write_text(csv_content, encoding="utf-8")

        header = csv_content.splitlines()[0].split(",")

        manifest[table_name] = {"row_count": 1, "column_names": header}

    manifest_path = manifests_data_dir / "benchmark_raw_data_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    return Settings(
        kaggle_dataset="test-owner/test-dataset",
        raw_data_dir=raw_data_dir,
        manifests_data_dir=manifests_data_dir,
    )


def test_postgres_ingestion_pipeline(integration_settings: Settings) -> None:
    run_ingestion(settings=integration_settings)

    # Running the ingestion twice to verify it is repeatable.
    run_ingestion(settings=integration_settings)

    with connect_to_database() as connection, connection.cursor() as cursor:
        for schema_name in ("raw", "staging"):
            for table_name in RAW_TABLES:
                statement = sql.SQL("SELECT COUNT(*) FROM {}.{};").format(
                    sql.Identifier(schema_name), sql.Identifier(table_name)
                )

                cursor.execute(statement)
                result = cursor.fetchone()
                assert result is not None
                assert result[0] == 1

        cursor.execute(
            """
                SELECT
                    pg_typeof(order_item_id)::TEXT,
                    pg_typeof(price)::TEXT,
                    pg_typeof(shipping_limit_date)::TEXT
                FROM staging.order_items
                """
        )

        assert cursor.fetchone() == ("integer", "numeric", "timestamp without time zone")

        cursor.execute(
            """
                SELECT COUNT(*)
                FROM staging.order_items AS items
                JOIN staging.orders AS orders
                    USING (order_id)
                JOIN staging.products AS products
                    USING (product_id)
                JOIN staging.sellers AS sellers
                    USING (seller_id)
                """
        )

        assert cursor.fetchone() == (1,)


def test_failed_staging_load_rolls_back_ingestion(integration_settings: Settings) -> None:

    run_ingestion(settings=integration_settings)

    order_items_path = integration_settings.raw_data_dir / "olist_order_items_dataset.csv"

    invalid_content = FIXTURE_CSVS["order_items"][1].replace("product-1", "missing-product")

    order_items_path.write_text(invalid_content, encoding="utf-8")

    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        run_ingestion(settings=integration_settings)

    with connect_to_database() as connection, connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT product_id
                FROM raw.order_items
                WHERE order_id = 'order-1'
                """
        )
        assert cursor.fetchone() == ("product-1",)

        cursor.execute(
            """
                SELECT product_id
                FROM staging.order_items
                WHERE order_id = 'order-1'
                """
        )
        assert cursor.fetchone() == ("product-1",)
