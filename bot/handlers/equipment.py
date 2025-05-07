from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import json
import os
import logging

from bot.states.order_states import OrderStates
from bot.keyboards.equipment_kb import (
    get_simplified_equipment_keyboard, # Используем новую клавиатуру
    get_confirm_order_keyboard,
    load_equipment_data
)
from bot.keyboards.common_kb import get_cancel_keyboard

# Создание роутера
router = Router()

async def send_equipment_selection(message: Message, state: FSMContext):
    """Отправляет сообщение с выбором типа техники."""
    await message.answer(
        "🚜 <b>Выберите тип техники:</b>",
        reply_markup=get_equipment_type_keyboard(),
        parse_mode='HTML'
    )
    await state.set_state(OrderStates.selecting_equipment_type)

def calculate_total_cost(data: dict) -> int:
    """Рассчитывает общую стоимость заказа."""
    equipment_cost = data.get('equipment_price', 0)
    equipment_type = data.get('equipment_type', 'urb')
    depth = data.get('depth', 0)
    
    # Пересчитываем стоимость бурения в зависимости от типа техники
    if equipment_type == 'mgbu':
        drilling_cost = 3500 * depth
    else:
        drilling_cost = 3200 * depth
        
    return drilling_cost + equipment_cost

async def show_equipment_options(message: Message, state: FSMContext):
    """Отправляет сообщение с выбором опций оборудования."""
    await message.answer(
        "🔧 <b>Выберите вариант оборудования:</b>",
        reply_markup=get_simplified_equipment_keyboard(),
        parse_mode='HTML'
    )
    await state.set_state(OrderStates.selecting_equipment)

# --- Обработчик выбора опции оборудования --- 

@router.callback_query(OrderStates.selecting_equipment_type, F.data.startswith("equipment_type_"))
async def select_equipment_type(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает выбор типа техники."""
    equipment_type = callback.data.split("_")[-1]
    await state.update_data(equipment_type=equipment_type)
    
    # Переходим к выбору конкретного оборудования
    await callback.message.edit_text(
        "🔧 <b>Выберите вариант оборудования:</b>",
        reply_markup=get_simplified_equipment_keyboard(),
        parse_mode='HTML'
    )
    await state.set_state(OrderStates.selecting_equipment)
    await callback.answer()

@router.callback_query(OrderStates.selecting_equipment, F.data.startswith("select_equipment_"))
async def select_equipment_option(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает выбор одной из опций оборудования."""
    option_key = callback.data.split("_")[-1]
    equipment_data = load_equipment_data()
    selected_option = None

    for option in equipment_data.get("options", []):
        if option['key'] == option_key:
            selected_option = option
            break

    if not selected_option:
        await callback.answer("Ошибка: Выбранная опция не найдена.", show_alert=True)
        return

    # Сохраняем выбранную опцию и ее стоимость
    await state.update_data(
        selected_equipment_key=option_key,
        equipment_name=selected_option['name'],
        equipment_price=selected_option['price']
    )

    # Пересчитываем общую стоимость
    data = await state.get_data()
    total_cost = calculate_total_cost(data)
    await state.update_data(total_cost=total_cost)

    # Сразу переходим к подтверждению заказа
    await show_order_summary(callback, state)
    await callback.answer()

async def show_order_summary(callback: CallbackQuery, state: FSMContext):
    """Показывает итоговый заказ для подтверждения."""
    data = await state.get_data()
    
    district_name = data.get("district_name", "Не указан")
    depth = data.get("depth", 0)
    ground_type = data.get("ground_type", "Неизвестный")
    price_per_meter = data.get("price_per_meter", 0)
    drilling_cost = data.get("drilling_cost", 0)
    equipment_name = data.get("equipment_name", "Не выбрано")
    equipment_price = data.get("equipment_price", 0)
    total_cost = data.get("total_cost", 0)

    summary = (
        f"✅ <b>Ваш заказ сформирован:</b>\n\n"
        f"📍 <b>Район:</b> {district_name}\n"
        f"📏 <b>Глубина:</b> {depth} м (Грунт: {ground_type})\n"
        f"💰 <b>Стоимость бурения:</b> {drilling_cost} ₽ (Цена за метр: {price_per_meter} ₽)\n\n"
        f"🔧 <b>Выбранное оборудование:</b>\n"
        f"  - {equipment_name} ({equipment_price} ₽)\n\n"
        f"💲 <b>Стоимость оборудования:</b> {equipment_price} ₽\n"
        f"<b>ИТОГО: {total_cost} ₽</b>\n\n"
        f"Пожалуйста, введите ваше ФИО для оформления заказа."
    )

    await state.set_state(OrderStates.entering_name)
    try:
        await callback.message.edit_text(summary, parse_mode='HTML')
    except Exception as e:
        logging.error(f"Ошибка при редактировании сообщения для подтверждения: {e}")
        await callback.message.answer(summary, parse_mode='HTML')

# --- Обработчик кнопки "Изменить оборудование" --- 

@router.callback_query(F.data == "select_equipment") # Обрабатываем callback от кнопки "Изменить оборудование"
async def edit_equipment_handler(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору оборудования из экрана подтверждения."""
    # Просто показываем снова опции оборудования
    await state.set_state(OrderStates.selecting_equipment)
    try:
        await callback.message.edit_text(
            "🔧 <b>Выберите вариант оборудования:</b>",
            reply_markup=get_simplified_equipment_keyboard(),
            parse_mode='HTML'
        )
    except Exception as e:
        logging.error(f"Ошибка при редактировании сообщения для изменения оборудования: {e}")
        await callback.message.answer(
            "🔧 <b>Выберите вариант оборудования:</b>",
            reply_markup=get_simplified_equipment_keyboard(),
            parse_mode='HTML'
        )
    await callback.answer()

# --- Обработчик кнопки "Назад (к глубине)" --- 

@router.callback_query(F.data == "back_to_depth")
async def back_to_depth_handler(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору глубины из меню оборудования."""
    from bot.handlers.depth import send_depth_selection # Импорт внутри функции
    await state.set_state(OrderStates.selecting_depth)
    # Нужно передать message, а не callback.message для send_depth_selection
    await send_depth_selection(callback.message, state) 
    await callback.answer()

@router.callback_query(F.data == "back_to_depth_from_confirm")
async def back_to_depth_from_confirm_handler(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору глубины из меню подтверждения."""
    from bot.handlers.depth import send_depth_selection # Импорт внутри функции
    await state.set_state(OrderStates.selecting_depth)
    # Нужно передать message, а не callback.message для send_depth_selection
    await send_depth_selection(callback.message, state) 
    await callback.answer()

# Старые обработчики удалены

