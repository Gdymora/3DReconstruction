import os
import subprocess
import traceback
from .base_pipeline import BasePipeline
from ..processing.point_cloud import PointCloudProcessor
from ..processing.mesh import MeshProcessor
from ..processing.texture import TextureProcessor
from ..export.model_exporter import ModelExporter
from ..utils.file_utils import run_command

class ColmapPipeline(BasePipeline):
    """
    Пайплайн реконструкції з використанням COLMAP.
    """
    
    def run(self):
        """
        Запускає повний процес реконструкції з використанням COLMAP.
        
        Returns:
            str: Шлях до згенерованої 3D-моделі
        """
        try:
            # Перевіряємо вхідні дані
            if not self.validate_input():
                raise ValueError("Невалідні вхідні дані")
                
            # Етап 1: Structure from Motion з COLMAP
            self.progress.update_progress("sfm", 10, "Запуск Structure from Motion")
            self.logger.info("Запуск Structure from Motion з COLMAP")
            
            sparse_output = self._run_colmap_sfm()
            self.progress.update_progress("sfm", 30, "Structure from Motion завершено")
            
            # Етап 2: Генерація щільної хмари точок
            self.progress.update_progress("pointcloud", 35, "Генерація щільної хмари точок")
            self.logger.info("Генерація щільної хмари точок")
            
            point_cloud_processor = PointCloudProcessor(
                self.sparse_dir, 
                self.dense_dir, 
                self.quality, 
                self.logger, 
                self.gpu_available
            )
            
            if self.quality == 'high':
                point_cloud_path = point_cloud_processor.generate_multiscale()
            else:
                point_cloud_path = point_cloud_processor.generate()
                
            self.progress.update_progress("pointcloud", 50, "Хмару точок згенеровано")
            
            # Етап 3: Створення меша з хмари точок
            self.progress.update_progress("mesh", 55, "Створення полігональної моделі")
            self.logger.info("Створення меша з хмари точок")
            
            mesh_processor = MeshProcessor(self.output_dir, self.logger)
            mesh_path = mesh_processor.create_mesh(point_cloud_path, self.quality)
            self.progress.update_progress("mesh", 70, "Модель створено")
            
            # Етап 4: Очищення меша
            self.progress.update_progress("clean", 75, "Очищення моделі")
            self.logger.info("Очищення меша від шуму та аномалій")
            
            mesh_path = mesh_processor.clean_mesh(mesh_path)
            self.progress.update_progress("clean", 80, "Модель очищено")
            
            # Етап 5: Текстурування меша
            self.progress.update_progress("texture", 85, "Текстурування моделі")
            self.logger.info("Текстурування меша")
            
            texture_processor = TextureProcessor(self.input_dir, self.output_dir, self.logger)
            textured_mesh_path = texture_processor.enhance_texture(mesh_path, self.quality)
            self.progress.update_progress("texture", 90, "Модель текстуровано")
            
            # Етап 6: Експорт моделі в різні формати
            self.progress.update_progress("export", 95, "Експорт моделі в різні формати")
            self.logger.info("Експорт моделі в різні формати")
            
            exporter = ModelExporter(self.output_dir, self.logger)
            exported_formats = exporter.export_model(textured_mesh_path)
            
            self.progress.update_progress("export", 100, "Модель експортовано")
            self.logger.info(f"Модель експортовано в {len(exported_formats)} форматів")
            
            # Очищення тимчасових файлів
            self.cleanup()
            
            return textured_mesh_path
            
        except Exception as e:
            self.logger.error(f"Помилка в COLMAP пайплайні: {str(e)}")
            self.logger.error(traceback.format_exc())
            raise
    
    def _run_colmap_sfm(self):
        """
        Запускає COLMAP для Structure from Motion.
        
        Returns:
            str: Шлях до директорії з sparse reconstruction
        """
        self.logger.info("Запуск COLMAP SfM")
        
        # Параметри якості для COLMAP
        quality_params = {
            'low': {
                'sift_extraction': f'--SiftExtraction.max_num_features 4096 --SiftExtraction.use_gpu 1 --SiftExtraction.estimate_affine_shape 0',
                'matcher': f'--SiftMatching.max_num_matches 8192 --SiftMatching.use_gpu 1 --SiftMatching.guided_matching 0',
                'mapper': '--Mapper.min_num_matches 15 --Mapper.max_reg_trials 2'
            },
            'medium': {
                'sift_extraction': f'--SiftExtraction.max_num_features 8192 --SiftExtraction.use_gpu 1 --SiftExtraction.estimate_affine_shape 1',
                'matcher': f'--SiftMatching.max_num_matches 16384 --SiftMatching.use_gpu 1 --SiftMatching.guided_matching 1',
                'mapper': '--Mapper.min_num_matches 30 --Mapper.max_reg_trials 3'
            },
            'high': {
                'sift_extraction': f'--SiftExtraction.max_num_features 16384 --SiftExtraction.use_gpu 1 --SiftExtraction.estimate_affine_shape 1',
                'matcher': f'--SiftMatching.max_num_matches 32768 --SiftMatching.use_gpu 1 --SiftMatching.guided_matching 1',
                'mapper': '--Mapper.min_num_matches 50 --Mapper.max_reg_trials 4'
            }
        }
        
        # Додаткові параметри для підвищення стабільності
        robust_params = (
            f"--Mapper.ba_global_function_tolerance=0.000001 "
            f"--Mapper.ba_global_max_num_iterations=500 "
            f"--Mapper.filter_max_reproj_error=4.0 "
        )
        
        params = quality_params.get(self.quality, quality_params['medium'])
        
        db_path = os.path.join(self.sparse_dir, "database.db")
        sparse_model_path = os.path.join(self.sparse_dir, "sparse")
        os.makedirs(sparse_model_path, exist_ok=True)
        
        # Налаштовуємо середовище для роботи в headless режимі
        env = os.environ.copy()
        env['QT_QPA_PLATFORM'] = 'offscreen'
        env['DISPLAY'] = ':99'
        
        # 1. Feature extraction
        self.logger.info("Запуск feature extraction")
        self.progress.update_progress("sfm", 15, "Виявлення ключових точок на зображеннях")
        
        feature_extractor_cmd = (
            f"xvfb-run.sh colmap feature_extractor "
            f"--database_path {db_path} "
            f"--image_path {self.input_dir} "
            f"{params['sift_extraction']} "
            f"--ImageReader.single_camera 1 "
            f"--ImageReader.camera_model PINHOLE"
        )
        
        run_command(feature_extractor_cmd, env=env, logger=self.logger)
        self.logger.info("Feature extraction завершено")
        
        # 2. Feature matching
        self.logger.info("Запуск feature matching")
        self.progress.update_progress("sfm", 20, "Зіставлення ключових точок")
        
        matcher_cmd = (
            f"xvfb-run.sh colmap exhaustive_matcher "
            f"--database_path {db_path} "
            f"{params['matcher']}"
        )
        
        run_command(matcher_cmd, env=env, logger=self.logger)
        self.logger.info("Feature matching завершено")
        
        # 3. Structure from Motion
        self.logger.info("Запуск mapper (sparse reconstruction)")
        self.progress.update_progress("sfm", 25, "Реконструкція камер і структури сцени")
        
        mapper_cmd = (
            f"xvfb-run.sh colmap mapper "
            f"--database_path {db_path} "
            f"--image_path {self.input_dir} "
            f"--output_path {sparse_model_path} "
            f"{params['mapper']} "
            f"{robust_params}"
        )
        
        run_command(mapper_cmd, env=env, logger=self.logger)
        self.logger.info("Sparse reconstruction завершено")
        
        # Перевіряємо наявність результатів
        model_dir = os.path.join(sparse_model_path, '0')
        if not os.path.exists(model_dir):
            subdirs = [d for d in os.listdir(sparse_model_path) 
                      if os.path.isdir(os.path.join(sparse_model_path, d))]
            if subdirs:
                model_dir = os.path.join(sparse_model_path, subdirs[0])
                self.logger.info(f"Знайдено альтернативну директорію моделі: {model_dir}")
            else:
                self.logger.error(f"Не знайдено директорії з моделлю в {sparse_model_path}")
                raise FileNotFoundError(f"No model directory found in {sparse_model_path}")
        
        return sparse_model_path