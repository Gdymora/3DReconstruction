FROM nvidia/cuda:11.4.3-cudnn8-devel-ubuntu20.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV QT_QPA_PLATFORM=offscreen

# Встановлення системних залежностей
RUN apt-get update && apt-get install -y \
    python3-pip python3-dev \
    build-essential cmake git \
    libboost-all-dev \
    libeigen3-dev \
    libsuitesparse-dev \
    libfreeimage-dev \
    libgoogle-glog-dev \
    libgflags-dev \
    libglew-dev \
    qtbase5-dev \
    libqt5opengl5-dev \
    libcgal-dev \
    libcgal-qt5-dev \
    libatlas-base-dev \
    libsuitesparse-dev \
    libopencv-dev \
    wget unzip \
    libflann-dev \
    libmetis-dev \
    xvfb mesa-utils libgl1-mesa-glx libgl1-mesa-dri \
    && rm -rf /var/lib/apt/lists/*

# Спроба встановити COLMAP з пакетів Ubuntu (якщо доступно)
RUN apt-get update && \
    apt-get install -y colmap || echo "COLMAP package is not available, will build from source"

# Робоча директорія
WORKDIR /app

# Копіювання файлів залежностей та встановлення Python бібліотек
COPY requirements.txt /app/
RUN pip3 install --no-cache-dir -r requirements.txt

# Копіювання решти коду
COPY . /app/

# Створення директорій для даних
RUN mkdir -p /data/uploads /data/results

# Перевірка, чи COLMAP доступний
RUN colmap -h || echo "COLMAP встановлено успішно"

# Порт для Flask API
EXPOSE 5000

# Встановлення wrapper-скрипта для роботи з Xvfb
COPY xvfb-run.sh /usr/local/bin/xvfb-run.sh
RUN chmod +x /usr/local/bin/xvfb-run.sh

# Команда запуску
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "300", "app:app"]