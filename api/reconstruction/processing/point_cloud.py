import os
import numpy as np
import open3d as o3d

class PointCloudProcessor:
    """
    Клас для обробки та генерації хмар точок.
    """
    
    def __init__(self, sparse_dir, dense_dir, quality, logger, gpu_available):
        """
        Ініціалізація процесора хмари точок.
        
        Args:
            sparse_dir (str): Директорія з розрідженою реконструкцією
            dense_dir (str): Директорія для щільної хмари точок
            quality (str): Якість реконструкції ('low', 'medium', 'high')
            logger: Об'єкт для логування
            gpu_available (bool): Чи доступне GPU
        """
        self.sparse_dir = sparse_dir
        self.dense_dir = dense_dir
        self.quality = quality
        self.logger = logger
        self.gpu_available = gpu_available
        
        # Параметри якості для різних етапів
        self.quality_params = {
            'low': {'max_image_size': 1000, 'window_radius': 3, 'filter': 1},
            'medium': {'max_image_size': 1600, 'window_radius': 5, 'filter': 1},
            'high': {'max_image_size': 2400, 'window_radius': 7, 'filter': 1, 'geom_consistency': 1}
        }
    
    def generate(self):
        """
        Генерує щільну хмару точок з розрідженої реконструкції.
        
        Returns:
            str: Шлях до згенерованої хмари точок
        """
        self.logger.info("Генерація щільної хмари точок")
        
        sparse_model_dir = self._find_sparse_model_dir()
        params = self.quality_params.get(self.quality, self.quality_params['medium'])
        
        # 1. Undistort images
        self.logger.info("Undistorting images")
        undistorter_cmd = (
            f"colmap image_undistorter "
            f"--image_path {os.path.dirname(self.sparse_dir)} "
            f"--input_path {sparse_model_dir} "
            f"--output_path {self.dense_dir} "
            f"--output_type COLMAP"
        )
        self._run_command(undistorter_cmd)
        
        # 2. Compute stereo depth maps
        self.logger.info("Computing stereo depth maps")
        stereo_cmd = (
            f"colmap patch_match_stereo "
            f"--workspace_path {self.dense_dir} "
            f"--PatchMatchStereo.max_image_size {params['max_image_size']} "
            f"--PatchMatchStereo.window_radius {params['window_radius']} "
            f"--PatchMatchStereo.filter {params['filter']} "
        )
        
        if self.quality == 'high':
            stereo_cmd += f"--PatchMatchStereo.geom_consistency {params['geom_consistency']} "
            
        if self.gpu_available:
            stereo_cmd += "--PatchMatchStereo.gpu_index 0 "
            
        self._run_command(stereo_cmd)
        
        # 3. Fuse depth maps into a point cloud
        self.logger.info("Fusing depth maps into a point cloud")
        fusion_cmd = (
            f"colmap stereo_fusion "
            f"--workspace_path {self.dense_dir} "
            f"--input_type geometric "
            f"--output_path {os.path.join(self.dense_dir, 'fused.ply')}"
        )
        self._run_command(fusion_cmd)
        
        # Verify the point cloud exists
        point_cloud_path = os.path.join(self.dense_dir, "fused.ply")
        if not os.path.exists(point_cloud_path):
            raise RuntimeError("Dense point cloud generation failed")
            
        self.logger.info(f"Хмару точок згенеровано: {point_cloud_path}")
        
        return point_cloud_path
    
    def generate_multiscale(self):
        """
        Генерує мультимасштабну хмару точок для кращої деталізації.
        
        Returns:
            str: Шлях до згенерованої хмари точок
        """
        self.logger.info("Генерація мультимасштабної хмари точок")
        
        # Основна хмара точок
        point_cloud_path = self.generate()
        
        if self.quality == 'high':
            # Різні параметри розміру патчів для кращої деталізації
            patch_sizes = [11, 7]
            detail_clouds = []
            
            for idx, patch_size in enumerate(patch_sizes):
                try:
                    self.logger.info(f"Запуск додаткового проходу з розміром патча {patch_size}")
                    
                    # Окрема директорія для кожної ітерації
                    detail_dir = os.path.join(self.dense_dir, f"detail_{idx}")
                    os.makedirs(detail_dir, exist_ok=True)
                    
                    # Копіюємо необхідні файли з основної щільної реконструкції
                    self._copy_dense_files(self.dense_dir, detail_dir)
                    
                    # Модифікуємо команду stereo matching
                    stereo_cmd = (
                        f"colmap patch_match_stereo "
                        f"--workspace_path {detail_dir} "
                        f"--PatchMatchStereo.window_radius {patch_size} "
                        f"--PatchMatchStereo.min_triangulation_angle 3.0 "
                        f"--PatchMatchStereo.filter 1 "
                        f"--PatchMatchStereo.geom_consistency 1 "
                        f"--PatchMatchStereo.max_image_size 2000"
                    )
                    
                    if self.gpu_available:
                        stereo_cmd += " --PatchMatchStereo.gpu_index 0"
                        
                    self._run_command(stereo_cmd)
                    
                    # Окремий файл для виходу
                    detail_pc_path = os.path.join(detail_dir, f"fused_detail_{idx}.ply")
                    
                    # Запускаємо fusion з більш детальними налаштуваннями
                    fusion_cmd = (
                        f"colmap stereo_fusion "
                        f"--workspace_path {detail_dir} "
                        f"--input_type geometric "
                        f"--output_path {detail_pc_path} "
                        f"--StereoFusion.min_num_pixels 3 "
                        f"--StereoFusion.max_normal_error 10 "
                    )
                    self._run_command(fusion_cmd)
                    
                    # Додаємо до списку для подальшого об'єднання
                    if os.path.exists(detail_pc_path):
                        detail_clouds.append(detail_pc_path)
                        self.logger.info(f"Створено детальну хмару точок: {detail_pc_path}")
                    
                except Exception as e:
                    self.logger.warning(f"Не вдалося створити додатковий рівень деталізації {idx}: {str(e)}")
            
            # Об'єднуємо всі хмари точок
            if detail_clouds:
                combined_path = self._combine_point_clouds(point_cloud_path, detail_clouds)
                self.logger.info(f"Створено об'єднану хмару точок: {combined_path}")
                return combined_path
        
        return point_cloud_path
    
    def _combine_point_clouds(self, main_cloud_path, detail_clouds):
        """
        Об'єднує основну хмару точок з детальними.
        
        Args:
            main_cloud_path (str): Шлях до основної хмари точок
            detail_clouds (list): Список шляхів до детальних хмар точок
            
        Returns:
            str: Шлях до об'єднаної хмари точок
        """
        self.logger.info("Об'єднання хмар точок")
        
        try:
            # Завантажуємо основну хмару точок
            main_pcd = o3d.io.read_point_cloud(main_cloud_path)
            combined_points = np.asarray(main_pcd.points)
            combined_colors = np.asarray(main_pcd.colors)
            
            # Додаємо точки з детальних хмар
            for cloud_path in detail_clouds:
                detail_pcd = o3d.io.read_point_cloud(cloud_path)
                detail_points = np.asarray(detail_pcd.points)
                detail_colors = np.asarray(detail_pcd.colors)
                
                # Об'єднуємо масиви
                combined_points = np.vstack([combined_points, detail_points])
                combined_colors = np.vstack([combined_colors, detail_colors])
            
            # Створюємо нову хмару точок
            combined_pcd = o3d.geometry.PointCloud()
            combined_pcd.points = o3d.utility.Vector3dVector(combined_points)
            combined_pcd.colors = o3d.utility.Vector3dVector(combined_colors)
            
            # Видаляємо дублікати та викиди
            combined_pcd = combined_pcd.voxel_down_sample(voxel_size=0.005)
            combined_pcd, _ = combined_pcd.remove_statistical_outlier(nb_neighbors=20, std_ratio=2.0)
            
            # Зберігаємо об'єднану хмару
            combined_path = os.path.join(self.dense_dir, "fused_combined.ply")
            o3d.io.write_point_cloud(combined_path, combined_pcd)
            
            self.logger.info(f"Створено комбіновану хмару точок з {len(combined_pcd.points)} точок")
            return combined_path
            
        except Exception as e:
            self.logger.error(f"Помилка при об'єднанні хмар точок: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return main_cloud_path
    
    def _find_sparse_model_dir(self):
        """
        Знаходить директорію з sparse моделлю COLMAP.
        
        Returns:
            str: Шлях до директорії з моделлю
        """
        model_dir = os.path.join(self.sparse_dir, "0")
        if not os.path.exists(model_dir):
            subdirs = [d for d in os.listdir(self.sparse_dir) 
                      if os.path.isdir(os.path.join(self.sparse_dir, d))]
            if subdirs:
                model_dir = os.path.join(self.sparse_dir, subdirs[0])
                self.logger.info(f"Знайдено альтернативну директорію моделі: {model_dir}")
            else:
                raise FileNotFoundError(f"Не знайдено директорії з моделлю в {self.sparse_dir}")
        
        return model_dir
    
    def _copy_dense_files(self, src_dir, dst_dir):
        """
        Копіює необхідні файли з src_dir в dst_dir.
        
        Args:
            src_dir (str): Вихідна директорія
            dst_dir (str): Цільова директорія
        """
        import shutil
        
        for item in ["images", "sparse", "stereo"]:
            src_path = os.path.join(src_dir, item)
            if os.path.exists(src_path):
                dst_path = os.path.join(dst_dir, item)
                if os.path.isdir(src_path):
                    shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
                else:
                    shutil.copy2(src_path, dst_path)
                    
        self.logger.info(f"Скопійовано файли з {src_dir} в {dst_dir}")
    
    def _run_command(self, command):
        """
        Запускає зовнішню команду.
        
        Args:
            command (str): Команда для виконання
        """
        from ..utils.file_utils import run_command
        return run_command(command, logger=self.logger)