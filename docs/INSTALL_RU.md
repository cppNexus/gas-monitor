# Подробная инструкция по установке

## Содержание

1. [Системные требования](#системные-требования)
2. [Создание Telegram бота](#создание-telegram-бота)
3. [Локальная установка](#локальная-установка)
4. [Docker установка](#docker-установка)
5. [Настройка RPC endpoints](#настройка-rpc-endpoints)
6. [Проверка работы](#проверка-работы)
7. [Решение проблем](#решение-проблем)

---

## Системные требования

### Минимальные
- Python 3.9 или выше
- 512 MB RAM
- 1 GB свободного места на диске
- Стабильное интернет соединение

### Рекомендуемые
- Python 3.11
- 1 GB RAM
- 5 GB свободного места (для истории и графиков)
- VPS/Dedicated сервер для 24/7 работы

---

## Создание Telegram бота

### Шаг 1: Создание бота

1. Откройте Telegram и найдите [@BotFather](https://t.me/BotFather)
2. Отправьте команду `/newbot`
3. Придумайте имя для бота (например, "Gas Monitor Bot")
4. Придумайте username (например, "my_gas_monitor_bot")
5. Сохраните токен, который вам даст BotFather

Пример токена: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`

### Шаг 2: Получение Chat ID

**Способ 1 (простой):**
1. Найдите бота [@userinfobot](https://t.me/userinfobot)
2. Отправьте ему `/start`
3. Скопируйте ваш ID (например, `123456789`)

**Способ 2 (для группы):**
1. Добавьте вашего бота в группу
2. Откройте https://api.telegram.org/bot`YOUR_BOT_TOKEN`/getUpdates
3. Найдите `"chat":{"id":-123456789}` в ответе
4. Используйте это значение как chat_id

### Шаг 3: Проверка работы бота

```bash
# Замените YOUR_BOT_TOKEN и YOUR_CHAT_ID
curl "https://api.telegram.org/botYOUR_BOT_TOKEN/sendMessage?chat_id=YOUR_CHAT_ID&text=Test"
```

Если всё настроено правильно, вы получите тестовое сообщение.

---

## Локальная установка

### macOS / Linux

```bash
# 1. Клонируем репозиторий
git clone https://github.com/cppNexus/gas-monitor.git
cd gas-monitor

# 2. Создаем виртуальное окружение
python3 -m venv venv

# 3. Активируем окружение
source venv/bin/activate

# 4. Обновляем pip
pip install --upgrade pip

# 5. Устанавливаем зависимости
pip install -r requirements.txt

# 6. Создаем .env файл
cp .env.example .env

# 7. Редактируем .env
nano .env
# или
vim .env
# или используйте любой текстовый редактор

# 8. Создаем необходимые папки
mkdir -p logs charts data

# 9. Тестируем конфигурацию
python config.py

# 10. Запускаем мониторинг
python main.py
```

### Windows

```powershell
# 1. Клонируем репозиторий
git clone https://github.com/cppNexus/gas-monitor.git
cd gas-monitor

# 2. Создаем виртуальное окружение
python -m venv venv

# 3. Активируем окружение
venv\Scripts\activate

# 4. Обновляем pip
python -m pip install --upgrade pip

# 5. Устанавливаем зависимости
pip install -r requirements.txt

# 6. Создаем .env файл
copy .env.example .env

# 7. Редактируем .env в Notepad
notepad .env

# 8. Создаем папки
mkdir logs charts data

# 9. Тестируем конфигурацию
python config.py

# 10. Запускаем мониторинг
python main.py
```

---

## Docker установка

### Предварительные требования

```bash
# Проверьте установку Docker
docker --version
docker-compose --version
```

Если Docker не установлен:
- **Linux**: https://docs.docker.com/engine/install/
- **macOS**: https://docs.docker.com/desktop/install/mac-install/
- **Windows**: https://docs.docker.com/desktop/install/windows-install/

### Установка и запуск

```bash
# 1. Клонируем репозиторий
git clone https://github.com/cppNexus/gas-monitor.git
cd gas-monitor

# 2. Создаем .env файл
cp .env.example .env

# 3. Редактируем .env
nano .env

# 4. Собираем и запускаем
docker-compose up -d

# 5. Проверяем логи
docker-compose logs -f

# 6. Остановка
docker-compose down

# 7. Рестарт
docker-compose restart
```

### Полезные Docker команды

```bash
# Логи в реальном времени
docker-compose logs -f gas-monitor

# Последние 100 строк логов
docker-compose logs --tail=100 gas-monitor

# Вход в контейнер
docker-compose exec gas-monitor sh

# Перезапуск после изменения .env
docker-compose down
docker-compose up -d

# Полная очистка и пересборка
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## Настройка RPC endpoints

### Бесплатные публичные RPC

Проект использует публичные RPC по умолчанию:

- **Ethereum**: Ankr, LlamaRPC
- **Arbitrum**: Ankr, LlamaRPC
- **Optimism**: Ankr, LlamaRPC
- **Base**: Ankr, LlamaRPC
- **Polygon**: Ankr, LlamaRPC

### Рекомендуемые платные RPC (лучшая стабильность)

1. **Alchemy** (https://www.alchemy.com/)
   - Бесплатный tier: 300M compute units/месяц
   - Отличная документация

2. **Infura** (https://infura.io/)
   - Бесплатный tier: 100K requests/день
   - Простая регистрация

3. **QuickNode** (https://www.quicknode.com/)
   - Бесплатный trial
   - Высокая скорость

### Настройка своих RPC в .env

```env
# Ethereum
ETHEREUM_RPC=https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY
ETHEREUM_RPC_2=https://mainnet.infura.io/v3/YOUR_KEY

# Arbitrum
ARBITRUM_RPC=https://arb-mainnet.g.alchemy.com/v2/YOUR_KEY

# Optimism  
OPTIMISM_RPC=https://opt-mainnet.g.alchemy.com/v2/YOUR_KEY

# Base
BASE_RPC=https://base-mainnet.g.alchemy.com/v2/YOUR_KEY

# Polygon
POLYGON_RPC=https://polygon-mainnet.g.alchemy.com/v2/YOUR_KEY
```

---

## Дополнительные настройки .env

Если вы не хотите использовать Telegram-уведомления, отключите алерты:

```env
ENABLE_ALERTS=true
```

Настройка параметров графиков:

```env
CHART_WIDTH=14
CHART_HEIGHT=8
CHART_DPI=150
CHART_DIRECTORY=charts
```

---

## Проверка работы

### 1. Проверка конфигурации

```bash
python config.py
```

Вы должны увидеть:
```
Конфигурация успешно загружена
======================================================================
GAS MONITOR - КОНФИГУРАЦИЯ
======================================================================
Сети (5): ethereum, arbitrum, optimism, base, polygon
Telegram: Настроен
...
```

### 2. Тестовый запуск

```bash
python main.py
```

В течение 30-60 секунд вы должны увидеть:
- Подключение к сетям
- Получение данных о газе
- Запись в логи

### 3. Проверка Telegram алерта

Подождите до момента, когда газ упадет ниже порога, или временно увеличьте пороги в `.env`:

```env
# В config.py временно измените для теста:
gas_thresholds={
    "low": 1000,  # Большое значение для теста
    ...
}
```

### 4. Проверка графиков

После первого часа работы проверьте папку `charts/`:

```bash
ls -lh charts/
```

Вы должны увидеть файлы `.png` с графиками.

---

## Решение проблем

### Проблема: `ModuleNotFoundError`

**Решение:**
```bash
# Убедитесь что виртуальное окружение активно
which python  # должно показать путь в venv/

# Переустановите зависимости
pip install --upgrade -r requirements.txt
```

### Проблема: Telegram бот не отвечает

**Проверки:**
1. Правильность токена и chat ID
2. Бот не заблокирован
3. Для группы: бот добавлен как администратор

**Тест:**
```bash
curl "https://api.telegram.org/bot<TOKEN>/getMe"
```

### Проблема: RPC errors

**Симптомы:**
```
WARNING - HTTP 429 (ethereum), попытка 1
ERROR - RPC ошибка (ethereum): ...
```

**Решение:**
1. Используйте платные RPC endpoints
2. Увеличьте `CHECK_INTERVAL` в `.env`
3. Добавьте больше RPC endpoints

### Проблема: Высокое использование памяти

**Решение:**
```env
# Уменьшите историю
MAX_HISTORY_HOURS=12

# Отключите графики
ENABLE_CHARTS=false

# Увеличьте интервал
CHECK_INTERVAL=30
```

### Проблема: Docker контейнер падает

**Проверка:**
```bash
# Логи
docker-compose logs gas-monitor

# Статус
docker-compose ps

# Перезапуск
docker-compose restart
```

### Проблема: Графики не генерируются

**Проверка:**
```bash
# Проверьте matplotlib
python -c "import matplotlib; print(matplotlib.__version__)"

# Права на папку
ls -ld charts/
chmod 755 charts/

# Логи
grep -i "график" logs/gas_monitor.log
```

---

## Запуск как сервиса (Linux)

### systemd service

Создайте `/etc/systemd/system/gas-monitor.service`:

```ini
[Unit]
Description=Gas Monitor Service
After=network.target

[Service]
Type=simple
User=YOUR_USER
WorkingDirectory=/path/to/gas-monitor
Environment="PATH=/path/to/gas-monitor/venv/bin"
ExecStart=/path/to/gas-monitor/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Активация:
```bash
sudo systemctl daemon-reload
sudo systemctl enable gas-monitor
sudo systemctl start gas-monitor
sudo systemctl status gas-monitor
```

---

## Мониторинг работы

### Логи

```bash
# Реальное время
tail -f logs/gas_monitor.log

# Поиск ошибок
grep ERROR logs/gas_monitor.log

# Статистика
grep "Успешно:" logs/gas_monitor.log | tail -20
```

### Метрики

```bash
# Размер истории
du -sh data/

# Количество графиков
ls -1 charts/*.png | wc -l

# Использование памяти (если запущено)
ps aux | grep python
```

---

## Следующие шаги

1. Поставьте звезду на GitHub
2. Создайте issue если нашли баг
3. Contribute если есть идеи
4. Поделитесь проектом

---

**Нужна помощь?** Создайте issue на GitHub: https://github.com/cppNexus/gas-monitor/issues
