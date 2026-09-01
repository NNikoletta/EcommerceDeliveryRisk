import os
from pathlib import Path
from dotenv import load_dotenv
from dataclasses import dataclass


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
kaggle_dataset_name = "olistbr/brazilian-ecommerce"

load_dotenv()
KAGGLE_USERNAME = os.getenv("KAGGLE_USERNAME")
KAGGLE_KEY = os.getenv("KAGGLE_KEY")
KAGGLE_DATASET = os.getenv("KAGGLE_DATASET")
