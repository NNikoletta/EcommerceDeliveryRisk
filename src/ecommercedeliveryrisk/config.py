import os
from pathlib import Path
from dataclasses import dataclass


@dataclass
class DownloadResult:
    download_date: str
    dataset_metadata: list[dict]
    dataset_version: int

@dataclass(frozen=True)
class ExpectedFiles:
    customers: str = "olist_customers_dataset.csv"
    geolocation: str = "olist_geolocation_dataset.csv"
    order_items: str = "olist_order_items_dataset.csv"
    order_payments: str = "olist_order_payments_dataset.csv"
    order_reviews: str = "olist_order_reviews_dataset.csv"
    orders: str = "olist_orders_dataset.csv"
    products: str = "olist_products_dataset.csv"
    sellers: str = "olist_sellers_dataset.csv"
    translation: str = "product_category_name_translation.csv"


project_root = Path(__file__).resolve().parents[2]

raw_data_dir = project_root / "data" / "raw"
manifests_data_dir = project_root / "data" / "manifests"


@dataclass(frozen=True)
class Settings:
    kaggle_dataset: str
    raw_data_dir: Path
    manifests_data_dir: Path

    def __post_init__(self) -> None:
        parts = self.kaggle_dataset.split("/")

        if(len(parts) != 2
           or not all(parts)
           or any(character.isspace() for character in self.kaggle_dataset)):
            raise ValueError("KAGGLE_DATASET must use the format 'owner/dataset'.")

        for name, path in (("raw_data_dir", self.raw_data_dir),
                           ("manifests_data_dir", self.manifests_data_dir)):
            if not isinstance(path, Path):
                raise TypeError(f"Expected {name} to be a Path object.")

            if path.exists() and not path.is_dir():
                raise ValueError(f"{name} must point to a directory: {path}")


def load_settings() -> Settings:
    dataset = os.getenv("KAGGLE_DATASET", "").strip()

    if not dataset:
        raise ValueError("KAGGLE_DATASET environment variable is missing or empty.")

    return Settings(kaggle_dataset=dataset,
                    raw_data_dir=raw_data_dir,
                    manifests_data_dir=manifests_data_dir)


@dataclass(frozen=True)
class PostgresSettings:
    host: str
    port: int
    database: str
    user: str
    password: str

    def __post_init__(self) -> None:
        parts = self.kaggle_dataset.split("/")

        if(len(parts) != 2
           or not all(parts)
           or any(character.isspace() for character in self.kaggle_dataset)):
            raise ValueError("KAGGLE_DATASET must use the format 'owner/dataset'.")

        for name, path in (("raw_data_dir", self.raw_data_dir),
                           ("manifests_data_dir", self.manifests_data_dir)):
            if not isinstance(path, Path):
                raise TypeError(f"Expected {name} to be a Path object.")

            if path.exists() and not path.is_dir():
                raise ValueError(f"{name} must point to a directory: {path}")