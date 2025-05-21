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
        Запускає COLMAP для Structure from Motion з детальним логуванням.
        
        Returns:
            str: Шлях до директорії з sparse reconstruction
        """
        self.logger.info("Запуск COLMAP SfM пайплайну")
        
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
        
        # Додаємо лічильник для моніторингу прогресу
        progress_counter = {
            'feature_extraction': {'total': 0, 'current': 0, 'features': 0},
            'feature_matching': {'total': 0, 'current': 0, 'matches': 0},
            'mapping': {'total': 0, 'current': 0, 'points': 0}
        }
        
        # Функція для обробки вихідних даних COLMAP
        def process_output(line, stage):
            if stage == 'feature_extraction':
                # Пошук рядків про кількість зображень або ключові точки
                if 'processed' in line and 'images' in line:
                    try:
                        parts = line.split()
                        current = int(parts[1])
                        total = int(parts[3])
                        progress_counter['feature_extraction']['current'] = current
                        progress_counter['feature_extraction']['total'] = total
                        percent = min(15, 5 + (current * 10) // total)
                        self.progress.update_progress("sfm", percent, f"Обробка зображень: {current}/{total}")
                        self.logger.info(f"Прогрес виділення ключових точок: {current}/{total} зображень")
                    except Exception as e:
                        self.logger.error(f"Помилка при аналізі прогресу: {str(e)}")
                
                if 'Features:' in line:
                    try:
                        features_count = int(line.split(':')[1].strip())
                        progress_counter['feature_extraction']['features'] = features_count
                        self.logger.info(f"Виявлено ключових точок: {features_count}")
                    except Exception:
                        pass
            
            elif stage == 'feature_matching':
                # Пошук рядків про прогрес зіставлення
                if 'Matching block' in line:
                    try:
                        # Формат: Matching block [1/10, 2/10] in 0.123s
                        block_info = line.split('[')[1].split(']')[0]
                        current_block, total_blocks = block_info.split(',')[0].strip().split('/')
                        current_block = int(current_block)
                        total_blocks = int(total_blocks)
                        
                        progress_counter['feature_matching']['current'] = current_block
                        progress_counter['feature_matching']['total'] = total_blocks
                        
                        # Розрахунок відсотка прогресу для етапу зіставлення (від 15% до 30%)
                        percent = min(30, 15 + (current_block * 15) // total_blocks)
                        self.progress.update_progress("sfm", percent, 
                                                    f"Зіставлення ключових точок: блок {current_block}/{total_blocks}")
                        self.logger.info(f"Прогрес зіставлення: блок {current_block}/{total_blocks}")
                    except Exception as e:
                        self.logger.error(f"Помилка при аналізі прогресу зіставлення: {str(e)}")
                
                if 'Matches:' in line:
                    try:
                        matches_count = int(line.split(':')[1].strip())
                        progress_counter['feature_matching']['matches'] = matches_count
                        self.logger.info(f"Знайдено зіставлень: {matches_count}")
                    except Exception:
                        pass
            
            elif stage == 'mapping':
                # Пошук рядків про реєстрацію зображень
                if 'Registering image' in line:
                    try:
                        # Parsing "Registering image #X"
                        current_img = int(line.split('#')[1].split()[0])
                        if progress_counter['mapping']['total'] == 0:
                            # Це перше зображення, оцінимо загальну кількість з feature_extraction
                            progress_counter['mapping']['total'] = progress_counter['feature_extraction']['total']
                        
                        progress_counter['mapping']['current'] = current_img
                        
                        # Розрахунок відсотка для етапу mapping (від 30% до 50%)
                        percent = min(50, 30 + (current_img * 20) // progress_counter['mapping']['total'])
                        self.progress.update_progress("sfm", percent, 
                                                    f"Реконструкція камер: {current_img}/{progress_counter['mapping']['total']}")
                        self.logger.info(f"Прогрес реконструкції: зображення {current_img}/{progress_counter['mapping']['total']}")
                    except Exception as e:
                        self.logger.error(f"Помилка при аналізі прогресу реконструкції: {str(e)}")
                
                if 'points_count' in line:
                    try:
                        points_count = int(line.split(':')[1].strip())
                        progress_counter['mapping']['points'] = points_count
                        self.logger.info(f"Реконструйовано 3D точок: {points_count}")
                    except Exception:
                        pass
        
        # Функція для запуску команди з обробкою виводу в реальному часі
        def custom_run_command(command, stage, env=None, timeout=3600):  # 1 година максимум
            """Запускає команду з обробкою виводу в реальному часі"""
            self.logger.info(f"Виконання команди для етапу {stage}: {command}")
            
            try:
                process = subprocess.Popen(
                    command, 
                    shell=True, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    universal_newlines=True,
                    bufsize=1,  # Буферизація порядкова
                    env=env
                )
                
                # Читаємо вивід у режимі реального часу
                for line in process.stdout:
                    line = line.strip()
                    if line:
                        self.logger.info(f"STDOUT: {line}")
                        process_output(line, stage)
                
                # Читаємо помилки у режимі реального часу
                for line in process.stderr:
                    line = line.strip()
                    if line:
                        self.logger.warning(f"STDERR: {line}")
                
                # Чекаємо завершення процесу з таймаутом
                try:
                    return_code = process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    process.kill()
                    self.logger.error(f"Команда перервана через перевищення таймауту ({timeout}с): {command}")
                    raise RuntimeError(f"Команда перервана через таймаут: {command}")
                
                if return_code != 0:
                    self.logger.error(f"Команда завершилася з кодом {return_code}")
                    raise RuntimeError(f"Помилка виконання команди: {command}")
                    
                self.logger.info(f"Команда для етапу {stage} виконана успішно")
                # Виводимо підсумкову статистику етапу
                if stage == 'feature_extraction':
                    self.logger.info(f"Підсумок етапу Feature Extraction:")
                    self.logger.info(f"  Оброблено зображень: {progress_counter['feature_extraction']['current']}/{progress_counter['feature_extraction']['total']}")
                    self.logger.info(f"  Знайдено ключових точок: {progress_counter['feature_extraction']['features']}")
                elif stage == 'feature_matching':
                    self.logger.info(f"Підсумок етапу Feature Matching:")
                    self.logger.info(f"  Оброблено блоків: {progress_counter['feature_matching']['current']}/{progress_counter['feature_matching']['total']}")
                    self.logger.info(f"  Знайдено зіставлень: {progress_counter['feature_matching']['matches']}")
                elif stage == 'mapping':
                    self.logger.info(f"Підсумок етапу Mapping:")
                    self.logger.info(f"  Реконструйовано зображень: {progress_counter['mapping']['current']}/{progress_counter['mapping']['total']}")
                    self.logger.info(f"  Створено 3D точок: {progress_counter['mapping']['points']}")
                
                return ""
            except Exception as e:
                self.logger.error(f"Помилка при виконанні команди: {str(e)}")
                raise
        
        # 1. Feature extraction з детальним логуванням
        self.logger.info("Запуск feature extraction")
        self.progress.update_progress("sfm", 5, "Виявлення ключових точок на зображеннях")
        
        feature_extractor_cmd = (
            f"xvfb-run.sh colmap feature_extractor "
            f"--database_path {db_path} "
            f"--image_path {self.input_dir} "
            f"{params['sift_extraction']} "
            f"--ImageReader.single_camera 1 "
            f"--ImageReader.camera_model PINHOLE"
        )
        
        try:
            custom_run_command(feature_extractor_cmd, "feature_extraction", env=env)
            self.logger.info("Feature extraction завершено")
        except Exception as e:
            self.logger.error(f"Помилка при feature extraction: {str(e)}")
            self.logger.error(traceback.format_exc())
            raise
        
        # 2. Feature matching з детальним логуванням
        self.logger.info("Запуск feature matching")
        self.progress.update_progress("sfm", 15, "Зіставлення ключових точок")
        
        matcher_cmd = (
            f"xvfb-run.sh colmap exhaustive_matcher "
            f"--database_path {db_path} "
            f"{params['matcher']}"
        )
        
        try:
            custom_run_command(matcher_cmd, "feature_matching", env=env)
            self.logger.info("Feature matching завершено")
        except Exception as e:
            self.logger.error(f"Помилка при feature matching: {str(e)}")
            self.logger.error(traceback.format_exc())
            raise
        
        # 3. Structure from Motion з детальним логуванням
        self.logger.info("Запуск mapper (sparse reconstruction)")
        self.progress.update_progress("sfm", 30, "Реконструкція камер і структури сцени")
        
        mapper_cmd = (
            f"xvfb-run.sh colmap mapper "
            f"--database_path {db_path} "
            f"--image_path {self.input_dir} "
            f"--output_path {sparse_model_path} "
            f"{params['mapper']} "
            f"{robust_params}"
        )
        
        try:
            custom_run_command(mapper_cmd, "mapping", env=env)
            self.logger.info("Sparse reconstruction завершено")
        except Exception as e:
            self.logger.error(f"Помилка при sparse reconstruction: {str(e)}")
            self.logger.error(traceback.format_exc())
            raise
        
        # 4. Перевірка наявності результатів
        self.logger.info("Перевірка результатів реконструкції")
        model_dir = os.path.join(sparse_model_path, '0')
        if not os.path.exists(model_dir):
            subdirs = [d for d in os.listdir(sparse_model_path) 
                      if os.path.isdir(os.path.join(sparse_model_path, d))]
            if subdirs:
                model_dir = os.path.join(sparse_model_path, subdirs[0])
                self.logger.info(f"Знайдено альтернативну директорію моделі: {model_dir}")
            else:
                self.logger.error(f"Не знайдено директорії з моделлю в {sparse_model_path}")
                files = os.listdir(sparse_model_path)
                self.logger.info(f"Файли в директорії: {files}")
                raise FileNotFoundError(f"Директорія з моделлю не знайдена в {sparse_model_path}")
        
        # Виводимо підсумкову статистику
        self.logger.info(f"Structure from Motion завершено успішно:")
        self.logger.info(f"  Загальна кількість ключових точок: {progress_counter['feature_extraction']['features']}")
        self.logger.info(f"  Загальна кількість зіставлень: {progress_counter['feature_matching']['matches']}")
        self.logger.info(f"  Реконструйовано зображень: {progress_counter['mapping']['current']}/{progress_counter['mapping']['total']}")
        self.logger.info(f"  Створено 3D точок: {progress_counter['mapping']['points']}")
        
        return sparse_model_path