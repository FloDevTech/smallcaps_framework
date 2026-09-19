"""Configuración del logger persistente para el framework."""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

LOG_NAME = "smallcaps"
FILE_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
CONSOLE_FORMAT = "%(levelname)s: %(message)s"
MAX_LINES_PER_FILE = 50


class RotatingFileHandler(logging.FileHandler):
    """Handler que rota el archivo cuando supera MAX_LINES_PER_FILE líneas.

    El archivo activo siempre es 'last.log'. Cuando se rota, se renombra
    a 'YYYYMMDDHHmm.log' y se crea un nuevo 'last.log'.
    """

    def __init__(self, log_dir: Path):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.last_log_path = self.log_dir / "last.log"
        super().__init__(self.last_log_path, encoding="utf-8")

    def emit(self, record: logging.LogRecord) -> None:
        super().emit(record)
        self._check_rotation()

    def _count_lines(self) -> int:
        if not self.last_log_path.exists():
            return 0
        with self.last_log_path.open(encoding="utf-8") as f:
            return sum(1 for _ in f)

    def _check_rotation(self) -> None:
        if self._count_lines() < MAX_LINES_PER_FILE:
            return
        self.close()
        timestamp = datetime.now().strftime("%Y%m%d%H%M")
        rotated_path = self.log_dir / f"{timestamp}.log"
        counter = 1
        while rotated_path.exists():
            rotated_path = self.log_dir / f"{timestamp}_{counter}.log"
            counter += 1
        self.last_log_path.rename(rotated_path)
        self.baseFilename = str(self.last_log_path.absolute())
        self.stream = self._open()


def setup_logger(data_dir: Path | str) -> logging.Logger:
    """Configura el logger con salida a archivo y consola.

    El archivo de log activo es {data_dir}/last.log. Cuando supera 50 líneas,
    se rota a {data_dir}/YYYYMMDDHHmm.log y se crea un nuevo last.log.
    Llamar una vez al inicio del programa.

    Returns:
        El logger configurado con nombre 'smallcaps'.
    """
    logger = logging.getLogger(LOG_NAME)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        file_handler = RotatingFileHandler(Path(data_dir))
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(FILE_FORMAT, datefmt="%Y-%m-%d %H:%M:%S"))

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(CONSOLE_FORMAT))

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger
