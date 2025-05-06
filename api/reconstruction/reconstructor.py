import os
import time
import json
from .utils.logging_utils import setup_logger
from .utils.gpu_utils import check_gpu_availability
from .utils.progress_tracker import ProgressTracker
from .pipeline.colmap_pipeline import ColmapPipeline
from .pipeline.openmvs_pipeline import OpenMVSPipeline
from .pipeline.custom_pipeline import CustomPipeline

class Reconstructor:
    """
    Основний клас для керування процесом 3D-реконструкції.
    Ініціалізує потрібний пайплайн та відслідковує прогрес.
    """
    
    def __init__(self, session_id, input_dir, output_dir):
        """
        Ініціалізація реконструктора.
        
        Args:
            session_id (str): Унікальний ідентифікатор сесії
            input_dir (str): Директорія з вхідними зображеннями
            output_dir (str): Директорія для результатів
        """
        self.session_id = session_id
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.temp_dir = os.path.join(output_dir, "temp")
        self.metadata_path = os.path.join(output_dir, "metadata.json")
        
        # Створюємо директорії, якщо вони не існують
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Ініціалізуємо логер
        self.logger = setup_logger(output_dir, "reconstructor")
        self.logger.info(f"Ініціалізовано реконструктор для сесії {session_id}")
        
        # Ініціалізуємо трекер прогресу
        self.progress = ProgressTracker(self.metadata_path)
        
        # Перевіряємо доступність GPU
        self.gpu_available = check_gpu_availability()
        self.logger.info(f"GPU доступність: {'Так' if self.gpu_available else 'Ні'}")
    
    def run_reconstruction(self, method='colmap', quality='medium'):
        """
        Запускає процес реконструкції з вибраним методом та якістю.
        
        Args:
            method (str): Метод реконструкції ('colmap', 'openmvs', 'custom')
            quality (str): Якість реконструкції ('low', 'medium', 'high')
            
        Returns:
            str: Шлях до згенерованої 3D-моделі
        """
        self.logger.info(f"Запуск реконструкції з методом {method}, якість {quality}")
        self.progress.update_progress("initialization", 0, "Ініціалізація процесу")
        
        # Вибір відповідного пайплайну
        pipeline = self._get_pipeline(method, quality)
        
        try:
            # Оновлюємо метадані - процес розпочато
            self._update_metadata({
                "status": "processing",
                "started_at": time.time(),
                "quality": quality,
                "method": method,
            })
            
            # Запускаємо процес реконструкції
            result_path = pipeline.run()
            
            # Оновлюємо метадані - процес завершено успішно
            self._update_metadata({
                "status": "completed",
                "completed_at": time.time(),
                "output_path": result_path,
            })
            
            self.progress.update_progress("complete", 100, "Реконструкція завершена")
            self.logger.info(f"Реконструкція завершена успішно: {result_path}")
            
            return result_path
            
        except Exception as e:
            self.logger.error(f"Помилка під час реконструкції: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            
            # Оновлюємо метадані - процес завершено з помилкою
            self._update_metadata({
                "status": "failed",
                "error": str(e),
                "completed_at": time.time(),
            })
            
            self.progress.update_progress("error", 0, f"Помилка: {str(e)}")
            raise
            
    def _get_pipeline(self, method, quality):
        """
        Створює відповідний об'єкт пайплайну.
        
        Args:
            method (str): Метод реконструкції
            quality (str): Якість реконструкції
            
        Returns:
            BasePipeline: Об'єкт пайплайну
        """
        if method == 'colmap':
            return ColmapPipeline(
                self.input_dir, 
                self.output_dir, 
                self.temp_dir, 
                quality, 
                self.progress, 
                self.logger, 
                self.gpu_available
            )
        elif method == 'openmvs':
            return OpenMVSPipeline(
                self.input_dir, 
                self.output_dir, 
                self.temp_dir, 
                quality, 
                self.progress, 
                self.logger, 
                self.gpu_available
            )
        elif method == 'custom':
            return CustomPipeline(
                self.input_dir, 
                self.output_dir, 
                self.temp_dir, 
                quality, 
                self.progress, 
                self.logger, 
                self.gpu_available
            )
        else:
            raise ValueError(f"Невідомий метод реконструкції: {method}")
            
    def _update_metadata(self, data):
        """
        Оновлює метадані сесії.
        
        Args:
            data (dict): Дані для оновлення
        """
        try:
            with open(self.metadata_path, "r") as f:
                metadata = json.load(f)
                
            # Оновлюємо дані
            metadata.update(data)
            
            # Зберігаємо оновлені метадані
            with open(self.metadata_path, "w") as f:
                json.dump(metadata, f)
                
        except Exception as e:
            self.logger.error(f"Помилка при оновленні метаданих: {str(e)}")