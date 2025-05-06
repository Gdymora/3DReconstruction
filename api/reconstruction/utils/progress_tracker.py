import os
import json
import time
import logging

class ProgressTracker:
    """
    Клас для відстеження прогресу реконструкції.
    """
    
    def __init__(self, metadata_path):
        """
        Ініціалізація трекера прогресу.
        
        Args:
            metadata_path (str): Шлях до файлу метаданих
        """
        self.metadata_path = metadata_path
        self.logger = logging.getLogger("progress_tracker")
    
    def update_progress(self, stage, progress, message=None):
        """
        Оновлює інформацію про прогрес реконструкції.
        
        Args:
            stage (str): Поточний етап реконструкції
            progress (int): Прогрес у відсотках (0-100)
            message (str, optional): Повідомлення про статус
        """
        try:
            if not os.path.exists(self.metadata_path):
                self.logger.warning(f"Файл метаданих не існує: {self.metadata_path}")
                # Створюємо новий файл метаданих
                with open(self.metadata_path, "w") as f:
                    json.dump({
                        "status": "processing",
                        "started_at": time.time(),
                        "current_stage": stage,
                        "progress": progress,
                        "current_message": message if message else ""
                    }, f)
                return
            
            # Зчитуємо існуючі метадані
            with open(self.metadata_path, "r") as f:
                metadata = json.load(f)
            
            # Оновлюємо прогрес
            metadata["current_stage"] = stage
            metadata["progress"] = progress
            if message:
                metadata["current_message"] = message
            
            # Зберігаємо оновлені метадані
            with open(self.metadata_path, "w") as f:
                json.dump(metadata, f)
                
            self.logger.info(f"Прогрес оновлено: {stage} - {progress}% - {message}")
        except Exception as e:
            self.logger.error(f"Помилка при оновленні прогресу: {str(e)}")
    
    def get_progress(self):
        """
        Отримує поточний прогрес реконструкції.
        
        Returns:
            dict: Інформація про прогрес
        """
        try:
            with open(self.metadata_path, "r") as f:
                metadata = json.load(f)
                
            # Вилучаємо інформацію про прогрес
            progress_info = {
                "current_stage": metadata.get("current_stage", "unknown"),
                "progress": metadata.get("progress", 0),
                "current_message": metadata.get("current_message", ""),
                "status": metadata.get("status", "unknown")
            }
            
            return progress_info
        except Exception as e:
            self.logger.error(f"Помилка при отриманні прогресу: {str(e)}")
            return {
                "current_stage": "unknown",
                "progress": 0,
                "current_message": f"Помилка: {str(e)}",
                "status": "error"
            }