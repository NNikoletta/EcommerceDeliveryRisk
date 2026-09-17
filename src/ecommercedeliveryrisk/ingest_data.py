import os
import psycopg
from psycopg import sql

from pathlib import Path

from ecommercedeliveryrisk.config import project_root


RAW_TABLES = {
    "customers": "olist_customers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
    "order_reviews": "olist_order_reviews_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "product_category_name_translation": "product_category_name_translation.csv"
}

def connect_to_database() -> psycopg.Connection:
    return psycopg.connect(
        host = os.environ["POSTGRES_HOST"],
        port = os.environ["POSTGRES_PORT"],
        dbname = os.environ["POSTGRES_DB"],
        user = os.environ["POSTGRES_USER"],
        password = os.environ["POSTGRES_PASSWORD"]
    )

def create_raw_tables(
        connection: psycopg.Connection,
        sql_file: Path
) -> None:
    statement = sql_file.read_text(encoding="utf-8")
    connection.execute(statement)

def copy_csv_to_table(
        connection: psycopg.Connection,
        table_name: str,
        csv_path: Path
) -> None:
    truncate_statement = sql.SQL(
        "TRUNCATE TABLE raw.{}"
    ).format(sql.Identifier(table_name))

    copy_statement = sql.SQL(
        """
        COPY raw.{}
        FROM STDIN
        WITH (
            FORMAT CSV,
            HEADER TRUE,
            ENCODING 'UTF8'
        )
        """
    ).format(sql.Identifier(table_name))

    with connection.cursor() as cursor:
        cursor.execute(truncate_statement)

        with csv_path.open("rb") as csv_file:
            with cursor.copy(copy_statement) as copy:
                while chunk := csv_file.read(1024 * 1024):
                    copy.write(chunk)

def ingest_raw_data(
        connection: psycopg.Connection,
        raw_data_dir: Path
) -> None:
    for table_name, file_name in RAW_TABLES.items():
        csv_path = raw_data_dir / file_name

        if not csv_path.is_file():
            raise FileNotFoundError(
                f"Required ingestion file was not found: {csv_path}"
            )

        copy_csv_to_table(
            connection=connection,
            table_name=table_name,
            csv_path=csv_path
            )

def run_ingestion(settings) -> None:
    sql_file = (
        project_root
        / "sql"
        / "migrations"
        / "002_create_raw_tables.sql"
    )


    with connect_to_database() as connection:
        create_raw_tables(
            connection=connection,
            sql_file=sql_file
        )

        ingest_raw_data(
            connection=connection,
            raw_data_dir=settings.raw_data_dir
        )