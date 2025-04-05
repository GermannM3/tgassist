from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """
    Основная клавиатура бота
    """
    keyboard = [
        [KeyboardButton(text="🔍 Новый расчет")],
        [KeyboardButton(text="📋 Мои заказы"), KeyboardButton(text="ℹ️ Помощь")]
    ]
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_back_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура с кнопкой "Назад"
    """
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="◀️ Назад", callback_data="back"))
    
    return builder.as_markup()

def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура с кнопкой "Отмена"
    """
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"))
    
    return builder.as_markup()

def get_confirm_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура с кнопками "Подтвердить" и "Отмена"
    """
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm"))
    builder.add(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"))
    
    return builder.as_markup()

