from abc import ABC, abstractmethod
import os
import shutil

class BasePipeline(ABC):
    """
    Базовий абстрактний клас для пайплайнів реконструкції.
    Всі конкретні пайплайни повинні успадковуватись від нього.
    """
    
    def __init__(self, input_dir, output_dir, temp_dir, quality, progress_tracker, logger, gpu_available):
        """
        Ініціалізація базового пайплайну.
        
        Args:
            input_dir (str): Директорія з вхідними зображеннями
            output_dir (str): Директорія для результатів
            temp_dir (str): Директорія для тимчасових файлів
            quality (str): Якість реконструкції ('low', 'medium', 'high')
            progress_tracker (ProgressTracker): Об'єкт для відстеження прогресу
            logger (Logger): Об'єкт для логування
            gpu_available (bool): Чи доступне GPU
        """
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.temp_dir = temp_dir
        self.quality = quality
        self.progress = progress_tracker
        self.logger = logger
        self.gpu_available = gpu_available
        
        # Створюємо директорії для етапів реконструкції
        self.sparse_dir = os.path.join(temp_dir, "sparse")
        self.dense_dir = os.path.join(temp_dir, "dense")
        
        os.makedirs(self.sparse_dir, exist_ok=True)
        os.makedirs(self.dense_dir, exist_ok=True)
        
        self.logger.info(f"Ініціалізовано базовий пайплайн з якістю {quality}")
        self.logger.info(f"GPU доступність: {'Так' if gpu_available else 'Ні'}")
    
    @abstractmethod
    def run(self):
        """
        Запускає повний процес реконструкції.
        Повинен бути реалізований в похідних класах.
        
        Returns:
            str: Шлях до згенерованої 3D-моделі
        """
        pass
    
    def cleanup(self):
        """
        Очищає тимчасові файли після завершення реконструкції.
        """
        try:
            if self.quality != 'debug':  # В режимі debug не видаляємо файли
                self.logger.info("Видалення тимчасових файлів")
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            self.logger.warning(f"Не вдалося видалити тимчасові файли: {str(e)}")
            
    def validate_input(self):
        """
        Перевіряє наявність та валідність вхідних даних.
        
        Returns:
            bool: True, якщо дані валідні, інакше False
        """
        # Перевіряємо директорію з зображеннями
        if not os.path.exists(self.input_dir):
            self.logger.error(f"Директорія з вхідними зображеннями не існує: {self.input_dir}")
            return False
            
        # Рахуємо кількість зображень
        image_files = [f for f in os.listdir(self.input_dir) 
                      if f.lower().endswith(('.jpg', '.jpeg', '.png', '.tif', '.tiff'))]
                      
        if len(image_files) < 3:
            self.logger.error(f"Недостатньо зображень для реконструкції. Знайдено: {len(image_files)}, потрібно мінімум 3")
            return False
            
        self.logger.info(f"Вхідні дані валідні. Знайдено {len(image_files)} зображень")
        return True