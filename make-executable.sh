#!/bin/bash

# Зробимо скрипти виконуваними
chmod +x start.sh
chmod +x stop.sh
chmod +x install-deps.sh

echo "Скрипти тепер виконувані. Ви можете запустити їх так:"
echo "  sudo ./install-deps.sh - для встановлення залежностей"
echo "  ./start.sh - для запуску системи"
echo "  ./stop.sh - для зупинки системи"