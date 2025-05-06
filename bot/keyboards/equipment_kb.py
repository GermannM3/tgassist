from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import json
import os

def load_equipment_data():
    """Загружает данные об оборудовании из JSON."""
    try:
        # Используем относительный путь от корня проекта
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        file_path = os.path.join(base_dir, "data", "equipment.json")
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Ошибка: Файл {file_path} не найден.")
        return {}
    except json.JSONDecodeError:
        print(f"Ошибка: Неверный формат JSON в {file_path}.")
        return {}

def get_simplified_equipment_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для выбора одного из четырех вариантов оборудования."""
    builder = InlineKeyboardBuilder()
    equipment_data = load_equipment_data()
    options = equipment_data.get("options", [])

    if not options:
        builder.button(text="Нет доступных опций", callback_data="no_options")
    else:
        for option in options:
            button_text = f"{option['name']} - {option['price']} ₽"
            # Используем 'key' в callback_data для идентификации опции
            builder.button(text=button_text, callback_data=f"select_equipment_{option['key']}")

    builder.button(text="◀️ Назад (к глубине)", callback_data="back_to_depth")
    builder.adjust(1) # Все кнопки в один столбец
    return builder.as_markup()

# --- Клавиатура подтверждения финального заказа --- 
def get_confirm_order_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура для подтверждения финального заказа с оборудованием.
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить заказ", callback_data="confirm_order_final")
    # Обновляем callback_data для кнопки изменения
    builder.button(text="✏️ Изменить оборудование", callback_data="select_equipment") 
    builder.button(text="◀️ Назад (к глубине)", callback_data="back_to_depth_from_confirm")
    builder.button(text="❌ Отмена заказа", callback_data="cancel_order")
    builder.adjust(1)
    return builder.as_markup()

# Старые функции get_main_equipment_keyboard, get_adapter_options_keyboard, get_caisson_options_keyboard удалены

