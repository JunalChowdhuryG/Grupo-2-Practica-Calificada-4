import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/app/reports/notify.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def notify(message):
    logger.info(f"Received message: {message}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        logger.error("Uso: python notify.py <message>")
        sys.exit(1)
    notify(sys.argv[1])