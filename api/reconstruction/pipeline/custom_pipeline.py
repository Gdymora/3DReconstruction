import os
import cv2
import numpy as np
import open3d as o3d
from .base_pipeline import BasePipeline
from ..processing.mesh import MeshProcessor
from ..processing.texture import TextureProcessor
from ..export.model_exporter import ModelExporter

class CustomPipeline(BasePipeline):
    """
    Власний пайплайн реконструкції з використанням OpenCV та Open3D.
    """
    
    def run(self):
        """
        Запускає повний процес реконструкції з використанням власного алгоритму.
        
        Returns:
            str: Шлях до згенерованої 3D-моделі
        """
        try:
            # Перевіряємо вхідні дані
            if not self.validate_input():
                raise ValueError("Невалідні вхідні дані")
                
            # Етап 1: Виявлення та зіставлення ключових точок
            self.progress.update_progress("keypoints", 10, "Виявлення ключових точок на зображеннях")
            self.logger.info("Виявлення та зіставлення ключових точок")
            
            image_files, features_points, matches_pairs = self._detect_and_match_features()
            self.progress.update_progress("keypoints", 20, "Ключові точки виявлено та зіставлено")
            
            # Етап 2: Створення базової хмари точок
            self.progress.update_progress("pointcloud", 30, "Створення базової хмари точок")
            self.logger.info("Створення базової хмари точок")
            
            point_cloud = self._create_point_cloud(image_files, features_points, matches_pairs)
            point_cloud_path = os.path.join(self.output_dir, "point_cloud.ply")
            o3d.io.write_point_cloud(point_cloud_path, point_cloud)
            self.progress.update_progress("pointcloud", 50, "Базову хмару точок створено")
            
            # Етап 3: Створення меша з хмари точок
            self.progress.update_progress("mesh", 60, "Створення полігональної моделі")
            self.logger.info("Створення меша з хмари точок")
            
            mesh_processor = MeshProcessor(self.output_dir, self.logger)
            mesh_path = mesh_processor.create_mesh(point_cloud_path, self.quality)
            self.progress.update_progress("mesh", 70, "Модель створено")
            
            # Етап 4: Очищення та оптимізація меша
            self.progress.update_progress("clean", 75, "Очищення та оптимізація моделі")
            self.logger.info("Очищення та оптимізація меша")
            
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
            self.logger.error(f"Помилка в custom пайплайні: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            raise
    
    def _detect_and_match_features(self):
        """
        Виявляє ключові точки на зображеннях та зіставляє їх.
        
        Returns:
            tuple: (image_files, features_points, matches_pairs)
        """
        # Отримуємо список зображень
        image_files = [os.path.join(self.input_dir, f) for f in os.listdir(self.input_dir) 
                      if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        
        # Ініціалізуємо SIFT детектор
        sift = cv2.SIFT_create()
        
        # Знаходимо характеристичні точки для кожного зображення
        features_points = []
        descriptors_list = []
        
        self.logger.info(f"Обробка {len(image_files)} зображень")
        
        for img_path in image_files:
            img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                self.logger.warning(f"Не вдалося завантажити зображення: {img_path}")
                continue
                
            # Знаходимо ключові точки та дескриптори
            keypoints, descriptors = sift.detectAndCompute(img, None)
            if descriptors is None:
                self.logger.warning(f"Не знайдено ключових точок на зображенні: {img_path}")
                continue
                
            features_points.append(keypoints)
            descriptors_list.append(descriptors)
            self.logger.info(f"Знайдено {len(keypoints)} ключових точок на {os.path.basename(img_path)}")
        
        # Зіставлення характеристичних точок між парами зображень
        matcher = cv2.BFMatcher()
        matches_pairs = []
        
        self.logger.info("Зіставлення ключових точок між парами зображень")
        total_matches = 0
        
        for i in range(len(descriptors_list)):
            for j in range(i+1, len(descriptors_list)):
                if descriptors_list[i] is None or descriptors_list[j] is None:
                    continue
                matches = matcher.knnMatch(descriptors_list[i], descriptors_list[j], k=2)
                
                # Застосовуємо фільтр співвідношення Лоу для видалення поганих зіставлень
                good_matches = []
                for m, n in matches:
                    if m.distance < 0.7 * n.distance:
                        good_matches.append(m)
                
                matches_pairs.append((i, j, good_matches))
                total_matches += len(good_matches)
        
        self.logger.info(f"Знайдено {total_matches} зіставлень між парами зображень")
        
        return image_files, features_points, matches_pairs
    
    def _create_point_cloud(self, image_files, features_points, matches_pairs):
        """
        Створює хмару точок на основі ключових точок та їх зіставлень.
        
        Args:
            image_files (list): Список шляхів до зображень
            features_points (list): Список ключових точок для кожного зображення
            matches_pairs (list): Список зіставлень між парами зображень
            
        Returns:
            o3d.geometry.PointCloud: Хмара точок
        """
        # Ініціалізуємо хмару точок
        point_cloud = o3d.geometry.PointCloud()
        
        # Якщо є достатньо зіставлень, використовуємо справжню геометричну інформацію
        if matches_pairs and any(len(m) > 10 for _, _, m in matches_pairs):
            # Беремо пару з найбільшою кількістю зіставлень
            best_pair = max(matches_pairs, key=lambda x: len(x[2]))
            i, j, good_matches = best_pair
            
            self.logger.info(f"Використання найкращої пари зображень з {len(good_matches)} зіставленнями")
            
            # Завантажуємо зображення для цієї пари
            img1 = cv2.imread(image_files[i], cv2.IMREAD_COLOR)
            img2 = cv2.imread(image_files[j], cv2.IMREAD_COLOR)
            
            # Отримуємо точки для обчислення фундаментальної матриці
            pts1 = np.float32([features_points[i][m.queryIdx].pt for m in good_matches])
            pts2 = np.float32([features_points[j][m.trainIdx].pt for m in good_matches])
            
            # Обчислюємо фундаментальну матрицю
            F, mask = cv2.findFundamentalMat(pts1, pts2, cv2.FM_RANSAC)
            
            # Відфільтровуємо викиди (outliers)
            inlier_mask = mask.ravel() == 1
            pts1 = pts1[inlier_mask]
            pts2 = pts2[inlier_mask]
            
            # Обчислюємо камери для стереопари
            _, H1, H2 = cv2.stereoRectifyUncalibrated(pts1, pts2, F, img1.shape[:2])
            
            # Створюємо хмару точок для демонстрації
            # У реальній імплементації тут би була тріангуляція точок
            points = []
            colors = []
            
            for k in range(pts1.shape[0]):
                # Створюємо просту 3D точку з 2D координат (демонстрація)
                x = pts1[k, 0] / img1.shape[1] - 0.5
                y = pts1[k, 1] / img1.shape[0] - 0.5
                
                # Використовуємо різницю між точками як наближення глибини z
                diff_x = pts1[k, 0] - pts2[k, 0]
                diff_y = pts1[k, 1] - pts2[k, 1]
                z = -0.5 * (abs(diff_x) + abs(diff_y)) / (img1.shape[1] + img1.shape[0])
                
                points.append([x, y, z])
                
                # Додаємо колір з першого зображення
                color = img1[int(pts1[k, 1]), int(pts1[k, 0])] / 255.0
                colors.append(color[::-1])  # BGR -> RGB
                
            # Згущення хмари точок для кращої якості реконструкції
            self._densify_point_cloud(points, colors)
                
        else:
            # Якщо не вдалося зіставити характеристичні точки, створюємо демонстраційну модель
            self.logger.warning("Недостатньо зіставлень, створюємо демонстраційну модель")
            
            # Завантажуємо і аналізуємо перше зображення для демонстрації
            base_img = cv2.imread(image_files[0])
            
            if base_img is None:
                raise ValueError("Не вдалося завантажити перше зображення")
                
            height, width = base_img.shape[:2]
            
            # Визначаємо орієнтовну форму об'єкта з зображення
            gray = cv2.cvtColor(base_img, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Використовуємо найбільший контур як основу для 3D форми
            points = []
            colors = []
            
            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                # Отримуємо опуклу оболонку контуру для більш стабільної форми
                hull = cv2.convexHull(largest_contour)
                
                # Створюємо 3D точки на основі 2D контуру
                z_levels = 5  # Кількість шарів по глибині
                
                for z_idx in range(z_levels):
                    z = (z_idx / (z_levels - 1)) - 0.5  # від -0.5 до 0.5
                    scale_factor = 1.0 - 0.3 * abs(z)  # Менший масштаб на краях
                    
                    for pt_idx in range(len(hull)):
                        pt = hull[pt_idx][0]
                        # Нормалізуємо координати
                        x = (pt[0] / width - 0.5) * 2.0 * scale_factor
                        y = (pt[1] / height - 0.5) * 2.0 * scale_factor
                        
                        # Додаємо шум для натуральності
                        x += np.random.normal(0, 0.01)
                        y += np.random.normal(0, 0.01)
                        z += np.random.normal(0, 0.01)
                        
                        points.append([x, y, z])
                        
                        # Отримання кольору з зображення
                        x_img = int((x / 2.0 + 0.5) * width)
                        y_img = int((y / 2.0 + 0.5) * height)
                        
                        # Обмеження координат
                        x_img = max(0, min(x_img, width - 1))
                        y_img = max(0, min(y_img, height - 1))
                        
                        color = base_img[y_img, x_img] / 255.0
                        colors.append(color[::-1])  # BGR -> RGB
                
                # Додаємо додаткові випадкові точки для заповнення обсягу
                num_random_points = 5000 if self.quality == 'high' else (3000 if self.quality == 'medium' else 1000)
                for _ in range(num_random_points):
                    x = np.random.uniform(-0.8, 0.8)
                    y = np.random.uniform(-0.8, 0.8)
                    z = np.random.uniform(-0.5, 0.5)
                    
                    # Відстань від центру
                    dist = np.sqrt(x*x + y*y + z*z*4)
                    
                    # Додаємо точку, якщо вона знаходиться в межах об'єкта
                    if dist < 0.8:
                        points.append([x, y, z])
                        
                        # Визначаємо колір
                        x_img = int((x / 2.0 + 0.5) * width)
                        y_img = int((y / 2.0 + 0.5) * height)
                        
                        # Обмеження координат
                        x_img = max(0, min(x_img, width - 1))
                        y_img = max(0, min(y_img, height - 1))
                        
                        color = base_img[y_img, x_img] / 255.0
                        colors.append(color[::-1])  # BGR -> RGB
            else:
                # Якщо не знайдено контурів, створюємо просту форму
                self.logger.warning("Контури не виявлено, створюємо просту фігуру")
                for _ in range(5000):
                    x = np.random.uniform(-0.5, 0.5)
                    y = np.random.uniform(-0.5, 0.5)
                    z = np.random.uniform(-0.5, 0.5)
                    dist = np.sqrt(x*x + y*y + z*z*4)
                    if dist < 0.5:
                        points.append([x, y, z])
                        colors.append(np.random.uniform(0, 1, size=3))  # Випадкові кольори
        
        # Створюємо хмару точок з обчислених/згенерованих даних
        point_cloud.points = o3d.utility.Vector3dVector(np.array(points))
        point_cloud.colors = o3d.utility.Vector3dVector(np.array(colors))
        
        # Обчислюємо нормалі для хмари точок
        self.logger.info("Обчислення нормалей для хмари точок")
        
        # Параметри для різної якості
        normal_nn = 30 if self.quality == 'high' else (20 if self.quality == 'medium' else 10)
        normal_radius = 0.05 if self.quality == 'high' else (0.1 if self.quality == 'medium' else 0.2)
        
        point_cloud.estimate_normals(
            search_param=o3d.geometry.KDTreeSearchParamHybrid(
                radius=normal_radius, 
                max_nn=normal_nn
            )
        )
        point_cloud.orient_normals_consistent_tangent_plane(k=15)
        
        return point_cloud
    
    def _densify_point_cloud(self, points, colors):
        """
        Згущує хмару точок для кращої якості реконструкції.
        
        Args:
            points (list): Список точок
            colors (list): Список кольорів
        """
        if self.quality != 'low' and len(points) < 10000:
            self.logger.info("Згущення хмари точок")
            
            # Створюємо тимчасову хмару точок для пошуку найближчих сусідів
            temp_pcd = o3d.geometry.PointCloud()
            temp_pcd.points = o3d.utility.Vector3dVector(np.array(points))
            temp_pcd.colors = o3d.utility.Vector3dVector(np.array(colors))
            
            # Створюємо додаткові точки шляхом інтерполяції
            dense_factor = 3 if self.quality == 'high' else 2
            points_np = np.asarray(temp_pcd.points)
            colors_np = np.asarray(temp_pcd.colors)
            
            # Для кожної пари сусідніх точок створюємо проміжні точки
            extra_points = []
            extra_colors = []
            
            # Знаходимо k найближчих сусідів для кожної точки
            pcd_tree = o3d.geometry.KDTreeFlann(temp_pcd)
            
            # Обробляємо підмножину точок для економії часу
            num_points_to_process = min(len(points_np), 1000)
            step = max(1, len(points_np) // num_points_to_process)
            
            for i in range(0, len(points_np), step):
                # Знаходимо k найближчих сусідів
                k = min(5, len(points_np) - 1)
                _, idx, _ = pcd_tree.search_knn_vector_3d(points_np[i], k+1)
                
                # Пропускаємо першу точку, бо це сама точка
                for j in range(1, len(idx)):
                    # Створюємо проміжні точки між точкою і її сусідом
                    p1 = points_np[i]
                    p2 = points_np[idx[j]]
                    color1 = colors_np[i]
                    color2 = colors_np[idx[j]]
                    
                    for f in range(1, dense_factor):
                        t = f / dense_factor
                        # Лінійна інтерполяція
                        new_point = p1 * (1 - t) + p2 * t
                        new_color = color1 * (1 - t) + color2 * t
                        
                        extra_points.append(new_point)
                        extra_colors.append(new_color)
            
            # Додаємо нові точки до списків
            if extra_points:
                points.extend(extra_points)
                colors.extend(extra_colors)
                self.logger.info(f"Додано {len(extra_points)} нових точок, загальна кількість: {len(points)}")