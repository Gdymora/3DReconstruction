import os
import uuid
import shutil
import json
import time
import threading
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from reconstruction.reconstructor import Reconstructor
from reconstruction.utils.file_utils import create_directory, clean_temp_files
from reconstruction.utils.logging_utils import setup_logger

app = Flask(__name__)
CORS(app)  # Дозволяємо крос-доменні запити

# Конфігурація
UPLOAD_FOLDER = "/data/uploads"
RESULTS_FOLDER = "/data/results"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["RESULTS_FOLDER"] = RESULTS_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100 MB максимальний розмір файлу
base_url = os.environ.get("API_BASE_URL", "http://localhost:5000")

# Створення директорій, якщо вони ще не існують
create_directory(UPLOAD_FOLDER)
create_directory(RESULTS_FOLDER)

# Налаштовуємо логування
logger = setup_logger(RESULTS_FOLDER, "app")

# Дозволені розширення файлів зображень
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "tif", "tiff"}


def allowed_file(filename):
    """Перевіряє, чи файл має дозволене розширення"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/health", methods=["GET"])
def health_check():
    """Ендпоінт для перевірки стану API"""
    return jsonify({"status": "ok", "timestamp": time.time()})


@app.route("/api/upload", methods=["POST"])
def upload_images():
    """Завантаження зображень для 3D-реконструкції"""
    if "files" not in request.files:
        return jsonify({"error": "No files provided"}), 400

    files = request.files.getlist("files")

    if len(files) < 3:
        return (
            jsonify({"error": "At least 3 images are required for 3D reconstruction"}),
            400,
        )

    # Створюємо унікальну директорію для сесії
    session_id = str(uuid.uuid4())
    session_upload_dir = os.path.join(app.config["UPLOAD_FOLDER"], session_id)
    session_results_dir = os.path.join(app.config["RESULTS_FOLDER"], session_id)

    create_directory(session_upload_dir)
    create_directory(session_results_dir)

    # Зберігаємо файли
    saved_files = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(session_upload_dir, filename)
            file.save(filepath)
            saved_files.append(filepath)

    if not saved_files:
        return jsonify({"error": "No valid images uploaded"}), 400

    # Записуємо метадані сесії
    metadata = {
        "session_id": session_id,
        "timestamp": time.time(),
        "num_images": len(saved_files),
        "status": "uploaded",
    }

    with open(os.path.join(session_results_dir, "metadata.json"), "w") as f:
        json.dump(metadata, f)

    return jsonify(
        {
            "session_id": session_id,
            "message": f"Successfully uploaded {len(saved_files)} images",
            "status": "success",
        }
    )


@app.route("/api/reconstruct/<session_id>", methods=["POST"])
def reconstruct(session_id):
    """Запуск процесу 3D-реконструкції для заданої сесії"""
    session_upload_dir = os.path.join(app.config["UPLOAD_FOLDER"], session_id)
    session_results_dir = os.path.join(app.config["RESULTS_FOLDER"], session_id)

    if not os.path.exists(session_upload_dir):
        return jsonify({"error": "Session not found"}), 404

    # Отримуємо параметри реконструкції з запиту
    data = request.json or {}
    quality = data.get("quality", "medium")  # 'low', 'medium', 'high'
    method = data.get("method", "custom")  # 'colmap', 'openmvs', 'custom'

    # Запускаємо процес реконструкції в окремому потоці
    reconstruction_thread = threading.Thread(
        target=run_reconstruction_task,
        args=(session_id, session_upload_dir, session_results_dir, quality, method),
    )
    reconstruction_thread.daemon = True
    reconstruction_thread.start()

    # Одразу повертаємо відповідь про початок обробки
    return jsonify(
        {
            "session_id": session_id,
            "status": "processing",
            "message": "Reconstruction started. Check status with /api/results/{}".format(
                session_id
            ),
        }
    )


def run_reconstruction_task(session_id, input_dir, output_dir, quality, method):
    """Функція для виконання реконструкції в окремому потоці"""
    try:
        logger.info(
            f"Запуск реконструкції для сесії {session_id}, метод: {method}, якість: {quality}"
        )

        # Ініціалізуємо реконструктор
        reconstructor = Reconstructor(session_id, input_dir, output_dir)

        # Запускаємо реконструкцію
        result_path = reconstructor.run_reconstruction(method=method, quality=quality)

        logger.info(f"Реконструкція завершена успішно: {result_path}")

    except Exception as e:
        logger.error(f"Помилка під час реконструкції: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())


@app.route("/api/results/<session_id>", methods=["GET"])
def get_results(session_id):
    """Отримання результатів реконструкції"""
    session_results_dir = os.path.join(app.config["RESULTS_FOLDER"], session_id)

    if not os.path.exists(session_results_dir):
        return jsonify({"error": "Results not found"}), 404

    metadata_path = os.path.join(session_results_dir, "metadata.json")
    if not os.path.exists(metadata_path):
        return jsonify({"error": "Results metadata not found"}), 404

    with open(metadata_path, "r") as f:
        metadata = json.load(f)

    # Формуємо URL для завантаження моделі
    files = []
    for filename in os.listdir(session_results_dir):
        if filename.endswith((".obj", ".ply", ".stl", ".gltf", ".glb")):
            files.append(
                {
                    "filename": filename,
                    "url": f"{base_url}/api/results/{session_id}/{filename}",
                }
            )

    metadata["files"] = files

    return jsonify(metadata)


@app.route("/api/results/<session_id>/<path:filename>", methods=["GET"])
def serve_results_file(session_id, filename):
    """Serve files from the results directory"""
    session_results_dir = os.path.join(app.config["RESULTS_FOLDER"], session_id)
    # Handle nested paths correctly
    file_path = os.path.normpath(os.path.join(session_results_dir, filename))

    # Security check to ensure the file is within the session directory
    if not file_path.startswith(session_results_dir):
        return jsonify({"error": "Invalid file path"}), 403

    directory = os.path.dirname(file_path)
    base_filename = os.path.basename(file_path)

    # Перевірка існування файлу
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found", "path": file_path}), 404

    return send_from_directory(directory, base_filename)


@app.route("/api/model/<session_id>", methods=["GET"])
def get_model(session_id):
    """Endpoint for getting 3D model data for display in web browser"""
    logger.info(f"Отримано запит на модель для сесії: {session_id}")

    try:
        session_results_dir = os.path.join(app.config["RESULTS_FOLDER"], session_id)
        logger.info(f"Шукаємо в директорії: {session_results_dir}")

        if not os.path.exists(session_results_dir):
            logger.warning(f"Директорія не існує: {session_results_dir}")
            return jsonify({"error": "Results directory not found"}), 404

        # Priority order of formats
        model_extensions = [".gltf", ".glb", ".obj", ".ply"]

        model_file = None
        subdir_path = None

        # First check in the main results directory
        logger.info(f"Вміст головної директорії: {os.listdir(session_results_dir)}")
        for ext in model_extensions:
            possible_files = [
                f for f in os.listdir(session_results_dir) if f.endswith(ext)
            ]
            if possible_files:
                model_file = possible_files[0]
                subdir_path = ""
                logger.info(f"Знайдено файл у головній директорії: {model_file}")
                break

        # If not found, check subdirectories
        if not model_file:
            for subdir in os.listdir(session_results_dir):
                full_subdir_path = os.path.join(session_results_dir, subdir)
                if os.path.isdir(full_subdir_path):
                    logger.info(f"Перевіряємо піддиректорію: {subdir}")
                    logger.info(f"Вміст піддиректорії: {os.listdir(full_subdir_path)}")
                    for ext in model_extensions:
                        possible_files = [
                            f for f in os.listdir(full_subdir_path) if f.endswith(ext)
                        ]
                        if possible_files:
                            model_file = possible_files[0]
                            subdir_path = subdir
                            logger.info(
                                f"Знайдено файл у піддиректорії: {subdir}/{model_file}"
                            )
                            break
                    if model_file:
                        break

        if not model_file:
            logger.warning("Модель не знайдено в жодній директорії")
            return (
                jsonify(
                    {
                        "error": "No 3D model found",
                        "details": f"Searched in {session_results_dir}",
                        "available_files": os.listdir(session_results_dir),
                    }
                ),
                404,
            )

        # Construct the correct URL path for the model
        if subdir_path:
            model_url = (
                f"{base_url}/api/results/{session_id}/{subdir_path}/{model_file}"
            )
            full_model_path = os.path.join(session_results_dir, subdir_path, model_file)
        else:
            model_url = f"{base_url}/api/results/{session_id}/{model_file}"
            full_model_path = os.path.join(session_results_dir, model_file)

        logger.info(f"Створено URL моделі: {model_url}")
        logger.info(f"Повний шлях до файлу: {full_model_path}")

        # Verify file exists
        if not os.path.exists(full_model_path):
            logger.warning(f"Файл не існує за шляхом: {full_model_path}")
            return (
                jsonify({"error": "Model file not found", "path": full_model_path}),
                404,
            )

        response_data = {
            "model_url": model_url,
            "model_type": os.path.splitext(model_file)[1][1:],
            "session_id": session_id,
            "file_name": model_file,
        }
        logger.info(f"Відповідь API: {response_data}")
        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Помилка при отриманні моделі: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@app.route("/api/download/<session_id>/<filename>", methods=["GET"])
def download_file(session_id, filename):
    """Ендпоінт для завантаження згенерованих файлів"""
    session_results_dir = os.path.join(app.config["RESULTS_FOLDER"], session_id)
    return send_from_directory(session_results_dir, filename, as_attachment=True)


@app.route("/api/download-zip/<session_id>", methods=["GET"])
def download_all_results(session_id):
    """Завантаження всіх результатів як ZIP-архіву"""
    session_results_dir = os.path.join(app.config["RESULTS_FOLDER"], session_id)

    if not os.path.exists(session_results_dir):
        return jsonify({"error": "Results not found"}), 404

    # Створюємо тимчасовий ZIP-файл
    zip_filename = f"{session_id}_results.zip"
    zip_path = os.path.join(session_results_dir, zip_filename)

    shutil.make_archive(
        os.path.splitext(zip_path)[0],  # Вихідний шлях без розширення
        "zip",  # Формат архіву
        session_results_dir,  # Директорія для архівації
    )

    return send_from_directory(session_results_dir, zip_filename, as_attachment=True)


@app.route("/api/delete/<session_id>", methods=["DELETE"])
def delete_session(session_id):
    """Видалення сесії та всіх пов'язаних з нею файлів"""
    session_upload_dir = os.path.join(app.config["UPLOAD_FOLDER"], session_id)
    session_results_dir = os.path.join(app.config["RESULTS_FOLDER"], session_id)

    deleted = False

    if os.path.exists(session_upload_dir):
        shutil.rmtree(session_upload_dir)
        deleted = True

    if os.path.exists(session_results_dir):
        shutil.rmtree(session_results_dir)
        deleted = True

    if not deleted:
        return jsonify({"error": "Session not found"}), 404

    return jsonify({"session_id": session_id, "status": "deleted"})


@app.route("/api/status/<session_id>", methods=["GET"])
def check_status(session_id):
    """Перевірка статусу процесу реконструкції"""
    session_results_dir = os.path.join(app.config["RESULTS_FOLDER"], session_id)

    if not os.path.exists(session_results_dir):
        return jsonify({"error": "Session not found"}), 404

    # Зчитуємо метадані
    metadata_path = os.path.join(session_results_dir, "metadata.json")
    if not os.path.exists(metadata_path) or os.path.getsize(metadata_path) == 0:
        return (
            jsonify(
                {
                    "session_id": session_id,
                    "status": "unknown",
                    "error": "Metadata not found or empty",
                }
            ),
            404,
        )

    try:
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
    except json.JSONDecodeError:
        # Якщо файл існує, але має невалідний JSON
        return (
            jsonify(
                {
                    "session_id": session_id,
                    "status": "unknown",
                    "error": "Invalid metadata format",
                }
            ),
            500,
        )

    # Додаємо прогрес
    if metadata["status"] == "processing":
        # Тут можна додати логіку розрахунку прогресу
        started_at = metadata.get("started_at", 0)
        elapsed_time = time.time() - started_at
        metadata["elapsed_time"] = int(elapsed_time)

    return jsonify(metadata)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
