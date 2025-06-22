import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/app/reports/notify.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def notify(message="Test message"):
    logger.info(f"Received message: {message}")

if __name__ == "__main__":
    notify()