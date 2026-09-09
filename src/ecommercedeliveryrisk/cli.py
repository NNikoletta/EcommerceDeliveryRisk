from dotenv import load_dotenv
import logging

from ecommercedeliveryrisk.config import load_settings, project_root

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

logger = logging.getLogger(__name__)

def main() -> None:
    try:
        load_dotenv(project_root / ".env")
        settings = load_settings()

        from ecommercedeliveryrisk.download_data import download_raw_data
        from ecommercedeliveryrisk.validate_data import validate_data, compare_manifests

        download_raw_data(settings=settings)
        validate_data(data_dir=settings.raw_data_dir,
                      manifests_dir=settings.manifests_data_dir)
        compare_manifests(manifests_dir=settings.manifests_data_dir)

    except (FileNotFoundError, ValueError) as error:
        logger.error("Pipeline failed: %s", error)
        raise SystemExit(0)
    except Exception:
        logger.exception("Pipeline failed unexpectedly.")
        raise

