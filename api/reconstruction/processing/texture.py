import os
import numpy as np
import open3d as o3d
from ..utils.file_utils import run_command

class TextureProcessor:
    """
    Клас для обробки та покращення текстур 3D-моделей.
    """
    
    def __init__(self, image_dir, output_dir, logger):
        """
        Ініціалізація процесора текстур.
        
        Args:
            image_dir (str): Директорія з вхідними зображеннями
            output_dir (str): Директорія для результатів
            logger: Об'єкт для логування
        """
        self.image_dir = image_dir
        self.output_dir = output_dir
        self.logger = logger
    
    def enhance_texture(self, mesh_path, quality='medium'):
        """
        Покращує якість текстур меша.
        
        Args:
            mesh_path (str): Шлях до мешу
            quality (str): Якість реконструкції
            
        Returns:
            str: Шлях до текстурованого мешу
        """
        self.logger.info("Покращення якості текстур для меша")
        
        # Якість текстурування
        quality_params = {
            'low': "--resolution-level 2",
            'medium': "--resolution-level 1",
            'high': "--resolution-level 0 --export-texture-type png"
        }
        
        params = quality_params.get(quality, quality_params['medium'])
        
        # Шлях до текстурованого меша
        textured_mesh = os.path.join(self.output_dir, "model_textured.obj")
        
        try:
            # Спочатку перевіряємо наявність OpenMVS
            try:
                # Перевірка чи встановлений OpenMVS
                run_command("which TextureMesh", logger=self.logger)
                has_openmvs = True
            except:
                has_openmvs = False
                self.logger.warning("OpenMVS не знайдено, використовуємо альтернативний метод текстурування")
            
            if has_openmvs:
                # Запускаємо TextureMesh з OpenMVS
                texture_cmd = f"TextureMesh {mesh_path} --export-type obj {params}"
                run_command(texture_cmd, logger=self.logger)
                if os.path.exists(textured_mesh):
                    self.logger.info(f"Покращено текстури для моделі: {textured_mesh}")
                    return textured_mesh
            
            # Альтернативний метод текстурування за допомогою Open3D
            self.logger.info("Використання Open3D для текстурування")
            return self._create_simple_uvs(mesh_path, textured_mesh)
            
        except Exception as e:
            self.logger.warning(f"Не вдалося покращити текстури: {str(e)}")
            return mesh_path
    
    def _create_simple_uvs(self, mesh_path, textured_mesh_path):
        """
        Створює прості UV-координати для меша, якщо вони відсутні.
        
        Args:
            mesh_path (str): Шлях до меша
            textured_mesh_path (str): Шлях для збереження текстурованого меша
            
        Returns:
            str: Шлях до текстурованого меша
        """
        mesh = o3d.io.read_triangle_mesh(mesh_path)
        
        # Переконуємося, що меш має нормалі
        if not mesh.has_vertex_normals():
            mesh.compute_vertex_normals()
        
        # Спрощений метод створення UV-розгортки, якщо вона відсутня
        if not mesh.has_triangle_uvs():
            self.logger.info("Меш не має UV-координат, створюємо просту UV-розгортку")
            
            # Знаходимо межі об'єкта
            vertices = np.asarray(mesh.vertices)
            min_bound = np.min(vertices, axis=0)
            max_bound = np.max(vertices, axis=0)
            
            # Нормалізуємо координати до [0,1] діапазону
            normalized = (vertices - min_bound) / (max_bound - min_bound)
            
            # Створюємо прості UV-координати на основі XY проекції
            uvs = normalized[:, 0:2]
            
            # Встановлюємо UV-координати для кожного трикутника
            triangles = np.asarray(mesh.triangles)
            triangle_uvs = []
            
            for triangle in triangles:
                for vertex_idx in triangle:
                    triangle_uvs.append(uvs[vertex_idx])
            
            mesh.triangle_uvs = o3d.utility.Vector2dVector(np.array(triangle_uvs))
            self.logger.info("Створено прості UV-координати для меша")
        
        # Зберігаємо текстурований меш
        o3d.io.write_triangle_mesh(textured_mesh_path, mesh, write_triangle_uvs=True)
        self.logger.info(f"Створено текстурований меш з Open3D: {textured_mesh_path}")
        
        return textured_mesh_path