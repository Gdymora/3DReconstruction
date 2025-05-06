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
  log "Docker не встановлено." "error"
  exit 1
fi

# Перевірка наявності Docker Compose
if ! command -v docker-compose &> /dev/null; then
  log "Docker Compose не встановлено." "error"
  exit 1
fi

# Питання про збереження даних
read -p "Бажаєте зберегти завантажені зображення та результати реконструкції? (y/n): " save_data

# Зупинка контейнерів
log "Зупинка Docker контейнерів..." "info"
docker-compose down

# Перевірка статусу
if [ $? -eq 0 ]; then
  log "Контейнери успішно зупинені." "success"
else
  log "Виникла помилка при зупинці контейнерів." "error"
  exit 1
fi

# Видалення даних, якщо користувач не хоче їх зберігати
if [[ $save_data != "y" && $save_data != "Y" ]]; then
  log "Видалення даних..." "info"
  
  # Запитання про видалення контейнерів та образів
  read -p "Також видалити Docker образи? (y/n): " remove_images
  
  if [[ $remove_images == "y" || $remove_images == "Y" ]]; then
    log "Видалення Docker образів..." "info"
    docker-compose down --rmi all
    log "Docker образи видалено." "success"
  fi
  
  # Видалення даних
  log "Видалення даних реконструкції..." "info"
  rm -rf ./data/uploads/* ./data/results/*
  log "Дані видалено." "success"
else
  log "Дані збережено в директоріях ./data/uploads та ./data/results." "info"
fi

log "Система успішно зупинена." "success"

exit 0