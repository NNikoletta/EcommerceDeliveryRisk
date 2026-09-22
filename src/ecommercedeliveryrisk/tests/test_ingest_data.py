import json
from multiprocessing import connection
from unittest.mock import MagicMock, Mock

import pytest

import ecommercedeliveryrisk.ingest_data as ingestion_module
from ecommercedeliveryrisk.config import manifests_data_dir


def test_validate_table_row_data_count_sucess(monkeypatch):
    connection = Mock()
    get_row_count = Mock(return_value=100)

    monkeypatch.setattr(ingestion_module, "get_table_row_count", get_row_count)

    ingestion_module.validate_table_row_count(
        connection=connection, table_name="customers", expected_row_count=100
    )

    get_row_count.assert_called_once_with(connection=connection, table_name="customers")


def test_validate_table_row_count_missmatch(monkeypatch):
    connection = Mock()
    get_row_count = Mock(return_value=99)

    monkeypatch.setattr(ingestion_module, "get_table_row_count", get_row_count)

    with pytest.raises(ingestion_module.RowCountMismatchError, match="Expected row count: 100"):
        ingestion_module.validate_table_row_count(
            connection=connection, table_name="customers", expected_row_count=100
        )


def test_get_table_row_count_returns_count():
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = (100,)

    result = ingestion_module.get_table_row_count(connection=connection, table_name="customers")

    assert result == 100
    cursor.execute.assert_called_once()


def test_get_table_row_count_raises_error_when_database_returns_nothing():
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = None

    with pytest.raises(
        RuntimeError, match="PostgreSQL returned no row count for raw table 'customers'."
    ):
        ingestion_module.get_table_row_count(connection=connection, table_name="customers")


def test_execute_sql_file(tmp_path):
    sql_file = tmp_path / "create_tables.sql"
    sql_file.write_text("CREATE TABLE example (id INTEGER);", encoding="utf-8")

    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value

    ingestion_module.execute_sql_file(connection=connection, sql_file=sql_file)

    cursor.execute.assert_called_once_with("CREATE TABLE example (id INTEGER);")


def test_execute_sql_file_when_file_is_missing(tmp_path):
    sql_file = tmp_path / "create_tables.sql"

    connection = MagicMock()

    with pytest.raises(FileNotFoundError, match="SQL file was not found: "):
        ingestion_module.execute_sql_file(connection=connection, sql_file=sql_file)

    connection.cursor.assert_not_called()


def test_ingest_raw_data_and_validate_files(tmp_path, monkeypatch):
    raw_data_dir = tmp_path / "raw"
    manifests_data_dir = tmp_path / "manifests"

    raw_data_dir.mkdir()
    manifests_data_dir.mkdir()

    csv_path = raw_data_dir / "customers.csv"
    csv_path.write_text("customer_id\ncustomer-1\n", encoding="utf-8")

    manifest_path = manifests_data_dir / "benchmark_raw_data_manifest.json"
    manifest_path.write_text(
        """
        {
        "customers":{
                    "row_count": 1,
                    "column_names": ["customer_id"]
                    }
        }
        """,
        encoding="utf-8",
    )

    monkeypatch.setattr(ingestion_module, "RAW_TABLES", {"customers": "customers.csv"})

    copy_csv = Mock()
    validate_row_count = Mock()

    monkeypatch.setattr(ingestion_module, "copy_csv_to_table", copy_csv)
    monkeypatch.setattr(ingestion_module, "validate_table_row_count", validate_row_count)

    connection = Mock()

    ingestion_module.ingest_raw_data(
        connection=connection, raw_data_dir=raw_data_dir, manifests_data_dir=manifests_data_dir
    )

    copy_csv.assert_called_once_with(
        connection=connection,
        table_name="customers",
        column_names=["customer_id"],
        csv_path=csv_path,
    )

    validate_row_count.assert_called_once_with(
        connection=connection, table_name="customers", expected_row_count=1
    )


def test_ingest_raw_data_fail_when_csv_is_missing(tmp_path, monkeypatch):
    raw_data_dir = tmp_path / "raw"
    manifests_data_dir = tmp_path / "manifests"

    raw_data_dir.mkdir()
    manifests_data_dir.mkdir()

    manifest_path = manifests_data_dir / "benchmark_raw_data_manifest.json"
    manifest_path.write_text(
        """
    {
        "customers":{
            "row_count": 1
        }
    }
    """,
        encoding="utf-8",
    )

    monkeypatch.setattr(ingestion_module, "RAW_TABLES", {"customers": "customers.csv"})

    copy_csv = Mock()
    monkeypatch.setattr(ingestion_module, "copy_csv_to_table", copy_csv)

    with pytest.raises(FileNotFoundError, match="Required ingestion file was not found:"):
        ingestion_module.ingest_raw_data(
            connection=Mock(), raw_data_dir=raw_data_dir, manifests_data_dir=manifests_data_dir
        )

    copy_csv.assert_not_called()
