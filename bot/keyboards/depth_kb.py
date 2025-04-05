from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import json
import os

def get_depths_keyboard(district_id: int) -> InlineKeyboardMarkup:
    """
    Клавиатура для выбора глубины
    """
    # Загрузка данных о районах
    with open(os.path.join("data", "districts.json"), "r", encoding="utf-8") as file:
        data = json.load(file)
    
    districts = data.get("districts", [])
    
    # Поиск выбранного района
    selected_district = next((d for d in districts if d["id"] == district_id), None)
    
    if not selected_district:
        return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="back")]])
    
    # Получение доступных глубин для выбранного района
    depths = selected_district.get("depths", [])
    ground_types = selected_district.get("ground_types", {})
    
    # Создание клавиатуры
    builder = InlineKeyboardBuilder()
    
    # Добавление кнопок для каждой глубины с указанием типа грунта
    for depth in depths:
        # Определяем тип грунта для данной глубины
        ground_type = "Неизвестный"
        for gtype, info in ground_types.items():
            min_depth = info.get("min_depth", 0)
            max_depth = info.get("max_depth", 0)
            if min_depth <= depth <= max_depth:
                if gtype == "sand":
                    ground_type = "Песок"
                elif gtype == "limestone":
                    ground_type = "Известняк"
                elif gtype == "limestone_shallow":
                    ground_type = "Известняк (верх)"
                elif gtype == "limestone_deep":
                    ground_type = "Известняк (низ)"
                break
        
        builder.add(InlineKeyboardButton(
            text=f"{depth} м - {ground_type}",
            callback_data=f"depth_{depth}"
        ))
    
    # Добавление кнопки "Назад"
    builder.add(InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_districts"))
    
    # Размещение кнопок в одну колонку, кнопка "Назад" отдельно
    builder.adjust(1)
    
    return builder.as_markup()

