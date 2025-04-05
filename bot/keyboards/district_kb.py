from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import json
import os

def get_districts_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура для выбора района
    """
    # Загрузка данных о районах
    with open(os.path.join("data", "districts.json"), "r", encoding="utf-8") as file:
        data = json.load(file)
    
    districts = data.get("districts", [])
    
    # Создание клавиатуры
    builder = InlineKeyboardBuilder()
    
    # Добавление кнопок для каждого района
    for district in districts:
        builder.add(InlineKeyboardButton(
            text=district["name"],
            callback_data=f"district_{district['id']}"
        ))
    
    # Размещение кнопок в одну колонку
    builder.adjust(1)
    
    return builder.as_markup()

