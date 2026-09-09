import argparse
import logging
from collections.abc import Sequence
from dotenv import load_dotenv

from ecommercedeliveryrisk.config import load_settings, project_root
from ecommercedeliveryrisk.download_data import download_raw_data
from ecommercedeliveryrisk.validate_data import validate_data, compare_manifests

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

logger = logging.getLogger(__name__)

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='ecommercedeliveryrisk',
                                     description='Download and validate Brazilian Ecommerce Delivery Risk raw data.')

    mode = parser.add_mutually_exclusive_group()

    mode.add_argument("--replace-existing",
                      action="store_true",
                      help="Replace the existing raw data with a validated download.")

    mode.add_argument("--validate-only",
                      action="store_true",
                      help="Validate the existing raw data without downloading.")

    return parser

def main(argv: Sequence[str] | None = None) -> None:
    args = build_parser().parse_args(argv)

    try:
        load_dotenv(project_root / ".env")
        settings = load_settings()

        if not args.validate_only:
            download_raw_data(settings=settings,
                              replace_existing=args.replace_existing)

        validate_data(data_dir=settings.raw_data_dir,
                      manifests_dir=settings.manifests_data_dir)

        compare_manifests(manifests_dir=settings.manifests_data_dir)

    except (FileNotFoundError, ValueError) as error:
        logger.error("Pipeline failed: %s", error)
        raise SystemExit(1)
    except Exception:
        logger.exception("Pipeline failed unexpectedly.")
        raise

