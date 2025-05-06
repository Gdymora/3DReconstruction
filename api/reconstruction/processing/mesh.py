import os
import numpy as np
import open3d as o3d
import scipy.sparse as sp
from scipy.sparse.csgraph import connected_components

class MeshProcessor:
    """
    Клас для створення та обробки 3D-мешів.
    """
    
    def __init__(self, output_dir, logger):
        """
        Ініціалізація процесора мешів.
        
        Args:
            output_dir (str): Директорія для результатів
            logger: Об'єкт для логування
        """
        self.output_dir = output_dir
        self.logger = logger
        
        # Параметри для різної якості
        self.quality_params = {
            'low': {'depth': 8, 'smoothing_iters': 2, 'denoise_neighbors': 6},
            'medium': {'depth': 10, 'smoothing_iters': 3, 'denoise_neighbors': 10},
            'high': {'depth': 12, 'smoothing_iters': 5, 'denoise_neighbors': 16}
        }
    
    def create_mesh(self, point_cloud_path, quality='medium'):
        """
        Створює меш з хмари точок.
        
        Args:
            point_cloud_path (str): Шлях до хмари точок
            quality (str): Якість реконструкції
            
        Returns:
            str: Шлях до створеного мешу
        """
        self.logger.info("Створення меша з хмари точок")
        
        params = self.quality_params.get(quality, self.quality_params['medium'])
        
        # Завантажуємо хмару точок
        pcd = o3d.io.read_point_cloud(point_cloud_path)
        
        # Фільтруємо викиди з покращеними параметрами
        self.logger.info("Фільтрація викидів з хмари точок")
        filtered_pcd, _ = pcd.remove_statistical_outlier(
            nb_neighbors=params['denoise_neighbors'], 
            std_ratio=2.0
        )
        
        # Обчислюємо нормалі, якщо їх немає
        if not filtered_pcd.has_normals():
            self.logger.info("Обчислення нормалей для хмари точок")
            filtered_pcd.estimate_normals(
                search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30)
            )
            filtered_pcd.orient_normals_consistent_tangent_plane(k=15)
        
        # Створюємо меш за допомогою алгоритму Poisson
        self.logger.info(f"Застосування Poisson surface reconstruction з глибиною {params['depth']}")
        mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
            filtered_pcd, 
            depth=params['depth'],
            scale=1.1,
            linear_fit=True
        )
        
        # Видаляємо трикутники з низькою вагою
        percentile = 0.1 if quality == 'low' else (0.05 if quality == 'medium' else 0.02)
        vertices_to_remove = densities < np.quantile(densities, percentile)
        mesh.remove_vertices_by_mask(vertices_to_remove)
        
        # Згладжуємо меш
        self.logger.info(f"Згладжування меша з {params['smoothing_iters']} ітераціями")
        mesh = mesh.filter_smooth_taubin(number_of_iterations=params['smoothing_iters'])
        mesh.compute_vertex_normals()
        
        # Зберігаємо меш
        mesh_path = os.path.join(self.output_dir, "model.obj")
        o3d.io.write_triangle_mesh(mesh_path, mesh)
        
        self.logger.info(f"Меш створено та збережено: {mesh_path}")
        
        return mesh_path
    
    def clean_mesh(self, mesh_path):
        """
        Очищає меш від шуму та відокремлених компонентів.
        
        Args:
            mesh_path (str): Шлях до мешу
            
        Returns:
            str: Шлях до очищеного мешу
        """
        self.logger.info("Очищення меша від шуму та аномалій")
        
        try:
            # Завантажуємо меш
            mesh = o3d.io.read_triangle_mesh(mesh_path)
            
            # Базова інформація про меш
            num_vertices_original = len(mesh.vertices)
            num_triangles_original = len(mesh.triangles)
            self.logger.info(f"Оригінальний меш: {num_vertices_original} вершин, {num_triangles_original} трикутників")
            
            # Видаляємо дуплікати вершин
            mesh.remove_duplicated_vertices()
            
            # Видаляємо дуплікати трикутників
            mesh.remove_duplicated_triangles()
            
            # Видаляємо невалідні трикутники
            mesh.remove_degenerate_triangles()
            
            # Оновлена інформація
            num_vertices_after_clean = len(mesh.vertices)
            num_triangles_after_clean = len(mesh.triangles)
            
            if num_vertices_after_clean < num_vertices_original or num_triangles_after_clean < num_triangles_original:
                self.logger.info(f"Після базового очищення: {num_vertices_after_clean} вершин, {num_triangles_after_clean} трикутників")
            
            # Видаляємо неприкріплені компоненти
            triangles = np.asarray(mesh.triangles)
            vertices = np.asarray(mesh.vertices)
            
            if len(triangles) == 0:
                self.logger.warning("Меш не містить трикутників, пропускаємо аналіз компонентів")
                return mesh_path
            
            # Знаходимо компоненти зв'язності
            # Створюємо граф меша
            edges = np.vstack([
                triangles[:, [0, 1]],
                triangles[:, [1, 2]],
                triangles[:, [2, 0]]
            ])
            
            # Видаляємо дублікати ребер
            edges = np.unique(np.sort(edges, axis=1), axis=0)
            
            # Створюємо матрицю суміжності
            n_vertices = len(vertices)
            adjacency = sp.coo_matrix(
                (np.ones(len(edges)), (edges[:, 0], edges[:, 1])),
                shape=(n_vertices, n_vertices)
            )
            adjacency = (adjacency + adjacency.T) > 0
            
            # Знаходимо компоненти зв'язності
            n_components, labels = connected_components(adjacency, directed=False)
            
            if n_components > 1:
                self.logger.info(f"Знайдено {n_components} зв'язних компонентів у меші")
                
                # Знаходимо найбільший компонент
                component_sizes = np.bincount(labels)
                largest_component = np.argmax(component_sizes)
                
                # Створюємо маску для вершин
                mask = (labels == largest_component)
                
                # Застосовуємо маску до меша
                mesh_clean = mesh.select_by_index(np.where(mask)[0])
                
                # Зберігаємо очищений меш
                clean_path = os.path.join(self.output_dir, "model_clean.obj")
                o3d.io.write_triangle_mesh(clean_path, mesh_clean)
                
                self.logger.info(f"Видалено {n_components-1} відокремлених компонентів з меша")
                self.logger.info(f"Підсумковий меш: {len(mesh_clean.vertices)} вершин, {len(mesh_clean.triangles)} трикутників")
                
                return clean_path
            else:
                self.logger.info("Меш має лише один зв'язний компонент, очищення не потрібне")
            
            return mesh_path
            
        except Exception as e:
            self.logger.error(f"Помилка під час очищення меша: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return mesh_path  # Повертаємо оригінальний шлях у випадку помилки