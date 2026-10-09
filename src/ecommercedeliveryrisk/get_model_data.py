from typing import Literal

import pandas as pd
import psycopg
from psycopg import sql

from ecommercedeliveryrisk.ingest_data import connect_to_database

ModelName = Literal["non_delivery", "late_delivery"]

MODEL_DATASET_VIEWS = {
    "non_delivery": "non_delivery_dataset",
    "late_delivery": "late_delivery_dataset",
}


def load_model_dataset(connection: psycopg.Connection, model_name: ModelName) -> pd.DataFrame:
    view_name = MODEL_DATASET_VIEWS[model_name]

    statement = sql.SQL(
        """
        SELECT * 
        FROM curated.{}
        ORDER BY order_approved_at ASC, order_id ASC;
        """
    ).format(sql.Identifier(view_name))

    with connection.cursor() as cursor:
        cursor.execute(statement)

        if cursor.description is None:
            raise RuntimeError(f"No columns were returned from curated {view_name}.")

        column_names = [column.name for column in cursor.description]
        rows = cursor.fetchall()

    return pd.DataFrame(rows, columns=column_names)


def load_dataset(model_name) -> tuple:
    with connect_to_database() as connection:
        delivery_data = load_model_dataset(connection=connection, model_name=model_name)

    features = delivery_data.drop(
        columns=[
            "target",
            "order_id",
            "customer_unique_id",
            "order_purchase_timestamp",
            "order_approved_at",
        ]
    ).copy()

    categorical_columns = ["customer_state", "customer_zip_code_prefix"]
    features[categorical_columns] = features[categorical_columns].astype("category")
    numeric_columns = features.columns.difference(categorical_columns)
    features[numeric_columns] = features[numeric_columns].astype("float64")

    targets = delivery_data["target"].to_numpy()

    return features, targets
