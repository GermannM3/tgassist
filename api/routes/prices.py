from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
import json
import os
import PyPDF2
import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

# Модели данных
class PriceUpdate(BaseModel):
    equipment_name: str
    component_name: str
    price: float

class DistrictUpdate(BaseModel):
    district_id: int
    base_price: float

# Создание роутера
router = APIRouter()

@router.get("/equipment")
async def get_equipment_prices():
    """
    Получение цен на оборудование
    """
    try:
        # Путь к файлу с ценами на оборудование
        equipment_file = os.path.join("data", "equipment.json")
        
        # Проверка существования файла
        if not os.path.exists(equipment_file):
            return JSONResponse(
                status_code=404,
                content={"message": "Файл с ценами на оборудование не найден"}
            )
        
        # Загрузка данных
        with open(equipment_file, "r", encoding="utf-8") as file:
            data = json.load(file)
        
        return data
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/districts")
async def get_districts_prices():
    """
    Получение цен по районам
    """
    try:
        # Путь к файлу с данными о районах
        districts_file = os.path.join("data", "districts.json")
        
        # Проверка существования файла
        if not os.path.exists(districts_file):
            return JSONResponse(
                status_code=404,
                content={"message": "Файл с данными о районах не найден"}
            )
        
        # Загрузка данных
        with open(districts_file, "r", encoding="utf-8") as file:
            data = json.load(file)
        
        return data
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-equipment")
async def update_equipment_price(price_update: PriceUpdate):
    """
    Обновление цены на компонент оборудования
    """
    try:
        # Путь к файлу с ценами на оборудование
        equipment_file = os.path.join("data", "equipment.json")
        
        # Проверка существования файла
        if not os.path.exists(equipment_file):
            return JSONResponse(
                status_code=404,
                content={"message": "Файл с ценами на оборудование не найден"}
            )
        
        # Загрузка данных
        with open(equipment_file, "r", encoding="utf-8") as file:
            data = json.load(file)
        
        # Проверка существования категории оборудования
        if price_update.equipment_name not in data.get("equipment_data", {}):
            return JSONResponse(
                status_code=404,
                content={"message": f"Категория оборудования '{price_update.equipment_name}' не найдена"}
            )
        
        # Проверка существования компонента
        if price_update.component_name not in data["equipment_data"][price_update.equipment_name]:
            return JSONResponse(
                status_code=404,
                content={"message": f"Компонент '{price_update.component_name}' не найден в категории '{price_update.equipment_name}'"}
            )
        
        # Обновление цены
        data["equipment_data"][price_update.equipment_name][price_update.component_name] = price_update.price
        
        # Сохранение обновленных данных
        with open(equipment_file, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        
        return {"message": "Цена успешно обновлена"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-district")
async def update_district_price(district_update: DistrictUpdate):
    """
    Обновление базовой цены для района
    """
    try:
        # Путь к файлу с данными о районах
        districts_file = os.path.join("data", "districts.json")
        
        # Проверка существования файла
        if not os.path.exists(districts_file):
            return JSONResponse(
                status_code=404,
                content={"message": "Файл с данными о районах не найден"}
            )
        
        # Загрузка данных
        with open(districts_file, "r", encoding="utf-8") as file:
            data = json.load(file)
        
        # Поиск района по ID
        district_found = False
        for district in data.get("districts", []):
            if district.get("id") == district_update.district_id:
                district["base_price"] = district_update.base_price
                district_found = True
                break
        
        if not district_found:
            return JSONResponse(
                status_code=404,
                content={"message": f"Район с ID {district_update.district_id} не найден"}
            )
        
        # Сохранение обновленных данных
        with open(districts_file, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        
        return {"message": "Базовая цена района успешно обновлена"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/parse-pdf")
async def parse_pdf_prices(file: UploadFile = File(...)):
    """
    Парсинг цен из PDF-файла
    """
    try:
        # Проверка расширения файла
        if not file.filename.endswith('.pdf'):
            return JSONResponse(
                status_code=400,
                content={"message": "Файл должен быть в формате PDF"}
            )
        
        # Сохранение загруженного файла
        temp_file_path = os.path.join("data", "temp", file.filename)
        os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)
        
        with open(temp_file_path, "wb") as temp_file:
            content = await file.read()
            temp_file.write(content)
        
        # Парсинг PDF
        extracted_data = parse_pdf_content(temp_file_path)
        
        # Удаление временного файла
        os.remove(temp_file_path)
        
        return extracted_data
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def parse_pdf_content(pdf_path: str) -> Dict[str, Any]:
    """
    Парсинг содержимого PDF-файла
    """
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

