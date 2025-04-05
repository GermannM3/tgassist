import PyPDF2
import re
import os
import json
from typing import Dict, Any, List, Tuple

def parse_pdf_prices(pdf_path: str) -> Dict[str, Any]:
    """
    Парсинг цен из PDF-файла
    """
    try:
        # Открытие PDF-файла
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            
            # Извлечение текста из всех страниц
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        
        # Поиск цен и оборудования в тексте
        # Это упрощенный пример, в реальном приложении нужно адаптировать регулярные выражения
        # под конкретный формат PDF-файла с ценами
        
        # Поиск оборудования и цен
        equipment_pattern = r"([А-Яа-я\s№]+):\s*(\d+(?:\s*\d+)*)\s*₽"
        equipment_matches = re.findall(equipment_pattern, text)
        
        # Поиск районов и базовых цен
        district_pattern = r"([А-Яа-я\s]+округ)[\s\-]*(\d+(?:\s*\d+)*)\s*₽/м"
        district_matches = re.findall(district_pattern, text)
        
        # Формирование результата
        result = {
            "equipment_data": {},
            "districts_data": []
        }
        
        # Обработка найденного оборудования
        for name, price in equipment_matches:
            name = name.strip()
            price = int(price.replace(" ", ""))
            
            # Определение категории и компонента (упрощенно)
            if "адаптер" in name.lower():
                category = "адаптер №1" if "1" in name else "адаптер №2" if "2" in name else "адаптер №3"
                component = "насос" if "насос" in name.lower() else "колонка" if "колонка" in name.lower() else name
            elif "кессон" in name.lower():
                category = "кессон №1" if "1" in name else "кессон №2" if "2" in name else "кессон №3"
                component = name
            else:
                category = "другое"
                component = name
            
            # Добавление в результат
            if category not in result["equipment_data"]:
                result["equipment_data"][category] = {}
            
            result["equipment_data"][category][component] = price
        
        # Обработка найденных районов
        for name, price in district_matches:
            name = name.strip()
            price = int(price.replace(" ", ""))
            
            result["districts_data"].append({
                "name": name,
                "base_price": price
            })
        
        return result
    
    except Exception as e:
        print(f"Ошибка при парсинге PDF: {str(e)}")
        return {"equipment_data": {}, "districts_data": []}

def update_prices_from_pdf(pdf_path: str) -> Tuple[bool, str]:
    """
    Обновление цен из PDF-файла
    """
    try:
        # Парсинг PDF
        parsed_data = parse_pdf_prices(pdf_path)
        
        # Обновление данных об оборудовании
        if parsed_data.get("equipment_data"):
            equipment_file = os.path.join("data", "equipment.json")
            
            # Загрузка существующих данных
            if os.path.exists(equipment_file):
                with open(equipment_file, "r", encoding="utf-8") as file:
                    equipment_data = json.load(file)
            else:
                equipment_data = {"equipment_data": {}, "cost_per_meter": 0}
            
            # Обновление данных
            for category, components in parsed_data["equipment_data"].items():
                if category not in equipment_data["equipment_data"]:
                    equipment_data["equipment_data"][category] = {}
                
                for component, price in components.items():
                    equipment_data["equipment_data"][category][component] = price
            
            # Сохранение обновленных данных
            with open(equipment_file, "w", encoding="utf-8") as file:
                json.dump(equipment_data, file, ensure_ascii=False, indent=4)
        
        # Обновление данных о районах
        if parsed_data.get("districts_data"):
            districts_file = os.path.join("data", "districts.json")
            
            # Загрузка существующих данных
            if os.path.exists(districts_file):
                with open(districts_file, "r", encoding="utf-8") as file:
                    districts_data = json.load(file)
            else:
                districts_data = {"districts": []}
            
            # Обновление данных
            for district_info in parsed_data["districts_data"]:
                district_name = district_info["name"]
                base_price = district_info["base_price"]
                
                # Поиск района по имени
                district_found = False
                for district in districts_data["districts"]:
                    if district["name"] == district_name:
                        district["base_price"] = base_price
                        district_found = True
                        break
                
                # Добавление нового района, если не найден
                if not district_found:
                    new_district = {
                        "id": len(districts_data["districts"]) + 1,
                        "name": district_name,
                        "depths": [30, 40, 50, 60, 70, 80],  # Значения по умолчанию
                        "base_price": base_price
                    }
                    districts_data["districts"].append(new_district)
            
            # Сохранение обновленных данных
            with open(districts_file, "w", encoding="utf-8") as file:
                json.dump(districts_data, file, ensure_ascii=False, indent=4)
        
        return True, "Цены успешно обновлены"
    
    except Exception as e:
        return False, f"Ошибка при обновлении цен: {str(e)}"

