import argparse
import logging
from collections.abc import Sequence

from dotenv import load_dotenv

from ecommercedeliveryrisk.classification_pipeline import (
    create_final_eval_split,
    create_optimization_split,
    optimization_pipeline,
)
from ecommercedeliveryrisk.config import load_settings, project_root
from ecommercedeliveryrisk.download_data import download_raw_data
from ecommercedeliveryrisk.ingest_data import run_ingestion
from ecommercedeliveryrisk.validate_data import compare_manifests, validate_data

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ecommercedeliveryrisk",
        description="Download, validate, and ingest Brazilian Ecommerce Delivery Risk raw data.",
    )

    mode = parser.add_mutually_exclusive_group()

    mode.add_argument("--download", action="store_true", help="Download raw data.")

    mode.add_argument(
        "--replace-existing",
        action="store_true",
        help="Replace the existing raw data with a validated download.",
    )

    mode.add_argument(
        "--validate",
        action="store_true",
        help="Validate the existing raw data without downloading.",
    )

    mode.add_argument(
        "--ingest",
        action="store_true",
        help="Load the validated raw CSV files into PostgreSQL and create the curated datasets for the ML model.",
    )

    mode.add_argument(
        "--create-optimization-split",
        action="store_true",
        help="Create, validate, and save optimization/testing data split.",
    )

    mode.add_argument(
        "--create-final-eval-split",
        action="store_true",
        help="Create, validate, and save final evaluation data split.",
    )

    mode.add_argument(
        "--optimization-pipeline",
        action="store_true",
        help="Run the classification pipeline for optimization purposes and testing on a previously saved fixed data split.",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    args = build_parser().parse_args(argv)

    try:
        load_dotenv(project_root / ".env")
        settings = load_settings()

        if (
            not args.download
            and not args.replace_existing
            and not args.validate
            and not args.ingest
            and not args.create_optimization_split
            and not args.create_final_eval_split
            and not args.optimization_pipeline
        ):
            download_raw_data(settings=settings, replace_existing=False)
            validate_data(data_dir=settings.raw_data_dir, manifests_dir=settings.manifests_data_dir)
            compare_manifests(manifests_dir=settings.manifests_data_dir)
            run_ingestion(settings=settings)
        elif args.download or args.replace_existing:
            download_raw_data(settings=settings, replace_existing=args.replace_existing)
        elif args.validate:
            validate_data(data_dir=settings.raw_data_dir, manifests_dir=settings.manifests_data_dir)
            compare_manifests(manifests_dir=settings.manifests_data_dir)
        elif args.ingest:
            validate_data(data_dir=settings.raw_data_dir, manifests_dir=settings.manifests_data_dir)
            compare_manifests(manifests_dir=settings.manifests_data_dir)
            run_ingestion(settings=settings)
        elif args.create_optimization_split:
            create_optimization_split("non_delivery")
        elif args.create_final_eval_split:
            create_final_eval_split("non_delivery")
        elif args.optimization_pipeline:
            optimization_pipeline("non_delivery")

    except (FileNotFoundError, ValueError) as error:
        logger.exception("Pipeline failed: %s", error)
        raise SystemExit(1) from None
    except Exception:
        logger.exception("Pipeline failed unexpectedly.")
        raise
