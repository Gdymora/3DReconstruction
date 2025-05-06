import os
import subprocess
import shutil
import logging


def run_command(command, env=None, logger=None):
    """
    Запускає команду в підпроцесі та логує результат в режимі реального часу.
    """
    if logger is None:
        logger = logging.getLogger("command_runner")

    logger.info(f"Виконання команди: {command}")

    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1,  # Буферизація порядкова
            env=env,
        )

        # Читаємо вивід у режимі реального часу
        for line in process.stdout:
            line = line.strip()
            if line:
                logger.info(f"STDOUT: {line}")

        # Читаємо помилки у режимі реального часу
        for line in process.stderr:
            line = line.strip()
            if line:
                logger.warning(f"STDERR: {line}")

        # Чекаємо завершення процесу
        return_code = process.wait()

        if return_code != 0:
            logger.error(f"Команда завершилася з кодом {return_code}")
            raise RuntimeError(f"Помилка виконання команди: {command}")

        logger.info(f"Команда виконана успішно")
        return ""

    except Exception as e:
        logger.error(f"Помилка при виконанні команди: {str(e)}")
        raise


def create_directory(path, logger=None):
    """
    Створює директорію, якщо вона не існує.

    Args:
        path (str): Шлях до директорії
        logger (Logger, optional): Логер для запису повідомлень
    """
    if logger is None:
        logger = logging.getLogger("file_utils")

    if not os.path.exists(path):
        os.makedirs(path)
        logger.info(f"Створено директорію: {path}")


def clean_temp_files(directory, include_subdirs=True, logger=None):
    """
    Видаляє тимчасові файли та директорії.

    Args:
        directory (str): Директорія для очищення
        include_subdirs (bool): Чи включати піддиректорії
        logger (Logger, optional): Логер для запису повідомлень
    """
    if logger is None:
        logger = logging.getLogger("file_utils")

    temp_dirs = ["temp", "__pycache__", "cache"]
    temp_extensions = [".log", ".tmp"]

    try:
        if not os.path.exists(directory):
            logger.warning(f"Директорія для очищення не існує: {directory}")
            return

        # Видаляємо тимчасові файли
        for root, dirs, files in os.walk(directory):
            # Видаляємо тимчасові директорії
            if include_subdirs:
                for dir_name in dirs.copy():  # Копія для безпечної ітерації
                    if dir_name in temp_dirs:
                        try:
                            dir_path = os.path.join(root, dir_name)
                            shutil.rmtree(dir_path)
                            logger.info(f"Видалено тимчасову директорію: {dir_path}")
                            dirs.remove(
                                dir_name
                            )  # Видаляємо з списку, щоб os.walk не заходив всередину
                        except Exception as e:
                            logger.warning(
                                f"Не вдалося видалити директорію {dir_path}: {str(e)}"
                            )

            # Видаляємо тимчасові файли
            for file_name in files:
                if any(file_name.endswith(ext) for ext in temp_extensions):
                    try:
                        file_path = os.path.join(root, file_name)
                        os.remove(file_path)
                        logger.info(f"Видалено тимчасовий файл: {file_path}")
                    except Exception as e:
                        logger.warning(
                            f"Не вдалося видалити файл {file_path}: {str(e)}"
                        )

        logger.info(f"Очищення тимчасових файлів у {directory} завершено")
    except Exception as e:
        logger.error(f"Помилка при очищенні тимчасових файлів: {str(e)}")
