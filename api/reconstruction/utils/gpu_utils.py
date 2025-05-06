import subprocess
import logging


def check_gpu_availability():
    """
    Перевіряє наявність та доступність GPU для CUDA операцій.

    Returns:
        bool: True, якщо GPU доступне, інакше False
    """
    logger = logging.getLogger("gpu_check")

    try:
        # Перевірка наявності GPU через nvidia-smi
        result = subprocess.run(
            ["nvidia-smi"], capture_output=True, text=True, check=False
        )

        if result.returncode == 0:
            logger.info("NVIDIA GPU доступне")
            # Навіть якщо OpenCV не підтримує CUDA, повертаємо True
            # щоб COLMAP міг використовувати GPU
            return True
        else:
            logger.warning("GPU не виявлено через nvidia-smi")
            return False
    except Exception as e:
        logger.warning(f"Помилка при перевірці GPU: {str(e)}")
        return False
