# run_bot.py
import asyncio
import logging
import sys
from os import getenv

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from bot.handlers import common, district, depth, equipment, order

# Загрузка переменных окружения (на случай локального запуска)
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

async def main():
    # Инициализация бота и диспетчера
    bot_token = getenv("BOT_TOKEN")
    if not bot_token:
        logging.critical("Ошибка: Переменная окружения BOT_TOKEN не установлена!")
        return

    bot = Bot(token=bot_token)
    # Установка параметров по умолчанию
    bot.parse_mode = ParseMode.HTML
    dp = Dispatcher(storage=MemoryStorage())

    # Регистрация обработчиков
    dp.include_router(common.router)
    dp.include_router(district.router)
    dp.include_router(depth.router)
    dp.include_router(equipment.router)
    dp.include_router(order.router)

    # Запуск бота
    logging.info("Запуск бота в режиме polling...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот остановлен вручную.")
    except Exception as e:
        logging.critical(f"Критическая ошибка при запуске бота: {e}", exc_info=True) 