from ecommercedeliveryrisk.download_data import download_raw_data
from ecommercedeliveryrisk.validate_data import validate_raw_data

def main() -> None:
    download_raw_data()
    validate_raw_data()

if __name__ == "__main__":
    main()