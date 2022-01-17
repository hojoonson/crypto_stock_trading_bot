import logging

LOG_FORMATTER = logging.Formatter(
    "[%(asctime)s] [%(process)d] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d:%H:%M:%S"
)
logger = logging.getLogger("crypto_trader")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
handler.setFormatter(LOG_FORMATTER)
logger.addHandler(handler)
logger.addHandler(logging.FileHandler(filename="./log/trading.log"))
