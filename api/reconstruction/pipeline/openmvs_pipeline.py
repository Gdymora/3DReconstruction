import os
import shutil
import traceback
from .base_pipeline import BasePipeline
from ..utils.file_utils import run_command
from ..export.model_exporter import ModelExporter

class OpenMVSPipeline(BasePipeline):
    """
    Пайплайн реконструкції з використанням COLMAP та OpenMVS.
    """
    
    def run(self):
        """
        Запускає повний процес реконструкції з використанням COLMAP та OpenMVS.
        
        Returns:
            str: Шлях до згенерованої 3D-моделі
        """
        try:
            # Перевіряємо вхідні дані
            if not self.validate_input():
                raise ValueError("Невалідні вхідні дані")
                
            # Етап 1: Structure from Motion з COLMAP
            self.progress.update_progress("sfm", 10, "Запуск Structure from Motion з COLMAP")
            self.logger.info("Запуск Structure from Motion з COLMAP")
            
            from .colmap_pipeline import ColmapPipeline
            colmap = ColmapPipeline(
                self.input_dir, 
                self.output_dir, 
                self.temp_dir, 
                self.quality, 
                self.progress, 
                self.logger, 
                self.gpu_available
            )
            
            sparse_output = colmap._run_colmap_sfm()
            self.progress.update_progress("sfm", 30, "Structure from Motion завершено")
            
            # Етап 2: Конвертація результатів COLMAP у формат OpenMVS
            self.progress.update_progress("conversion", 35, "Конвертація в формат OpenMVS")
            self.logger.info("Конвертація результатів COLMAP у формат OpenMVS")
            
            # Створюємо директорію для роботи OpenMVS
            mvs_dir = os.path.join(self.temp_dir, "mvs")
            os.makedirs(mvs_dir, exist_ok=True)
            
            # Шлях до сцени OpenMVS
            scene_mvs = os.path.join(mvs_dir, "scene.mvs")
            
            sparse_model_dir = self._find_sparse_model_dir(sparse_output)
            self._convert_colmap_to_openmvs(sparse_model_dir, scene_mvs)
            self.progress.update_progress("conversion", 40, "Конвертація завершена")
            
            # Етап 3: Створення щільної хмари точок з OpenMVS
            self.progress.update_progress("pointcloud", 45, "Генерація щільної хмари точок")
            self.logger.info("Створення щільної хмари точок з OpenMVS")
            
            dense_cloud_file = os.path.join(mvs_dir, "scene_dense.mvs")
            self._run_densify_point_cloud(scene_mvs, dense_cloud_file)
            self.progress.update_progress("pointcloud", 60, "Хмару точок згенеровано")
            
            # Етап 4: Створення меша з OpenMVS
            self.progress.update_progress("mesh", 65, "Створення полігональної моделі")
            self.logger.info("Створення меша з OpenMVS")
            
            mesh_file = os.path.join(mvs_dir, "scene_dense_mesh.mvs")
            self._run_reconstruct_mesh(dense_cloud_file, mesh_file)
            self.progress.update_progress("mesh", 80, "Модель створено")
            
            # Етап 5: Текстурування меша з OpenMVS
            self.progress.update_progress("texture", 85, "Текстурування моделі")
            self.logger.info("Текстурування меша з OpenMVS")
            
            textured_mesh_file = os.path.join(mvs_dir, "scene_dense_mesh_texture.mvs")
            self._run_texture_mesh(mesh_file, textured_mesh_file)
            self.progress.update_progress("texture", 90, "Модель текстуровано")
            
            # Етап 6: Копіювання результатів та експорт моделі
            self.progress.update_progress("export", 95, "Експорт моделі в різні формати")
            self.logger.info("Копіювання результатів та експорт моделі")
            
            result_files = self._copy_results(mvs_dir, self.output_dir)
            self.progress.update_progress("export", 98, "Результати скопійовано")
            
            # Шлях до основного файлу моделі
            mesh_path = None
            for file_path in result_files:
                if file_path.endswith('.obj'):
                    mesh_path = file_path
                    break
                    
            if mesh_path is None and result_files:
                mesh_path = result_files[0]
                
            if mesh_path is None:
                raise RuntimeError("Не вдалося знайти вихідний файл моделі")
            
            # Експорт моделі в різні формати
            exporter = ModelExporter(self.output_dir, self.logger)
            exported_formats = exporter.export_model(mesh_path)
            
            self.progress.update_progress("export", 100, "Модель експортовано")
            self.logger.info(f"Модель експортовано в {len(exported_formats)} форматів")
            
            # Очищення тимчасових файлів
            self.cleanup()
            
            return mesh_path
            
        except Exception as e:
            self.logger.error(f"Помилка в OpenMVS пайплайні: {str(e)}")
            self.logger.error(traceback.format_exc())
            raise
    
    def _find_sparse_model_dir(self, sparse_output):
        """
        Знаходить директорію з розрідженою моделлю COLMAP.
        
        Args:
            sparse_output (str): Шлях до директорії з виходом COLMAP
            
        Returns:
            str: Шлях до директорії з моделлю
        """
        # Перевіряємо, чи є sparse/0 директорія (структура COLMAP)
        colmap_sparse_dir = os.path.join(sparse_output, "sparse", "0")
        if not os.path.exists(colmap_sparse_dir):
            colmap_sparse_dir = os.path.join(sparse_output, "sparse")
            if not os.path.exists(colmap_sparse_dir):
                colmap_sparse_dir = sparse_output
                if not os.path.exists(os.path.join(colmap_sparse_dir, "cameras.bin")) and not os.path.exists(os.path.join(colmap_sparse_dir, "cameras.txt")):
                    # Шукаємо директорію з моделлю
                    for root, dirs, files in os.walk(sparse_output):
                        if "cameras.bin" in files or "cameras.txt" in files:
                            colmap_sparse_dir = root
                            break
                    else:
                        raise FileNotFoundError(f"Не знайдено директорію з моделлю COLMAP в {sparse_output}")
        
        self.logger.info(f"Знайдено директорію з моделлю COLMAP: {colmap_sparse_dir}")
        return colmap_sparse_dir
    
    def _convert_colmap_to_openmvs(self, colmap_sparse_dir, scene_mvs):
        """
        Конвертує результати COLMAP у формат OpenMVS.
        
        Args:
            colmap_sparse_dir (str): Шлях до директорії з моделлю COLMAP
            scene_mvs (str): Шлях для збереження сцени OpenMVS
        """
        self.logger.info(f"Конвертація COLMAP у OpenMVS: {colmap_sparse_dir} -> {scene_mvs}")
        
        # Перевіряємо наявність необхідних файлів COLMAP
        has_bin_format = os.path.exists(os.path.join(colmap_sparse_dir, "cameras.bin"))
        has_txt_format = os.path.exists(os.path.join(colmap_sparse_dir, "cameras.txt"))
        
        if not (has_bin_format or has_txt_format):
            # Перевіряємо точно наявність необхідних файлів COLMAP
            self.logger.warning(f"Перевірка вмісту директорії COLMAP: {os.listdir(colmap_sparse_dir)}")
            raise FileNotFoundError("Не знайдено файли COLMAP (cameras.bin/txt)")
        
        # Використовуємо InterfaceCOLMAP з OpenMVS (якщо він встановлений)
        convert_cmd = f"xvfb-run.sh InterfaceCOLMAP --input-path {colmap_sparse_dir} --output-file {scene_mvs}"
        try:
            run_command(convert_cmd, logger=self.logger)
            self.logger.info("Конвертація через InterfaceCOLMAP успішна")
            return
        except Exception as e:
            self.logger.warning(f"Помилка при запуску InterfaceCOLMAP: {str(e)}")
            self.logger.warning("Спроба альтернативного методу конвертації...")
            
        # Альтернативний метод: використання утиліти COLMAP для експорту у формат NVM
        try:
            nvm_file = os.path.join(os.path.dirname(scene_mvs), "scene.nvm")
            colmap_export_cmd = f"xvfb-run.sh colmap model_converter --input_path {colmap_sparse_dir} --output_path {nvm_file} --output_type NVM"
            run_command(colmap_export_cmd, logger=self.logger)
            
            # Потім використання InterfaceVisualSFM з OpenMVS
            convert_cmd = f"xvfb-run.sh InterfaceVisualSFM --input-file {nvm_file} --output-file {scene_mvs}"
            run_command(convert_cmd, logger=self.logger)
            self.logger.info("Конвертація через NVM успішна")
            return
        except Exception as e:
            self.logger.warning(f"Помилка при альтернативній конвертації: {str(e)}")
            
        # Остання спроба: використання власного спрощеного конвертера
        self.logger.warning("Спроба використання спрощеного конвертера...")
        # Тут можна було б додати простий власний конвертер, але це виходить за рамки поточного завдання
        
        if not os.path.exists(scene_mvs):
            raise RuntimeError("Не вдалося конвертувати COLMAP у OpenMVS")
    
    def _run_densify_point_cloud(self, scene_mvs, dense_cloud_file):
        """
        Запускає DensifyPointCloud з OpenMVS для створення щільної хмари точок.
        
        Args:
            scene_mvs (str): Шлях до вхідної сцени OpenMVS
            dense_cloud_file (str): Шлях для збереження щільної хмари точок
        """
        # Параметри якості
        quality_params = {
            'low': '--resolution-level 2 --min-resolution 320',
            'medium': '--resolution-level 1 --min-resolution 640',
            'high': '--resolution-level 0 --min-resolution 1024 --max-resolution 3840'
        }
        
        params = quality_params.get(self.quality, quality_params['medium'])
        
        # Додаємо параметр для використання GPU, якщо доступно
        if self.gpu_available:
            params += " --cuda-device 0"
            
        densify_cmd = f"xvfb-run.sh DensifyPointCloud {scene_mvs} {params}"
        run_command(densify_cmd, logger=self.logger)
        
        # Перевіряємо наявність результату
        if not os.path.exists(dense_cloud_file):
            self.logger.warning(f"Файл {dense_cloud_file} не створено. Перевіряємо альтернативні шляхи...")
            
            # Шукаємо файли .mvs в директорії
            mvs_dir = os.path.dirname(scene_mvs)
            for file in os.listdir(mvs_dir):
                if file.endswith('.mvs') and 'dense' in file:
                    self.logger.info(f"Знайдено альтернативний файл: {file}")
                    # Копіюємо файл у бажане місце
                    shutil.copy2(os.path.join(mvs_dir, file), dense_cloud_file)
                    break
            else:
                raise FileNotFoundError(f"Не вдалося знайти щільну хмару точок після запуску DensifyPointCloud")
    
    def _run_reconstruct_mesh(self, dense_cloud_file, mesh_file):
        """
        Запускає ReconstructMesh з OpenMVS для створення меша.
        
        Args:
            dense_cloud_file (str): Шлях до файлу щільної хмари точок
            mesh_file (str): Шлях для збереження меша
        """
        # Параметри якості
        quality_params = {
            'low': '--min-face-angle 8 --smooth 3',
            'medium': '--min-face-angle 6 --smooth 2',
            'high': '--min-face-angle 4 --smooth 1 --thickness-factor 1.0'
        }
        
        params = quality_params.get(self.quality, quality_params['medium'])
        
        mesh_cmd = f"xvfb-run.sh ReconstructMesh {dense_cloud_file} {params}"
        run_command(mesh_cmd, logger=self.logger)
        
        # Перевіряємо наявність результату
        if not os.path.exists(mesh_file):
            self.logger.warning(f"Файл {mesh_file} не створено. Перевіряємо альтернативні шляхи...")
            
            # Шукаємо файли .mvs в директорії
            mvs_dir = os.path.dirname(dense_cloud_file)
            for file in os.listdir(mvs_dir):
                if file.endswith('.mvs') and 'mesh' in file:
                    self.logger.info(f"Знайдено альтернативний файл: {file}")
                    # Копіюємо файл у бажане місце
                    shutil.copy2(os.path.join(mvs_dir, file), mesh_file)
                    break
            else:
                raise FileNotFoundError(f"Не вдалося знайти меш після запуску ReconstructMesh")
    
    def _run_texture_mesh(self, mesh_file, textured_mesh_file):
        """
        Запускає TextureMesh з OpenMVS для текстурування меша.
        
        Args:
            mesh_file (str): Шлях до файлу меша
            textured_mesh_file (str): Шлях для збереження текстурованого меша
        """
        # Параметри якості
        quality_params = {
            'low': '--resolution-level 2',
            'medium': '--resolution-level 1',
            'high': '--resolution-level 0 --export-texture-type png'
        }
        
        params = quality_params.get(self.quality, quality_params['medium'])
        
        texture_cmd = f"xvfb-run.sh TextureMesh {mesh_file} {params}"
        run_command(texture_cmd, logger=self.logger)
        
        # Перевіряємо наявність результату
        if not os.path.exists(textured_mesh_file):
            self.logger.warning(f"Файл {textured_mesh_file} не створено. Перевіряємо альтернативні шляхи...")
            
            # Шукаємо файли .mvs в директорії
            mvs_dir = os.path.dirname(mesh_file)
            for file in os.listdir(mvs_dir):
                if file.endswith('.mvs') and 'texture' in file:
                    self.logger.info(f"Знайдено альтернативний файл: {file}")
                    # Копіюємо файл у бажане місце
                    shutil.copy2(os.path.join(mvs_dir, file), textured_mesh_file)
                    break
            else:
                self.logger.warning(f"Не вдалося знайти текстурований меш після запуску TextureMesh")
                # Повертаємо шлях до нетекстурованого меша як fallback
                textured_mesh_file = mesh_file
    
    def _copy_results(self, mvs_dir, output_dir):
        """
        Копіює результати з директорії OpenMVS в директорію результатів.
        
        Args:
            mvs_dir (str): Директорія з результатами OpenMVS
            output_dir (str): Директорія для результатів
            
        Returns:
            list: Список шляхів до скопійованих файлів
        """
        result_files = []
        
        # Шукаємо результуючі файли
        for ext in ['.obj', '.ply', '.gltf', '.glb']:
            for file in os.listdir(mvs_dir):
                if file.endswith(ext):
                    src_path = os.path.join(mvs_dir, file)
                    dst_path = os.path.join(output_dir, file)
                    shutil.copy2(src_path, dst_path)
                    result_files.append(dst_path)
                    self.logger.info(f"Скопійовано файл результату: {dst_path}")
        
        # Якщо немає .obj файлів, конвертуємо .mvs в .obj
        if not any(f.endswith('.obj') for f in result_files):
            self.logger.info("Не знайдено .obj файлів, спроба конвертації .mvs")
            
            # Шукаємо текстурований .mvs файл
            for file in os.listdir(mvs_dir):
                if file.endswith('.mvs') and 'texture' in file:
                    src_path = os.path.join(mvs_dir, file)
                    dst_path = os.path.join(output_dir, "model.obj")
                    
                    # Запускаємо конвертацію
                    try:
                        convert_cmd = f"xvfb-run.sh TextureMesh {src_path} --export-type obj"
                        run_command(convert_cmd, logger=self.logger)
                        
                        # Шукаємо .obj файл в директорії mvs_dir
                        for obj_file in os.listdir(mvs_dir):
                            if obj_file.endswith('.obj'):
                                obj_src_path = os.path.join(mvs_dir, obj_file)
                                if os.path.exists(obj_src_path):
                                    shutil.copy2(obj_src_path, dst_path)
                                    result_files.append(dst_path)
                                    self.logger.info(f"Скопійовано конвертований .obj файл: {dst_path}")
                                    break
                                    
                    except Exception as e:
                        self.logger.warning(f"Не вдалося конвертувати .mvs в .obj: {str(e)}")
                    
                    break
        
        return result_files