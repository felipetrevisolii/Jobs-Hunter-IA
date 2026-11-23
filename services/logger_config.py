import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime


def configurar_logger():
    base_dir = Path(__file__).resolve().parent.parent
    logs_dir = base_dir / "logs"
    logs_dir.mkdir(exist_ok=True)

    data_hoje = datetime.now().strftime("%Y-%m-%d")
    arquivo_log = logs_dir / f"job_hunter_{data_hoje}.log"

    logger = logging.getLogger("job_hunter")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    formato = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%d/%m/%Y %H:%M:%S"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formato)

    arquivo_handler = RotatingFileHandler(
        arquivo_log,
        maxBytes=2_000_000,
        backupCount=5,
        encoding="utf-8"
    )
    arquivo_handler.setFormatter(formato)

    logger.addHandler(console_handler)
    logger.addHandler(arquivo_handler)

    return logger