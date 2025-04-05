from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import json
import os

def get_equipment_categories_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура для выбора категории оборудования
    """
    # Загрузка данных об оборудовании
    with open(os.path.join("data", "equipment.json"), "r", encoding="utf-8") as file:
        data = json.load(file)
    
    equipment_data = data.get("equipment_data", {})
    
    # Создание клавиатуры
    builder = InlineKeyboardBuilder()
    
    # Создаем и сохраняем маппинг для категорий
    categories_mapping = {}
    for i, category in enumerate(equipment_data.keys(), 1):
        categories_mapping[str(i)] = category
        builder.add(InlineKeyboardButton(
            text=category,
            callback_data=f"ecat_{i}"
        ))
    
    # Сохранение маппинга категорий
    with open(os.path.join("data", "category_codes.json"), "w", encoding="utf-8") as file:
        json.dump({"categories": categories_mapping}, file, ensure_ascii=False, indent=2)
    
    # Добавление кнопок управления
    builder.add(InlineKeyboardButton(text="✅ Завершить выбор", callback_data="finish_equipment"))
    builder.add(InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_depth"))
    
    # Размещение кнопок в одну колонку
    builder.adjust(1)
    
    return builder.as_markup()

def get_equipment_components_keyboard(category: str, selected_components: list = None) -> InlineKeyboardMarkup:
    """
    Клавиатура для выбора компонентов оборудования
    """
    if selected_components is None:
        selected_components = []
    
    # Загрузка данных об оборудовании
    with open(os.path.join("data", "equipment.json"), "r", encoding="utf-8") as file:
        data = json.load(file)
    
    equipment_data = data.get("equipment_data", {})
    
    # Получение компонентов для выбранной категории
    components = equipment_data.get(category, {})
    
    # Создание клавиатуры
    builder = InlineKeyboardBuilder()
    
    # Создаем и сохраняем маппинг для компонентов
    components_mapping = {}
    for i, (component, price) in enumerate(components.items(), 1):
        # Проверка, выбран ли компонент
        is_selected = component in selected_components
        prefix = "✅ " if is_selected else ""
        
        components_mapping[str(i)] = component
        builder.add(InlineKeyboardButton(
            text=f"{prefix}{component} - {price} ₽",
            callback_data=f"comp_{i}"
        ))
    
    # Сохранение маппинга компонентов
    with open(os.path.join("data", "component_codes.json"), "w", encoding="utf-8") as file:
        json.dump({"category": category, "components": components_mapping}, file, ensure_ascii=False, indent=2)
    
    # Добавление кнопок управления
    builder.add(InlineKeyboardButton(text="✅ Подтвердить выбор", callback_data="confirm_components"))
    builder.add(InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_equipment_categories"))
    
    # Размещение кнопок в одну колонку
    builder.adjust(1)
    
    return builder.as_markup()

def get_selected_equipment_keyboard(selected_equipment: dict) -> InlineKeyboardMarkup:
    """
    Клавиатура с выбранным оборудованием
    """
    builder = InlineKeyboardBuilder()
    
    # Создаем и сохраняем маппинг для редактирования категорий
    categories_mapping = {}
    i = 1
    
    # Добавление кнопок для каждой категории оборудования с выбранными компонентами
    for category, components in selected_equipment.items():
        if components:  # Если есть выбранные компоненты
            categories_mapping[str(i)] = category
            builder.add(InlineKeyboardButton(
                text=f"{category} ({len(components)} компонентов)",
                callback_data=f"edit_{i}"
            ))
            i += 1
    
    # Сохранение маппинга категорий для редактирования
    with open(os.path.join("data", "edit_codes.json"), "w", encoding="utf-8") as file:
        json.dump({"categories": categories_mapping}, file, ensure_ascii=False, indent=2)
    
    # Добавление кнопок управления
    builder.add(InlineKeyboardButton(text="➕ Добавить оборудование", callback_data="add_equipment"))
    builder.add(InlineKeyboardButton(text="✅ Подтвердить заказ", callback_data="confirm_order"))
    builder.add(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"))
    
    # Размещение кнопок в одну колонку
    builder.adjust(1)
    
    return builder.as_markup()

def get_adapters_keyboard() -> InlineKeyboardMarkup:
    """
    Создание клавиатуры для выбора адаптера
    """
    # Загрузка данных об оборудовании
    with open(os.path.join("data", "equipment.json"), "r", encoding="utf-8") as file:
        data = json.load(file)
    
    # Создание клавиатуры
    builder = InlineKeyboardBuilder()
    
    # Добавление кнопок для каждого адаптера
    for adapter in data.get("equipment", {}).get("adapters", []):
        # Формирование текста кнопки с названием и ценой
        button_text = f"{adapter['name']} - {adapter['price']} ₽"
        builder.add(InlineKeyboardButton(
            text=button_text,
            callback_data=f"select_adapter_{adapter['id']}"
        ))
    
    # Добавление кнопки "Назад"
    builder.add(InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_equipment"
    ))
    
    # Размещение кнопок в одну колонку
    builder.adjust(1)
    
    return builder.as_markup()

def get_caissons_keyboard() -> InlineKeyboardMarkup:
    """
    Создание клавиатуры для выбора кессона
    """
    # Загрузка данных об оборудовании
    with open(os.path.join("data", "equipment.json"), "r", encoding="utf-8") as file:
        data = json.load(file)
    
    # Создание кнопок для каждого кессона
    builder = InlineKeyboardBuilder()
    
    # Добавление кнопок для каждого кессона
    for caisson in data.get("equipment", {}).get("caissons", []):
        # Формирование текста кнопки с названием и ценой
        button_text = f"{caisson['name']} - {caisson['price']} ₽"
        builder.add(InlineKeyboardButton(
            text=button_text,
            callback_data=f"select_caisson_{caisson['id']}"
        ))
    
    # Добавление кнопки "Назад"
    builder.add(InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_adapters"
    ))
    
    # Размещение кнопок в одну колонку
    builder.adjust(1)
    
    return builder.as_markup()

def get_confirm_keyboard() -> InlineKeyboardMarkup:
    """
    Создание клавиатуры для подтверждения выбора
    """
    builder = InlineKeyboardBuilder()
    
    # Добавление кнопок подтверждения и отмены
    builder.add(InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm"))
    builder.add(InlineKeyboardButton(text="❌ Отменить", callback_data="cancel"))
    
    # Размещение кнопок в одну колонку
    builder.adjust(1)
    
    return builder.as_markup()

