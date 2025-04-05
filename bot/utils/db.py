import json
import os
from typing import Dict, Any, List, Optional
import aiofiles

class JsonDB:
    """
    Класс для работы с JSON-файлами как с базой данных
    """
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
    
    async def read_json(self, filename: str) -> Dict[str, Any]:
        """
        Чтение данных из JSON-файла
        """
        file_path = os.path.join(self.data_dir, filename)
        
        # Проверка существования файла
        if not os.path.exists(file_path):
            return {}
        
        # Чтение данных
        async with aiofiles.open(file_path, "r", encoding="utf-8") as file:
            content = await file.read()
            return json.loads(content)
    
    async def write_json(self, filename: str, data: Dict[str, Any]) -> bool:
        """
        Запись данных в JSON-файл
        """
        file_path = os.path.join(self.data_dir, filename)
        
        try:
            # Запись данных
            async with aiofiles.open(file_path, "w", encoding="utf-8") as file:
                await file.write(json.dumps(data, ensure_ascii=False, indent=4))
            return True
        except Exception as e:
            print(f"Ошибка при записи в файл {filename}: {str(e)}")
            return False
    
    async def get_districts(self) -> List[Dict[str, Any]]:
        """
        Получение списка районов
        """
        data = await self.read_json("districts.json")
        return data.get("districts", [])
    
    async def get_district_by_id(self, district_id: int) -> Optional[Dict[str, Any]]:
        """
        Получение района по ID
        """
        districts = await self.get_districts()
        return next((d for d in districts if d.get("id") == district_id), None)
    
    async def get_equipment(self) -> Dict[str, Any]:
        """
        Получение данных об оборудовании
        """
        return await self.read_json("equipment.json")
    
    async def get_orders(self) -> List[Dict[str, Any]]:
        """
        Получение списка заказов
        """
        data = await self.read_json("orders.json")
        return data.get("orders", [])
    
    async def get_user_orders(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Получение заказов пользователя
        """
        orders = await self.get_orders()
        return [order for order in orders if order.get("user_id") == user_id]
    
    async def add_order(self, order_data: Dict[str, Any]) -> bool:
        """
        Добавление нового заказа
        """
        data = await self.read_json("orders.json")
        orders = data.get("orders", [])
        orders.append(order_data)
        data["orders"] = orders
        return await self.write_json("orders.json", data)
    
    async def update_equipment_price(self, category: str, component: str, price: float) -> bool:
        """
        Обновление цены на компонент оборудования
        """
        data = await self.read_json("equipment.json")
        equipment_data = data.get("equipment_data", {})
        
        if category not in equipment_data:
            equipment_data[category] = {}
        
        equipment_data[category][component] = price
        data["equipment_data"] = equipment_data
        
        return await self.write_json("equipment.json", data)
    
    async def update_district_price(self, district_id: int, base_price: float) -> bool:
        """
        Обновление базовой цены для района
        """
        data = await self.read_json("districts.json")
        districts = data.get("districts", [])
        
        for district in districts:
            if district.get("id") == district_id:
                district["base_price"] = base_price
                break
        
        data["districts"] = districts
        return await self.write_json("districts.json", data)

