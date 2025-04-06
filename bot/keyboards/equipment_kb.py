from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import json
import os

# --- Новая структура данных для оборудования --- 
def load_equipment_data():
    """Загружает данные об оборудовании из JSON."""
    try:
        with open(os.path.join("data", "equipment.json"), "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        print("Ошибка: Файл data/equipment.json не найден.")
        return {}
    except json.JSONDecodeError:
        print("Ошибка: Неверный формат JSON в data/equipment.json.")
        return {}

# --- Основная клавиатура выбора оборудования --- 
def get_main_equipment_keyboard(selected_adapter_id=None, selected_caisson_id=None) -> InlineKeyboardMarkup:
    """Создает основную клавиатуру для выбора оборудования (адаптер, кессон)."""
    builder = InlineKeyboardBuilder()
    equipment_data = load_equipment_data()
    
    adapter_name = "Не выбран" 
    caisson_name = "Не выбран"

    # Получаем название выбранного адаптера
    if selected_adapter_id:
        for adapter in equipment_data.get("adapters", []):
            if adapter['id'] == selected_adapter_id:
                adapter_name = f"{adapter['name']} ({adapter['price']} ₽)"
                break

    # Получаем название выбранного кессона
    if selected_caisson_id:
        for caisson in equipment_data.get("caissons", []):
            if caisson['id'] == selected_caisson_id:
                caisson_name = f"{caisson['name']} ({caisson['price']} ₽)"
                break

    # Кнопка выбора адаптера
    adapter_text = f"🔩 Адаптер: {adapter_name}"
    builder.button(text=adapter_text, callback_data="select_adapter_category")

    # Кнопка выбора кессона
    caisson_text = f"🕳️ Кессон: {caisson_name}"
    builder.button(text=caisson_text, callback_data="select_caisson_category")

    # Кнопки управления
    builder.button(text="✅ Подтвердить выбор", callback_data="finish_equipment_selection")
    builder.button(text="◀️ Назад (к глубине)", callback_data="back_to_depth")

    builder.adjust(1) # Все кнопки в один столбец
    return builder.as_markup()

# --- Клавиатура выбора конкретного Адаптера --- 
def get_adapter_options_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру со списком доступных адаптеров."""
    builder = InlineKeyboardBuilder()
    equipment_data = load_equipment_data()
    adapters = equipment_data.get("adapters", [])

    if not adapters:
        builder.button(text="Нет доступных адаптеров", callback_data="no_options")
    else:
        for adapter in adapters:
            button_text = f"{adapter['name']} - {adapter['price']} ₽"
            builder.button(text=button_text, callback_data=f"set_adapter_{adapter['id']}")
    
    builder.button(text="❌ Не выбирать адаптер", callback_data="set_adapter_none") # Кнопка сброса
    builder.button(text="◀️ Назад", callback_data="back_to_main_equipment")
    builder.adjust(1)
    return builder.as_markup()

# --- Клавиатура выбора конкретного Кессона --- 
def get_caisson_options_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру со списком доступных кессонов."""
    builder = InlineKeyboardBuilder()
    equipment_data = load_equipment_data()
    caissons = equipment_data.get("caissons", [])

    if not caissons:
        builder.button(text="Нет доступных кессонов", callback_data="no_options")
    else:
        for caisson in caissons:
            button_text = f"{caisson['name']} - {caisson['price']} ₽"
            builder.button(text=button_text, callback_data=f"set_caisson_{caisson['id']}")
    
    builder.button(text="❌ Не выбирать кессон", callback_data="set_caisson_none") # Кнопка сброса
    builder.button(text="◀️ Назад", callback_data="back_to_main_equipment")
    builder.adjust(1)
    return builder.as_markup()

# --- Клавиатура подтверждения финального заказа --- 
def get_confirm_order_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура для подтверждения финального заказа с оборудованием.
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить заказ", callback_data="confirm_order_final")
    builder.button(text="✏️ Изменить оборудование", callback_data="edit_equipment") # Кнопка для возврата к выбору оборудования
    builder.button(text="◀️ Назад (к глубине)", callback_data="back_to_depth_from_confirm") # На всякий случай, если надо вернуться сильно назад
    builder.button(text="❌ Отмена заказа", callback_data="cancel_order")
    builder.adjust(1)
    return builder.as_markup()

