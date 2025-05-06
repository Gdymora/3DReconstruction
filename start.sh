#!/bin/bash

# Кольорові повідомлення
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Функція для виведення повідомлень
function log() {
  if [ "$2" = "info" ]; then
    echo -e "${BLUE}[INFO]${NC} $1"
  elif [ "$2" = "success" ]; then
    echo -e "${GREEN}[SUCCESS]${NC} $1"
  elif [ "$2" = "warning" ]; then
    echo -e "${YELLOW}[WARNING]${NC} $1"
  elif [ "$2" = "error" ]; then
    echo -e "${RED}[ERROR]${NC} $1"
  else
    echo -e "$1"
  fi
}

# Перевірка наявності Docker
if ! command -v docker &> /dev/null; then
  log "Docker не встановлено. Будь ласка, встановіть Docker перед запуском." "error"
  exit 1
fi

# Перевірка наявності Docker Compose
if ! command -v docker compose &> /dev/null; then
  log "Docker Compose не встановлено. Будь ласка, встановіть Docker Compose перед запуском." "error"
  exit 1
fi

# Створення необхідних директорій
log "Створення директорій для даних..." "info"
mkdir -p ./data/uploads
mkdir -p ./data/results

# Перевірка наявності .env файлу
if [ ! -f .env ]; then
  log "Файл .env не знайдено. Створюємо базовий конфігураційний файл..." "warning"
  cp .env.example .env 2>/dev/null || {
    log "Створення файлу .env з шаблону не вдалося. Створюємо базовий файл..." "warning"
    echo "# Загальні налаштування
COMPOSE_PROJECT_NAME=3d-reconstruction

# Налаштування API
API_PORT=5000
API_WORKERS=4
API_TIMEOUT=300
FLASK_ENV=development
MAX_UPLOAD_SIZE=100MB

# Шляхи збереження даних
DATA_UPLOAD_PATH=./data/uploads
DATA_RESULTS_PATH=./data/results

# Налаштування Nginx
NGINX_PORT=80

# Налаштування фронтенду
FRONTEND_PORT=3000
REACT_APP_API_URL=/api

# Налаштування Docker
DOCKER_BUILDKIT=1
DOCKER_COMPOSE_VERSION=3.8" > .env
  }
  log "Створено файл .env з базовими налаштуваннями." "success"
fi

# Запуск контейнерів
log "Запуск Docker контейнерів..." "info"
docker compose up -d

# Перевірка статусу
if [ $? -eq 0 ]; then
  log "Система 3D-реконструкції успішно запущена!" "success"
  echo ""
  log "Додаток доступний за адресою: http://localhost" "info"
  echo ""
  log "Для перегляду логів використовуйте команду: docker compose logs -f" "info"
  log "Для зупинки додатку використовуйте команду: docker compose down" "info"
else
  log "Виникла помилка при запуску контейнерів. Перевірте логи: docker compose logs" "error"
  exit 1
fi

# Тестовий запит до API для перевірки працездатності
echo ""
log "Перевірка доступності API..." "info"
timeout 30 bash -c 'until curl -s http://localhost/health > /dev/null; do sleep 2; done' 2>/dev/null
if [ $? -eq 0 ]; then
  log "API доступне! Система готова до використання." "success"
else
  log "Не вдалося підтвердити доступність API. Система може ще запускатися, перевірте статус: docker compose ps" "warning"
fi

exit 0