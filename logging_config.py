import logging
import os


def setup_logging(name: str, log_file: str):
    # Создаем директорию для логов, если ее нет
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # Создаем логгер
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Уровень логирования

    # Создаем форматters
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Создаем обработчик для записи логов в файл
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    # Создаем обработчик для вывода логов в консоль
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Добавляем обработчики к логгеру
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger