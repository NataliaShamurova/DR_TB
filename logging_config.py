import logging
import os


def setup_logging(name: str, log_file: str, level=logging.DEBUG) -> logging.Logger:
    """Настройка логирования для приложения."""

    # Создаем папку для логов, если она не существует
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # Формат логирования
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Создаем обработчик для записи логов в файл
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    # Создаем обработчик для вывода в консоль
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Создаем логгер
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger