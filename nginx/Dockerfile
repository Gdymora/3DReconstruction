FROM nginx:1.21-alpine

# Видаляємо стандартну конфігурацію
RUN rm /etc/nginx/conf.d/default.conf
RUN rm /etc/nginx/nginx.conf

# Копіюємо нашу конфігурацію
COPY nginx.conf /etc/nginx/nginx.conf

# Створюємо директорію для результатів
RUN mkdir -p /usr/share/nginx/html/results

# Встановлення додаткових утиліт
RUN apk add --no-cache bash curl

# Створення скрипту для перевірки здоров'я
RUN echo '#!/bin/sh\n\
if curl -f http://localhost:80/health > /dev/null 2>&1; then\n\
    exit 0\n\
else\n\
    exit 1\n\
fi' > /usr/local/bin/health-check.sh && \
    chmod +x /usr/local/bin/health-check.sh

# Експортуємо порт
EXPOSE 80

# Точка входу
CMD ["nginx", "-g", "daemon off;"]