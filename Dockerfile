FROM python:3.11-slim

WORKDIR /app

# Устанавливаем системные зависимости для matplotlib
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libfreetype6-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY . .

# Создаем папки для логов и графиков
RUN mkdir -p logs charts data

# Создаем пользователя
RUN useradd -m -u 1000 gasmonitor && \
    chown -R gasmonitor:gasmonitor /app

USER gasmonitor

# Точка входа
CMD ["python", "-u", "main.py"]