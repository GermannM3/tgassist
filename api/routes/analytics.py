from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import Counter

from bot.utils.pdf_generator import generate_analytics_pdf

# Создание роутера
router = APIRouter()

@router.get("/stats")
async def get_analytics_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Получение статистики по заказам за указанный период
    """
    try:
        # Путь к файлу с заказами
        orders_file = os.path.join("data", "orders.json")
        
        # Проверка существования файла
        if not os.path.exists(orders_file):
            return {
                "message": "Заказы не найдены",
                "stats": {
                    "total_orders": 0,
                    "popular_districts": [],
                    "popular_depths": [],
                    "popular_equipment": [],
                    "total_stats": {
                        "total_orders": 0,
                        "avg_order_cost": 0,
                        "total_revenue": 0,
                        "avg_depth": 0
                    }
                }
            }
        
        # Загрузка данных
        with open(orders_file, "r", encoding="utf-8") as file:
            data = json.load(file)
        
        orders = data.get("orders", [])
        
        # Фильтрация заказов по дате, если указаны даты
        if start_date or end_date:
            filtered_orders = []
            
            # Преобразование строк дат в объекты datetime
            start_datetime = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
            end_datetime = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1) if end_date else None
            
            for order in orders:
                order_date = datetime.strptime(order.get("order_date", "01.01.2000 00:00"), "%d.%m.%Y %H:%M")
                
                # Проверка условий фильтрации
                if start_datetime and order_date < start_datetime:
                    continue
                if end_datetime and order_date > end_datetime:
                    continue
                
                filtered_orders.append(order)
            
            orders = filtered_orders
        
        # Анализ данных
        
        # Популярные районы
        districts = [order.get("district_name", "Неизвестный район") for order in orders]
        district_counter = Counter(districts)
        popular_districts = [{"name": district, "count": count} for district, count in district_counter.most_common()]
        
        # Популярные глубины
        depths = [order.get("depth", 0) for order in orders]
        depth_counter = Counter(depths)
        popular_depths = [{"depth": depth, "count": count} for depth, count in depth_counter.most_common()]
        
        # Популярное оборудование
        equipment_list = []
        for order in orders:
            selected_equipment = order.get("selected_equipment", {})
            for category, components in selected_equipment.items():
                for component in components:
                    equipment_list.append(component)
        
        equipment_counter = Counter(equipment_list)
        popular_equipment = [{"name": equipment, "count": count} for equipment, count in equipment_counter.most_common(10)]
        
        # Общая статистика
        total_orders = len(orders)
        total_revenue = sum(order.get("total_cost", 0) for order in orders)
        avg_order_cost = total_revenue / total_orders if total_orders > 0 else 0
        avg_depth = sum(depths) / len(depths) if depths else 0
        
        # Формирование результата
        stats = {
            "total_orders": total_orders,
            "popular_districts": popular_districts,
            "popular_depths": popular_depths,
            "popular_equipment": popular_equipment,
            "total_stats": {
                "total_orders": total_orders,
                "avg_order_cost": round(avg_order_cost, 2),
                "total_revenue": total_revenue,
                "avg_depth": round(avg_depth, 2)
            }
        }
        
        return {"stats": stats}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pdf")
async def get_analytics_pdf(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Получение PDF-отчета с аналитикой
    """
    try:
        # Получение статистики
        stats_response = await get_analytics_stats(start_date, end_date)
        stats = stats_response.get("stats", {})
        
        # Генерация PDF с аналитикой
        pdf_path = generate_analytics_pdf(stats)
        
        # Отправка файла
        return FileResponse(
            path=pdf_path,
            filename=f"analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            media_type="application/pdf"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/popular-districts")
async def get_popular_districts():
    """
    Получение списка популярных районов
    """
    try:
        # Получение общей статистики
        stats_response = await get_analytics_stats()
        stats = stats_response.get("stats", {})
        
        # Извлечение данных о популярных районах
        popular_districts = stats.get("popular_districts", [])
        
        return {"popular_districts": popular_districts}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/popular-depths")
async def get_popular_depths():
    """
    Получение списка популярных глубин
    """
    try:
        # Получение общей статистики
        stats_response = await get_analytics_stats()
        stats = stats_response.get("stats", {})
        
        # Извлечение данных о популярных глубинах
        popular_depths = stats.get("popular_depths", [])
        
        return {"popular_depths": popular_depths}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/popular-equipment")
async def get_popular_equipment():
    """
    Получение списка популярного оборудования
    """
    try:
        # Получение общей статистики
        stats_response = await get_analytics_stats()
        stats = stats_response.get("stats", {})
        
        # Извлечение данных о популярном оборудовании
        popular_equipment = stats.get("popular_equipment", [])
        
        return {"popular_equipment": popular_equipment}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

