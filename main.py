#!/usr/bin/env python3
"""
Точка входа в Gas Monitor.
Запускает мониторинг газа и управляет жизненным циклом приложения.
"""

import asyncio
import signal
import sys
import logging
from typing import Optional

# Импорты из нашего проекта
from src.config import config
from src.monitor import GasMonitor
from src.alerting import AlertManager
from src.charts import ChartGenerator

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, config.logging.level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(config.logging.file_path)
    ]
)
logger = logging.getLogger(__name__)

class Application:
    """Главное приложение"""
    
    def __init__(self):
        self.monitor: Optional[GasMonitor] = None
        self.alert_manager: Optional[AlertManager] = None
        self.chart_generator: Optional[ChartGenerator] = None
        
        # Флаг для graceful shutdown
        self.should_stop = False
    
    async def init(self):
        """Инициализация приложения"""
        logger.info("Инициализация Gas Monitor")
        
        # Выводим сводку конфигурации
        config.print_summary()
        
        # Инициализируем компоненты
        self.alert_manager = AlertManager()
        self.chart_generator = ChartGenerator()
        
        # Инициализируем монитор (L2 калькулятор инициализируется внутри)
        self.monitor = GasMonitor(
            alert_manager=self.alert_manager,
            chart_generator=self.chart_generator
        )
        
        # Регистрируем обработчики сигналов
        self._register_signal_handlers()
        
        logger.info("Инициализация завершена")
    
    def _register_signal_handlers(self):
        """Регистрация обработчиков сигналов для graceful shutdown"""
        loop = asyncio.get_event_loop()
        
        if sys.platform != "win32":
            # только на *nix
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(
                    sig,
                    lambda s=sig: asyncio.create_task(self.shutdown(s))
                )
            logger.debug("Обработчики сигналов зарегистрированы")
        else:
            logger.debug("Регистрация сигналов пропущена на Windows")
    
    async def run(self):
        """Запуск основного цикла приложения"""
        if not self.monitor:
            logger.error("Монитор не инициализирован")
            return
        
        try:
            logger.info("Запуск мониторинга...")
            await self.monitor.run()
        except asyncio.CancelledError:
            logger.info("Мониторинг отменен")
        except Exception as e:
            logger.error(f"Ошибка в основном цикле: {e}")
            raise
    
    async def shutdown(self, sig=None):
        """Корректное завершение работы"""
        if self.should_stop:
            return
        
        self.should_stop = True
        signal_name = signal.Signals(sig).name if sig else "MANUAL"
        logger.info(f"Получен сигнал {signal_name}, завершение работы...")
        
        # Останавливаем монитор
        if self.monitor:
            await self.monitor.stop()
        
        # Останавливаем другие компоненты
        if self.alert_manager:
            await self.alert_manager.cleanup()
        
        if self.chart_generator:
            await self.chart_generator.cleanup()
        
        logger.info("Завершение работы успешно")
        
        # Останавливаем event loop
        loop = asyncio.get_event_loop()
        pass

async def main():
    """Главная функция"""
    app = Application()
    
    try:
        await app.init()
        await app.run()
    except KeyboardInterrupt:
        logger.info("Прервано пользователем")
        await app.shutdown()
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        await app.shutdown()
        raise

if __name__ == "__main__":
    # Проверка Python версии
    if sys.version_info < (3, 9):
        print("Требуется Python 3.9 или выше")
        sys.exit(1)
    
    # Запуск приложения
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nДо свидания!")
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        sys.exit(1)