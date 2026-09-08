from dotenv import load_dotenv

from ecommercedeliveryrisk.config import load_settings, project_root

def main() -> None:
    load_dotenv(project_root/".env")
    settings = load_settings()

    from ecommercedeliveryrisk.download_data import download_raw_data
    from ecommercedeliveryrisk.validate_data import validate_raw_data

    download_raw_data(settings=settings)
    validate_raw_data(data_dir=settings.raw_data_dir,
                      manifest_dir=settings.manifests_data_dir)