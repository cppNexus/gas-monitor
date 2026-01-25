# Gas Monitor

**Профессиональный мониторинг цен на газ с уведомлениями в Telegram и графиками**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[Возможности](#возможности) • [Установка](#быстрый-старт) • [Настройка](#настройка) • [Документация](#документация)

---

## Возможности

**Поддержка нескольких сетей**
- Одновременный мониторинг 5 сетей: Ethereum, Arbitrum, Optimism, Base и Polygon
- Автоматическое переключение между несколькими RPC endpoint'ами
- Индивидуальные пороги для каждой сети

**Умные уведомления**
- Telegram-оповещения при снижении цены газа ниже порогов
- Настраиваемый интервал между повторными алертами
- Подробные сообщения с данными о сети, номерами блоков и рекомендациями
- Несколько уровней алертов: ultra_low, low, medium, high, ultra_high

**Визуализация данных**
- Автоматически генерируемые графики с историческими трендами
- Отдельные графики для базовых комиссий, приоритетных комиссий и общих сумм
- Настраиваемые интервалы обновления и периоды хранения
- Поддержка нескольких процентилей (p10, p25, p50, p75, p90)

**Технические возможности**
- Поддержка EIP-1559 транзакций с отслеживанием базовой и приоритетной комиссий
- Специальные расчеты для L2 сетей Arbitrum, Optimism и Base
- Асинхронная архитектура для оптимальной производительности
- Подробное логирование с ротацией
- Поддержка Docker для простого развертывания
- Корректное завершение работы

## Быстрый старт

### Требования

- Python 3.9 или выше
- Токен Telegram бота и chat ID
- RPC endpoints (включены бесплатные публичные)

### Локальная установка

```bash
# Клонировать репозиторий
git clone https://github.com/cppNexus/gas-monitor.git
cd gas-monitor

# Создать виртуальное окружение
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Установить зависимости
pip install -r requirements.txt

# Настроить
cp .env.example .env
nano .env  # Добавить ваши настройки

# Запустить
python main.py
```

### Установка через Docker

```bash
# Клонировать репозиторий
git clone https://github.com/cppNexus/gas-monitor.git
cd gas-monitor

# Настроить
cp .env.example .env
nano .env

# Запустить
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановить
docker-compose down
```

## Настройка

### Настройка Telegram

1. Создать бота через [@BotFather](https://t.me/BotFather)
   - Отправить `/newbot`
   - Выбрать имя и username
   - Сохранить токен

2. Получить chat ID через [@userinfobot](https://t.me/userinfobot)
   - Отправить `/start`
   - Скопировать ID

3. Добавить в `.env`:
```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
```

### RPC Endpoints

Проект включает бесплатные публичные RPC endpoints. Для лучшей надежности используйте свои:

```env
# Ethereum
ETHEREUM_RPC_1=https://eth.llamarpc.com
ETHEREUM_RPC_2=https://ethereum.publicnode.com

# Arbitrum
ARBITRUM_RPC_1=https://arb1.arbitrum.io/rpc
ARBITRUM_RPC_2=https://arbitrum.publicnode.com

# Optimism
OPTIMISM_RPC_1=https://mainnet.optimism.io
OPTIMISM_RPC_2=https://optimism.publicnode.com

# Base
BASE_RPC_1=https://mainnet.base.org
BASE_RPC_2=https://base.publicnode.com

# Polygon
POLYGON_RPC_1=https://polygon-rpc.com
POLYGON_RPC_2=https://polygon.publicnode.com
```

**Рекомендуемые провайдеры** (доступны бесплатные тарифы):
- [Alchemy](https://www.alchemy.com/) - 300M compute units/месяц
- [Infura](https://infura.io/) - 100K запросов/день
- [QuickNode](https://www.quicknode.com/) - Бесплатный trial

### Пороги алертов

Пороги по умолчанию настроены в `config.py`. Можно настроить для каждой сети:

**Ethereum:**
- ultra_low: 15 Gwei
- low: 20 Gwei
- medium: 35 Gwei
- high: 50 Gwei
- ultra_high: 100 Gwei

**L2 сети (Arbitrum, Optimism, Base):**
- low: 0.1 Gwei
- medium: 0.3 Gwei
- high: 1.0 Gwei

### Настройки мониторинга

```env
CHECK_INTERVAL=12           # Секунд между проверками
ALERT_COOLDOWN=300         # Секунд между повторными алертами
MAX_HISTORY_HOURS=24       # Часов хранения данных
ENABLE_ALERTS=true         # Включить/выключить Telegram алерты
ENABLE_CHARTS=true         # Генерировать графики
CHART_UPDATE_INTERVAL=3600 # Секунд между обновлениями графиков
CHART_WIDTH=14             # Ширина графика (дюймы)
CHART_HEIGHT=8             # Высота графика (дюймы)
CHART_DPI=150              # Разрешение графика
CHART_DIRECTORY=charts     # Папка для графиков
```

## Использование

### Локальный запуск

```bash
# Активировать виртуальное окружение
source venv/bin/activate

# Запустить мониторинг
python main.py

# Остановить с помощью Ctrl+C
```

### Запуск через Docker

```bash
# Запустить в фоне
docker-compose up -d

# Просмотр логов
docker-compose logs -f gas-monitor

# Перезапуск
docker-compose restart

# Остановка
docker-compose down

# Обновление и перезапуск
git pull
docker-compose down
docker-compose build
docker-compose up -d
```

### Как системный сервис (Linux)

Создать `/etc/systemd/system/gas-monitor.service`:

```ini
[Unit]
Description=Gas Monitor Service
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/gas-monitor
Environment="PATH=/path/to/gas-monitor/venv/bin"
ExecStart=/path/to/gas-monitor/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Активировать и запустить:
```bash
sudo systemctl daemon-reload
sudo systemctl enable gas-monitor
sudo systemctl start gas-monitor
sudo systemctl status gas-monitor
```

## Хранение данных

### Исторические данные
- Хранятся в `data/history_backup.json`
- Автоматическое сохранение каждые 5 минут
- Настраиваемый период хранения

### Графики
- Генерируются в директории `charts/`
- Обновляются ежечасно по умолчанию
- Автоматическая очистка старых графиков
- Формат PNG, настраиваемый DPI

### Логи
- Вывод в консоль и файл
- Ротация файлов (макс. 10MB, 5 бэкапов)
- Настраиваемый уровень логирования (DEBUG, INFO, WARNING, ERROR)
- Расположение: `logs/gas_monitor.log`

## Структура проекта

```
gas-monitor/
│
├── main.py                  # Точка входа приложения
│
├── src/                     # Исходный код
│   ├── config.py           # Управление конфигурацией
│   ├── monitor.py          # Основная логика мониторинга
│   ├── models.py           # Модели данных
│   ├── alerting.py         # Telegram уведомления
│   ├── charts.py           # Генерация графиков
│   ├── l2_calculator.py    # Расчет L2 комиссий
│   └── sniper.py           # Снайпер транзакций (опционально)
│
├── docs/                    # Документация
│   ├── README.ru.md        # Документация на русском
│   └── INSTALL.ru.md       # Инструкция по установке на русском
│
├── logs/                    # Логи (создается автоматически)
│   └── gas_monitor.log     # Основной лог-файл
│
├── charts/                  # Графики (создается автоматически)
│   ├── ethereum_gas_trend.png
│   ├── arbitrum_gas_trend.png
│   └── ...
│
├── data/                    # Данные (создается автоматически)
│   └── history_backup.json # Бэкап исторических данных
│
├── requirements.txt         # Зависимости Python
├── Dockerfile              # Docker образ
├── docker-compose.yml      # Docker Compose конфигурация
├── .env.example            # Шаблон переменных окружения
├── .gitignore             # Правила игнорирования Git
├── .dockerignore          # Правила игнорирования Docker
├── LICENSE                # Лицензия MIT
├── README.md              # Документация на английском
└── INSTALL.md             # Инструкция по установке на английском
```

### Описание директорий

**src/** - Основной код приложения
- `config.py` - Загрузка и валидация конфигурации из .env
- `monitor.py` - Мониторинг цен на газ для всех сетей
- `models.py` - Модели данных (GasData и др.)
- `alerting.py` - Отправка уведомлений в Telegram
- `charts.py` - Генерация графиков с matplotlib
- `l2_calculator.py` - Расчет L1 комиссий для L2 сетей
- `sniper.py` - Автоматические транзакции (экспериментально)

**docs/** - Документация проекта
- Инструкции по установке
- Руководства пользователя
- API документация

**logs/** - Файлы логов
- Автоматически создается при первом запуске
- Ротация логов настроена (10MB макс, 5 бэкапов)

**charts/** - Сгенерированные графики
- PNG файлы с трендами цен на газ
- Автоматическая очистка старых графиков

**data/** - Данные приложения
- История цен на газ
- Бэкапы конфигурации
- Кэш данных

## Решение проблем

### Ошибки подключения к RPC

**Проблема:** Ошибки `ClientConnectorDNSError` или `Unauthorized`

**Решение:**
1. Проверить RPC endpoints в `.env`
2. Использовать альтернативных провайдеров (см. раздел Настройка)
3. Проверить сетевое подключение

### Не приходят Telegram уведомления

**Проблема:** Бот не отправляет сообщения

**Решение:**
1. Проверить `TELEGRAM_BOT_TOKEN` и `TELEGRAM_CHAT_ID`
2. Протестировать бота: `curl "https://api.telegram.org/bot<TOKEN>/getMe"`
3. Убедиться что бот не заблокирован
4. Для групп добавить бота как администратора

### Пустые графики

**Проблема:** Графики пустые или не показывают данные

**Решение:**
1. Подождать 30-60 минут для накопления данных
2. Проверить логи на наличие ошибок
3. Убедиться что `ENABLE_CHARTS=true` в `.env`

### Высокое потребление памяти

**Проблема:** Монитор потребляет слишком много RAM

**Решение:**
```env
MAX_HISTORY_HOURS=12    # Уменьшить историю
ENABLE_CHARTS=false     # Отключить графики
CHECK_INTERVAL=30       # Увеличить интервал
```

## Разработка

### Настройка окружения разработки

```bash
# Клонировать репозиторий
git clone https://github.com/cppNexus/gas-monitor.git
cd gas-monitor

# Создать виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt

# Запустить тесты
python config.py  # Тест конфигурации
python main.py    # Полный тест
```

### Стиль кода

- Следовать PEP 8
- Использовать type hints где возможно
- Документировать функции с docstrings
- Держать функции короче 50 строк

### Добавление новых сетей

1. Добавить конфигурацию сети в `config.py`:
```python
networks["new_network"] = NetworkConfig(
    name="New Network",
    chain_id=123,
    native_token="TOKEN",
    is_l2=False,
    supports_eip1559=True,
    block_time=12,
    explorer_url="https://explorer.example.com",
    gas_thresholds={"low": 10, "medium": 20, "high": 50}
)
```

2. Добавить RPC endpoints в `.env.example`
3. Протестировать с помощью `python main.py`

## Безопасность

### Лучшие практики

- Никогда не коммитить `.env` файл в git
- Использовать переменные окружения для секретов
- Держать зависимости обновленными
- Использовать отдельный кошелек для снайпера (если включен)
- Включить 2FA на аккаунте Telegram

### Предупреждение о снайпере

Модуль снайпера экспериментальный и отключен по умолчанию. Если вы его включаете:
- ВСЕГДА используйте `dry_run=true` для тестирования
- Никогда не храните приватные ключи в коде
- Используйте отдельный кошелек с минимальными средствами
- Понимайте риски автоматических транзакций

## Модуль снайпера

Модуль снайпера позволяет автоматически отправлять транзакции при снижении цен на газ ниже целевых уровней. Это продвинутая функция для опытных пользователей.

### Возможности

- Автоматическая отправка транзакций при низких ценах на газ
- Поддержка EIP-1559 транзакций
- Управление nonce с предотвращением коллизий
- Симуляция транзакций перед отправкой
- Система подтверждений для безопасности
- Режим dry-run для тестирования
- Проверка баланса
- Оценка газа
- Множественные проверки безопасности

### Настройка

**Включение снайпера:**
```env
ENABLE_SNIPER=false              # Установить true для включения
SNIPER_DRY_RUN=true              # ВСЕГДА true для тестирования
SNIPER_REQUIRE_CONFIRMATION=true # Требовать ручного подтверждения
SNIPER_CONFIRMATION_TTL=30       # Секунд на подтверждение
SNIPER_MAX_GAS_MULTIPLIER=1.2    # Макс. множитель цены газа
SNIPER_MIN_PROFIT_GWEI=5.0       # Минимальная прибыль в Gwei
```

**КРИТИЧНО: Никогда не устанавливайте приватный ключ в .env файле!**

### Пример использования

```python
from sniper import get_sniper

# Инициализировать снайпер
sniper = await get_sniper(network="ethereum")

# Установить приватный ключ (ДЕЛАЙТЕ ЭТО БЕЗОПАСНО!)
# Только для тестирования - используйте аппаратный кошелек в продакшене
sniper.set_private_key("YOUR_PRIVATE_KEY")

# Проверить баланс
balance = await sniper.get_balance()
print(f"Баланс: {balance} ETH")

# Подготовить транзакцию
tx = await sniper.prepare_transaction(
    to_address="0x...",
    value_eth=0.01,
    gas_limit=21000
)

# Сначала симуляция
success, error = await sniper.simulate_transaction(tx)
if success:
    # Отправить транзакцию (в режиме dry-run не отправит реально)
    tx_hash = await sniper.send_transaction(tx)
    
    # Дождаться подтверждения
    if tx_hash:
        confirmed = await sniper.wait_for_transaction(tx_hash)
        print(f"Транзакция подтверждена: {confirmed}")
```

### Режим Dry-Run

В режиме dry-run (по умолчанию) снайпер будет:
- Подготавливать транзакции
- Симулировать выполнение
- Логировать все детали
- НЕ отправлять транзакции в сеть

Это позволяет безопасно тестировать без риска для средств.

### Функции безопасности

1. **Управление Nonce**: Автоматическое отслеживание nonce предотвращает коллизии транзакций
2. **Оценка газа**: Расчет оптимальных лимитов газа
3. **Симуляция**: Тестирование транзакции перед отправкой
4. **Система подтверждений**: Требует ручного одобрения для каждой транзакции
5. **Проверка баланса**: Проверяет достаточность средств перед отправкой
6. **Периоды ожидания**: Предотвращает спам транзакций
7. **Восстановление ошибок**: Автоматический сброс nonce при ошибках

### Использование в продакшене

Для использования в продакшене с реальными средствами:

1. **Используйте аппаратный кошелек**
   - Рекомендуется Ledger или Trezor
   - Никогда не раскрывайте приватные ключи

2. **Отдельный кошелек**
   - Создайте отдельный кошелек для снайпера
   - Держите минимум средств (только то, что планируете использовать)

3. **Тщательное тестирование**
   - Запускайте в режиме dry-run несколько дней
   - Сначала тестируйте на testnet
   - Проверьте всю логику

4. **Постоянный мониторинг**
   - Следите за логами в реальном времени
   - Настройте алерты на ошибки
   - Имейте готовый kill switch

5. **Чеклист безопасности**
   - [ ] Используется аппаратный кошелек или безопасное управление ключами
   - [ ] Тщательно протестировано в режиме dry-run
   - [ ] Отдельный кошелек с минимальными средствами
   - [ ] Настроен мониторинг и алерты
   - [ ] Понимание всех рисков
   - [ ] Готова процедура экстренной остановки

### Примеры сценариев

**Сценарий 1: Минт NFT**
```python
# Когда газ падает ниже 20 Gwei, минтим NFT
if current_gas < 20:
    tx = await sniper.prepare_transaction(
        to_address="0xNFTContract",
        value_eth=0.08,  # Цена минта
        data="0x...",    # Вызов функции минта
        gas_limit=150000
    )
    await sniper.send_transaction(tx)
```

**Сценарий 2: Обмен токенов**
```python
# Выполнить обмен когда газ оптимален
if current_gas < target_gas:
    tx = await sniper.prepare_transaction(
        to_address="0xUniswapRouter",
        data="0x...",  # Calldata для свапа
        gas_limit=200000
    )
    await sniper.send_transaction(tx)
```

**Сценарий 3: Арбитраж**
```python
# Проверить возможность и прибыль
opportunity, profit = await sniper.check_opportunity(
    current_gas_price=current_gas,
    target_gas_price=target_gas
)

if opportunity and profit > sniper.config.min_profit_gwei:
    # Выполнить арбитраж
    tx = await sniper.prepare_transaction(...)
    await sniper.send_transaction(tx)
```

### Ограничения

- Не гарантирует включение транзакции
- Зависит от загруженности сети
- Существует риск фронтраннинга
- Цена газа может измениться между подготовкой и отправкой
- Проскальзывание на DEX сделках

### Решение проблем снайпера

**Проблема: Транзакция падает с "nonce too low"**
```python
# Сбросить nonce manager
sniper.nonce_manager.reset_nonce()
```

**Проблема: Оценка газа не работает**
```python
# Использовать ручной лимит газа
tx = await sniper.prepare_transaction(
    ...,
    gas_limit=300000  # Установить вручную
)
```

**Проблема: Транзакция висит в pending слишком долго**
```python
# Увеличить множитель цены газа
# В .env:
SNIPER_MAX_GAS_MULTIPLIER=1.5
```

### Правовая оговорка

**ИСПОЛЬЗУЙТЕ НА СВОЙ РИСК**

Модуль снайпера предоставляется как есть без гарантий. Пользователи несут ответственность за:
- Понимание рисков смарт-контрактов
- Соблюдение местного законодательства
- Безопасность приватных ключей
- Безопасное управление средствами

Авторы не несут ответственности за любые потери, понесенные при использовании этого ПО.

## FAQ

**В: Сколько сетей можно мониторить одновременно?**
О: Все 5 сетей (Ethereum, Arbitrum, Optimism, Base, Polygon) работают параллельно.

**В: Каковы системные требования?**
О: Минимум 512MB RAM, 1GB диска. Рекомендуется: 1GB RAM, 5GB диска для долгосрочной истории.

**В: Можно ли мониторить только определенные сети?**
О: Да, просто не настраивайте RPC endpoints для ненужных сетей в `.env`.

**В: Насколько точны прогнозы газа?**
О: Используются реальные on-chain данные из `eth_feeHistory`. Точность зависит от условий сети и надежности RPC.

**В: Можно ли запустить несколько экземпляров?**
О: Да, используйте разные `.env` файлы и Telegram ботов для каждого экземпляра.

**В: Работает ли на Windows?**
О: Да, но для продакшена рекомендуется Docker.

## Производительность

**Типичное использование ресурсов:**
- CPU: <5% на современных процессорах
- RAM: 50-200MB в зависимости от размера истории
- Сеть: ~1-5 KB/с на сеть
- Диск: ~100MB для 24ч истории

**Советы по оптимизации:**
- Использовать локальные RPC ноды для лучшей производительности
- Увеличить `CHECK_INTERVAL` для снижения нагрузки
- Отключить графики если не нужны
- Использовать SSD для быстрого I/O

## Вклад в проект

Вклад приветствуется! Пожалуйста:

1. Сделать Fork репозитория
2. Создать feature ветку (`git checkout -b feature/AmazingFeature`)
3. Закоммитить изменения (`git commit -m 'Add AmazingFeature'`)
4. Запушить в ветку (`git push origin feature/AmazingFeature`)
5. Открыть Pull Request

### Правила для контрибьюторов

- Следовать существующему стилю кода
- Добавлять тесты для новых функций
- Обновлять документацию
- Держать коммиты атомарными и хорошо описанными

## Дорожная карта

- [ ] Поддержка дополнительных L2 сетей (zkSync, Polygon zkEVM)
- [ ] Веб-панель для просмотра графиков
- [ ] База данных для долгосрочного хранения
- [ ] Интеграция с Discord
- [ ] Мобильное приложение
- [ ] Прогнозы цен на газ с ML
- [ ] Мультиязычная поддержка
- [ ] RESTful API

## Лицензия

Этот проект лицензирован под MIT License - см. файл [LICENSE](LICENSE) для деталей.

## Благодарности

- [Web3.py](https://github.com/ethereum/web3.py) - Библиотека Ethereum для Python
- [aiohttp](https://github.com/aio-libs/aiohttp) - Async HTTP клиент/сервер
- [matplotlib](https://matplotlib.org/) - Генерация графиков

## Поддержка

- Issues: [GitHub Issues](https://github.com/cppNexus/gas-monitor/issues)
- Обсуждения: [GitHub Discussions](https://github.com/cppNexus/gas-monitor/discussions)
- Email: cppnexus@proton.me
