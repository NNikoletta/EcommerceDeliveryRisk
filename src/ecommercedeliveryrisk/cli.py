import argparse
import logging
from collections.abc import Sequence

from dotenv import load_dotenv

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

    mode.add_argument(
        "--download",
        action="store_true",
        help="Download raw data."
    )

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
        help="Load the validated raw CSV files into PostgreSQL.",
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

        if not args.download and not args.replace_existing and not args.validate and not args.ingest:
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
            run_ingestion(settings=settings)

    except (FileNotFoundError, ValueError) as error:
        logger.error("Pipeline failed: %s", error)
        raise SystemExit(1) from None
    except Exception:
        logger.exception("Pipeline failed unexpectedly.")
        raise
