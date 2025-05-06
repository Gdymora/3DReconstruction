import os
import open3d as o3d

class ModelExporter:
    """
    Клас для експорту 3D-моделей у різні формати.
    """
    
    def __init__(self, output_dir, logger):
        """
        Ініціалізація експортера моделей.
        
        Args:
            output_dir (str): Директорія для результатів
            logger: Об'єкт для логування
        """
        self.output_dir = output_dir
        self.logger = logger
    
    def export_model(self, mesh_path):
        """
        Експортує модель у різні формати.
        
        Args:
            mesh_path (str): Шлях до мешу
            
        Returns:
            list: Список створених форматів
        """
        self.logger.info("Експорт моделі в різні формати")
        
        # Завантажуємо меш
        mesh = o3d.io.read_triangle_mesh(mesh_path)
        exported_formats = []
        
        try:
            # Експортуємо в PLY (Point Cloud Library формат)
            ply_path = os.path.join(self.output_dir, "model.ply")
            o3d.io.write_triangle_mesh(ply_path, mesh)
            exported_formats.append({"format": "ply", "path": ply_path})
            self.logger.info(f"Модель експортовано в PLY: {ply_path}")
            
            # Експортуємо в OBJ з MTL
            obj_path = os.path.join(self.output_dir, "model_with_texture.obj")
            o3d.io.write_triangle_mesh(obj_path, mesh, write_triangle_uvs=True)
            exported_formats.append({"format": "obj", "path": obj_path})
            self.logger.info(f"Модель експортовано в OBJ: {obj_path}")
            
            # Генеруємо GLTF для веб-візуалізації
            try:
                import trimesh
                tm_mesh = trimesh.load(mesh_path)
                
                # GLTF формат
                gltf_path = os.path.join(self.output_dir, "model.gltf")
                tm_mesh.export(gltf_path)
                exported_formats.append({"format": "gltf", "path": gltf_path})
                self.logger.info(f"Модель експортовано в GLTF: {gltf_path}")
                
                # Бінарний GLTF (GLB)
                glb_path = os.path.join(self.output_dir, "model.glb")
                tm_mesh.export(glb_path)
                exported_formats.append({"format": "glb", "path": glb_path})
                self.logger.info(f"Модель експортовано в GLB: {glb_path}")
                
            except Exception as e:
                self.logger.warning(f"Не вдалося експортувати в GLTF/GLB: {str(e)}")
                
            # Експортуємо в STL для 3D-друку
            try:
                stl_path = os.path.join(self.output_dir, "model.stl")
                if hasattr(o3d.io, 'write_triangle_mesh'):
                    o3d.io.write_triangle_mesh(stl_path, mesh)
                    exported_formats.append({"format": "stl", "path": stl_path})
                    self.logger.info(f"Модель експортовано в STL: {stl_path}")
                else:
                    # Альтернативно через trimesh, якщо доступний
                    if 'trimesh' in locals():
                        tm_mesh.export(stl_path)
                        exported_formats.append({"format": "stl", "path": stl_path})
                        self.logger.info(f"Модель експортовано в STL через trimesh: {stl_path}")
            except Exception as e:
                self.logger.warning(f"Не вдалося експортувати в STL: {str(e)}")
        
        except Exception as e:
            self.logger.error(f"Помилка під час експорту моделі: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
        
        self.logger.info(f"Модель експортовано в {len(exported_formats)} форматів")
        return exported_formats