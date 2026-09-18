import json
import logging
import os
from pathlib import Path
from typing import LiteralString, cast

import psycopg
from psycopg import sql

from ecommercedeliveryrisk.config import Settings, project_root

logger = logging.getLogger(__name__)

RAW_TABLES = {
    "customers": "olist_customers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
    "order_reviews": "olist_order_reviews_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "translations": "product_category_name_translation.csv",
}


def connect_to_database() -> psycopg.Connection:
    return psycopg.connect(
        host=os.environ["POSTGRES_HOST"],
        port=os.environ["POSTGRES_PORT"],
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )


def read_trusted_sql(sql_file: Path) -> LiteralString:
    return cast(
        LiteralString,
        sql_file.read_text(encoding="utf-8"),
    )


def execute_sql_file(connection: psycopg.Connection, sql_file: Path) -> None:

    if not sql_file.is_file():
        raise FileNotFoundError(f"SQL file was not found: {sql_file}")

    statement = read_trusted_sql(sql_file)

    with connection.cursor() as cursor:
        cursor.execute(statement)

    logger.info("File '%s' was successfully executed.", sql_file.name)


def copy_csv_to_table(connection: psycopg.Connection, table_name: str, csv_path: Path) -> None:
    truncate_statement = sql.SQL("TRUNCATE TABLE raw.{}").format(sql.Identifier(table_name))

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

        with csv_path.open("rb") as csv_file, cursor.copy(copy_statement) as copy:
            while chunk := csv_file.read(1024 * 1024):
                copy.write(chunk)


def get_table_row_count(connection: psycopg.Connection, table_name: str) -> int:
    row_count = sql.SQL("SELECT COUNT(*) FROM raw.{}").format(sql.Identifier(table_name))

    with connection.cursor() as cursor:
        cursor.execute(row_count)
        result = cursor.fetchone()

    if result is None:
        raise RuntimeError(f"PostgreSQL returned no row count for raw table '{table_name}'.")

    return result[0]


class RowCountMismatchError(ValueError):
    pass


def validate_table_row_count(
    connection: psycopg.Connection, table_name: str, expected_row_count: int
) -> None:
    actual_row_count = get_table_row_count(connection=connection, table_name=table_name)

    if actual_row_count != expected_row_count:
        raise RowCountMismatchError(
            f"Unexpected number of rows found in table '{table_name}'.\n"
            f"Expected row count: {expected_row_count}\n"
            f"Found: {actual_row_count}"
        )


def ingest_raw_data(
    connection: psycopg.Connection, raw_data_dir: Path, manifests_data_dir: Path
) -> None:
    benchmark_manifest_path = manifests_data_dir / "benchmark_raw_data_manifest.json"
    with benchmark_manifest_path.open("r", encoding="utf-8") as json_file:
        benchmark_manifest_data = json.load(json_file)

    for table_name, file_name in RAW_TABLES.items():
        csv_path = raw_data_dir / file_name

        if not csv_path.is_file():
            raise FileNotFoundError(f"Required ingestion file was not found: {csv_path}")

        copy_csv_to_table(connection=connection, table_name=table_name, csv_path=csv_path)
        validate_table_row_count(
            connection=connection,
            table_name=table_name,
            expected_row_count=benchmark_manifest_data[table_name]["row_count"],
        )

    logger.info("Raw data files ingested successfully.")


def run_ingestion(settings: Settings) -> None:
    create_schemas = project_root / "sql" / "migrations" / "001_create_schemas.sql"

    raw_tables_sql = project_root / "sql" / "migrations" / "002_create_raw_tables.sql"

    staging_tables_sql = project_root / "sql" / "migrations" / "003_create_staging_tables.sql"

    load_staging_tables_sql = project_root / "sql" / "staging" / "load_staging_tables.sql"

    with connect_to_database() as connection:
        execute_sql_file(connection=connection, sql_file=create_schemas)
        execute_sql_file(connection=connection, sql_file=raw_tables_sql)
        execute_sql_file(connection=connection, sql_file=staging_tables_sql)

        ingest_raw_data(
            connection=connection,
            raw_data_dir=settings.raw_data_dir,
            manifests_data_dir=settings.manifests_data_dir,
        )

        execute_sql_file(connection=connection, sql_file=load_staging_tables_sql)
