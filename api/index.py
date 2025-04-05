from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import sys
import os

# Добавляем корневую директорию в PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Импортируем ваше приложение из main.py
from main import app as main_app

# Создаем обработчик для Vercel
app = FastAPI()

@app.get("/api/health")
def health():
    return {"status": "ok"}

# Перенаправляем все запросы на основное приложение
@app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def catch_all(request: Request, path_name: str):
    return await main_app(request._request) 