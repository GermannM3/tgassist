import asyncio
import logging
import sys
from os import getenv

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from bot.handlers import common, district, depth, equipment, order
from api.routes import prices, orders, analytics

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Создание lifespan контекстного менеджера
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Запуск бота при старте приложения
    bot_task = asyncio.create_task(start_bot())
    yield
    # Отмена задачи при остановке приложения
    bot_task.cancel()

# Создание экземпляра FastAPI
app = FastAPI(
    title="BurAssist API", 
    description="API для бота расчета стоимости бурения",
    lifespan=lifespan
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение маршрутов API
app.include_router(prices.router, prefix="/api/prices", tags=["prices"])
app.include_router(orders.router, prefix="/api/orders", tags=["orders"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])

# Функция запуска бота
async def start_bot():
    # Инициализация бота и диспетчера
    bot = Bot(token=getenv("BOT_TOKEN"))
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
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

# Запуск сервера
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=getenv("API_HOST", "0.0.0.0"),
        port=int(getenv("API_PORT", 8000)),
        reload=True
    )

