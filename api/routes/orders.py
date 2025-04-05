from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse
import json
import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from bot.utils.pdf_generator import generate_order_pdf

# Модели данных
class OrderStatus(BaseModel):
    order_id: str
    status: str

# Создание роутера
router = APIRouter()

@router.get("/all")
async def get_all_orders(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = None
):
    """
    Получение списка всех заказов с пагинацией и фильтрацией по статусу
    """
    try:
        # Путь к файлу с заказами
        orders_file = os.path.join("data", "orders.json")
        
        # Проверка существования файла
        if not os.path.exists(orders_file):
            return {"orders": [], "total": 0}
        
        # Загрузка данных
        with open(orders_file, "r", encoding="utf-8") as file:
            data = json.load(file)
        
        orders = data.get("orders", [])
        
        # Фильтрация по статусу, если указан
        if status:
            orders = [order for order in orders if order.get("status") == status]
        
        # Общее количество заказов после фильтрации
        total = len(orders)
        
        # Сортировка заказов по дате (от новых к старым)
        orders.sort(
            key=lambda x: datetime.strptime(x.get("order_date", "01.01.2000 00:00"), "%d.%m.%Y %H:%M"),
            reverse=True
        )
        
        # Применение пагинации
        paginated_orders = orders[offset:offset + limit]
        
        return {"orders": paginated_orders, "total": total}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}")
async def get_user_orders(user_id: int):
    """
    Получение заказов конкретного пользователя
    """
    try:
        # Путь к файлу с заказами
        orders_file = os.path.join("data", "orders.json")
        
        # Проверка существования файла
        if not os.path.exists(orders_file):
            return {"orders": []}
        
        # Загрузка данных
        with open(orders_file, "r", encoding="utf-8") as file:
            data = json.load(file)
        
        # Фильтрация заказов пользователя
        user_orders = [order for order in data.get("orders", []) if order.get("user_id") == user_id]
        
        # Сортировка заказов по дате (от новых к старым)
        user_orders.sort(
            key=lambda x: datetime.strptime(x.get("order_date", "01.01.2000 00:00"), "%d.%m.%Y %H:%M"),
            reverse=True
        )
        
        return {"orders": user_orders}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/order/{order_id}")
async def get_order_details(order_id: str):
    """
    Получение деталей конкретного заказа
    """
    try:
        # Путь к файлу с заказами
        orders_file = os.path.join("data", "orders.json")
        
        # Проверка существования файла
        if not os.path.exists(orders_file):
            return JSONResponse(
                status_code=404,
                content={"message": "Заказы не найдены"}
            )
        
        # Загрузка данных
        with open(orders_file, "r", encoding="utf-8") as file:
            data = json.load(file)
        
        # Поиск заказа по ID
        order = next((order for order in data.get("orders", []) if order.get("order_id") == order_id), None)
        
        if not order:
            return JSONResponse(
                status_code=404,
                content={"message": f"Заказ с ID {order_id} не найден"}
            )
        
        return order
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-status")
async def update_order_status(order_status: OrderStatus):
    """
    Обновление статуса заказа
    """
    try:
        # Путь к файлу с заказами
        orders_file = os.path.join("data", "orders.json")
        
        # Проверка существования файла
        if not os.path.exists(orders_file):
            return JSONResponse(
                status_code=404,
                content={"message": "Заказы не найдены"}
            )
        
        # Загрузка данных
        with open(orders_file, "r", encoding="utf-8") as file:
            data = json.load(file)
        
        # Поиск заказа по ID
        order_found = False
        for order in data.get("orders", []):
            if order.get("order_id") == order_status.order_id:
                order["status"] = order_status.status
                order_found = True
                break
        
        if not order_found:
            return JSONResponse(
                status_code=404,
                content={"message": f"Заказ с ID {order_status.order_id} не найден"}
            )
        
        # Сохранение обновленных данных
        with open(orders_file, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        
        return {"message": "Статус заказа успешно обновлен"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pdf/{order_id}")
async def get_order_pdf(order_id: str):
    """
    Получение PDF-файла с деталями заказа
    """
    try:
        # Путь к файлу с заказами
        orders_file = os.path.join("data", "orders.json")
        
        # Проверка существования файла
        if not os.path.exists(orders_file):
            raise HTTPException(status_code=404, detail="Заказы не найдены")
        
        # Загрузка данных
        with open(orders_file, "r", encoding="utf-8") as file:
            data = json.load(file)
        
        # Поиск заказа по ID
        order = next((order for order in data.get("orders", []) if order.get("order_id") == order_id), None)
        
        if not order:
            raise HTTPException(status_code=404, detail=f"Заказ с ID {order_id} не найден")
        
        # Путь к PDF-файлу
        pdf_path = os.path.join("data", "pdf", f"order_{order_id}.pdf")
        
        # Проверка существования PDF-файла
        if not os.path.exists(pdf_path):
            # Генерация PDF, если файл не существует
            pdf_path = generate_order_pdf(order)
        
        # Отправка файла
        return FileResponse(
            path=pdf_path,
            filename=f"order_{order_id}.pdf",
            media_type="application/pdf"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

