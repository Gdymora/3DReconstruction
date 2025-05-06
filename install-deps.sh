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

# Функція для визначення дистрибутиву Linux
function get_distro() {
  if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo $ID
  elif [ -f /etc/lsb-release ]; then
    . /etc/lsb-release
    echo $DISTRIB_ID | tr '[:upper:]' '[:lower:]'
  else
    echo "unknown"
  fi
}

# Перевірка прав суперкористувача
if [ "$EUID" -ne 0 ]; then
  log "Цей скрипт потребує прав суперкористувача. Запустіть його з sudo." "error"
  exit 1
fi

distro=$(get_distro)
log "Виявлено дистрибутив: $distro" "info"

# Встановлення Docker і Docker Compose залежно від дистрибутиву
case $distro in
  "ubuntu" | "debian")
    log "Встановлення Docker на Ubuntu/Debian..." "info"
    apt-get update
    apt-get install -y apt-transport-https ca-certificates curl gnupg-agent software-properties-common
    curl -fsSL https://download.docker.com/linux/${distro}/gpg | apt-key add -
    add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/${distro} $(lsb_release -cs) stable"
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker compose
    ;;
    
  "fedora" | "centos" | "rhel")
    log "Встановлення Docker на Fedora/CentOS/RHEL..." "info"
    yum install -y dnf-plugins-core
    yum config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
    yum install -y docker-ce docker-ce-cli containerd.io
    curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker compose
    chmod +x /usr/local/bin/docker compose
    ln -s /usr/local/bin/docker compose /usr/bin/docker compose
    ;;
    
  "arch")
    log "Встановлення Docker на Arch Linux..." "info"
    pacman -Sy docker docker compose --noconfirm
    ;;
    
  *)
    log "Не вдалося визначити дистрибутив. Спробуйте встановити Docker вручну: https://docs.docker.com/get-docker/" "error"
    exit 1
    ;;
esac

# Запуск і активація Docker
log "Запуск і активація Docker..." "info"
systemctl start docker
systemctl enable docker

# Додавання поточного користувача до групи docker для запуску без sudo
current_user=$(logname 2>/dev/null || echo $SUDO_USER)
if [ -n "$current_user" ]; then
  log "Додавання користувача $current_user до групи docker..." "info"
  usermod -aG docker $current_user
  log "Перезапустіть термінал або вийдіть з системи та увійдіть знову, щоб зміни вступили в силу" "warning"
else
  log "Не вдалося визначити користувача. Додайте вашого користувача до групи docker вручну: sudo usermod -aG docker YOUR_USERNAME" "warning"
fi

# Перевірка встановлення
if command -v docker &>/dev/null && command -v docker compose &>/dev/null; then
  log "Docker та Docker Compose успішно встановлені!" "success"
  log "Docker версія: $(docker --version)" "info"
  log "Docker Compose версія: $(docker compose --version)" "info"
  
  log "Створення директорій для даних..." "info"
  mkdir -p ./data/uploads
  mkdir -p ./data/results
  chown -R $current_user:$current_user ./data
  
  log "Готово! Тепер ви можете запустити систему за допомогою ./start.sh" "success"
else
  log "Виникла помилка під час встановлення. Перевірте вивід команд вище для деталей." "error"
fi

exit 0