import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logger(output_dir, name, level=logging.INFO):
    """
    Налаштовує логер з виведенням у файл та консоль.
    
    Args:
        output_dir (str): Директорія для файлів логу
        name (str): Ім'я логера
        level: Рівень логування
        
    Returns:
        Logger: Налаштований логер
    """
    # Створюємо директорію для логів, якщо вона не існує
    log_dir = os.path.join(output_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Шлях до файлу логу
    log_file = os.path.join(log_dir, f"{name}.log")
    
    # Створюємо логер
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Видаляємо існуючі обробники, якщо вони є
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Формат повідомлень логу
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Обробник для запису в файл з ротацією
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Обробник для виведення в консоль
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    logger.info(f"Логер {name} налаштовано, запис у файл: {log_file}")
    return logger