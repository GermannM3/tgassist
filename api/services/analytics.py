import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import Counter

def get_analytics_data(start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Получение аналитических данных по заказам
    """
    try:
        # Путь к файлу с заказами
        orders_file = os.path.join("data", "orders.json")
        
        # Проверка существования файла
        if not os.path.exists(orders_file):
            return {
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
                if start_datetime and order_date &lt; start_datetime:
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
        result = {
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
        
        return result
    
    except Exception as e:
        print(f"Ошибка при получении аналитических данных: {str(e)}")
        return {
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

