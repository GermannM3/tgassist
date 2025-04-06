from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import json
import os
import logging

from bot.states.order_states import OrderStates
from bot.keyboards.equipment_kb import (
    get_main_equipment_keyboard,
    get_adapter_options_keyboard,
    get_caisson_options_keyboard,
    get_confirm_order_keyboard,
    load_equipment_data # Импортируем функцию загрузки данных
)
from bot.keyboards.common_kb import get_cancel_keyboard

# Создание роутера
router = Router()

def calculate_total_cost(data: dict) -> int:
    """Рассчитывает общую стоимость заказа."""
    drilling_cost = data.get('drilling_cost', 0)
    equipment_cost = data.get('equipment_cost', 0)
    return drilling_cost + equipment_cost

async def update_equipment_message(callback: CallbackQuery, state: FSMContext):
    """Обновляет сообщение с основной клавиатурой выбора оборудования."""
    data = await state.get_data()
    selected_adapter_id = data.get("selected_adapter_id")
    selected_caisson_id = data.get("selected_caisson_id")
    
    message_text = "🔧 <b>Выберите или измените оборудование:</b>\n"
    
    equipment_cost = 0
    equipment_data = load_equipment_data()
    adapter_info = None
    caisson_info = None

    # Информация о выбранном адаптере
    if selected_adapter_id:
        for adapter in equipment_data.get("adapters", []):
            if adapter['id'] == selected_adapter_id:
                adapter_info = adapter
                equipment_cost += adapter['price']
                break
    
    # Информация о выбранном кессоне
    if selected_caisson_id:
        for caisson in equipment_data.get("caissons", []):
            if caisson['id'] == selected_caisson_id:
                caisson_info = caisson
                equipment_cost += caisson['price']
                break

    # Сохраняем стоимость оборудования и детали для итогового заказа
    await state.update_data(equipment_cost=equipment_cost,
                            adapter_info=adapter_info, 
                            caisson_info=caisson_info)

    total_cost = calculate_total_cost(data) # Пересчитываем общую стоимость
    await state.update_data(total_cost=total_cost)
    
    message_text += f"\n💰 <b>Текущая стоимость оборудования:</b> {equipment_cost} ₽"
    message_text += f"\n<b>Итоговая стоимость заказа:</b> {total_cost} ₽"
    
    try:
        await callback.message.edit_text(
            message_text,
            reply_markup=get_main_equipment_keyboard(selected_adapter_id, selected_caisson_id),
            parse_mode='HTML'
        )
    except Exception as e:
        logging.error(f"Ошибка при обновлении сообщения оборудования: {e}")
        # Попытка отправить новое сообщение, если редактирование не удалось
        try:
            await callback.message.answer(
                message_text,
                reply_markup=get_main_equipment_keyboard(selected_adapter_id, selected_caisson_id),
                parse_mode='HTML'
            )
        except Exception as inner_e:
            logging.error(f"Не удалось отправить новое сообщение оборудования: {inner_e}")

# --- Обработчики основной клавиатуры --- 

@router.callback_query(F.data == "select_adapter_category")
async def select_adapter_category(callback: CallbackQuery, state: FSMContext):
    """Показывает варианты адаптеров."""
    await callback.message.edit_text(
        "Выберите адаптер из списка:",
        reply_markup=get_adapter_options_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "select_caisson_category")
async def select_caisson_category(callback: CallbackQuery, state: FSMContext):
    """Показывает варианты кессонов."""
    await callback.message.edit_text(
        "Выберите кессон из списка:",
        reply_markup=get_caisson_options_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "finish_equipment_selection")
async def finish_equipment_selection(callback: CallbackQuery, state: FSMContext):
    """Завершает выбор оборудования и показывает итоговый заказ."""
    data = await state.get_data()
    
    # Формирование итогового сообщения
    district_name = data.get("district_name", "Не указан")
    depth = data.get("depth", 0)
    ground_type = data.get("ground_type", "Неизвестный")
    price_per_meter = data.get("price_per_meter", 0)
    drilling_cost = data.get("drilling_cost", 0)
    equipment_cost = data.get("equipment_cost", 0)
    total_cost = data.get("total_cost", 0)
    adapter_info = data.get("adapter_info")
    caisson_info = data.get("caisson_info")

    summary = (
        f"✅ <b>Ваш заказ сформирован:</b>\n\n"
        f"📍 <b>Район:</b> {district_name}\n"
        f"📏 <b>Глубина:</b> {depth} м (Грунт: {ground_type})\n"
        f"💰 <b>Стоимость бурения:</b> {drilling_cost} ₽ (Цена за метр: {price_per_meter} ₽)\n\n"
        f"🔧 <b>Выбранное оборудование:</b>\n"
    )
    if adapter_info:
        summary += f"  - Адаптер: {adapter_info['name']} ({adapter_info['price']} ₽)\n"
    else:
        summary += "  - Адаптер: Не выбран\n"
    if caisson_info:
        summary += f"  - Кессон: {caisson_info['name']} ({caisson_info['price']} ₽)\n"
    else:
        summary += "  - Кессон: Не выбран\n"
    
    summary += f"\n💲 <b>Стоимость оборудования:</b> {equipment_cost} ₽\n"
    summary += f"<b>ИТОГО: {total_cost} ₽</b>\n\n"
    summary += "Для подтверждения заказа введите ваше ФИО."

    await state.set_state(OrderStates.entering_name)
    await callback.message.edit_text(summary, reply_markup=get_confirm_order_keyboard(), parse_mode='HTML')
    await callback.answer()

@router.callback_query(F.data == "back_to_depth")
async def back_to_depth_handler(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору глубины."""
    # Импортируем здесь, чтобы избежать циклического импорта
    from bot.handlers.depth import send_depth_selection
    await state.set_state(OrderStates.selecting_depth)
    await send_depth_selection(callback.message, state) # Используем функцию из depth.py
    await callback.answer()

# --- Обработчики выбора конкретных опций --- 

@router.callback_query(F.data.startswith("set_adapter_"))
async def set_adapter_handler(callback: CallbackQuery, state: FSMContext):
    """Устанавливает выбранный адаптер или сбрасывает выбор."""
    adapter_id = callback.data.split("_")[-1]
    if adapter_id == 'none':
        await state.update_data(selected_adapter_id=None)
    else:
        try:
            await state.update_data(selected_adapter_id=int(adapter_id))
        except ValueError:
             logging.error(f"Неверный ID адаптера: {adapter_id}")
             await callback.answer("Ошибка выбора адаптера.", show_alert=True)
             return

    await update_equipment_message(callback, state)
    await callback.answer()

@router.callback_query(F.data.startswith("set_caisson_"))
async def set_caisson_handler(callback: CallbackQuery, state: FSMContext):
    """Устанавливает выбранный кессон или сбрасывает выбор."""
    caisson_id = callback.data.split("_")[-1]
    if caisson_id == 'none':
        await state.update_data(selected_caisson_id=None)
    else:
        try:
            await state.update_data(selected_caisson_id=int(caisson_id))
        except ValueError:
            logging.error(f"Неверный ID кессона: {caisson_id}")
            await callback.answer("Ошибка выбора кессона.", show_alert=True)
            return
            
    await update_equipment_message(callback, state)
    await callback.answer()

@router.callback_query(F.data == "back_to_main_equipment")
async def back_to_main_equipment_handler(callback: CallbackQuery, state: FSMContext):
    """Возврат к главному меню выбора оборудования."""
    await update_equipment_message(callback, state)
    await callback.answer()

# --- Обработчики кнопок подтверждения/редактирования/отмены финального заказа --- 

@router.callback_query(F.data == "edit_equipment")
async def edit_equipment_handler(callback: CallbackQuery, state: FSMContext):
    """Возврат к редактированию оборудования из экрана подтверждения."""
    await state.set_state(OrderStates.selecting_equipment)
    await update_equipment_message(callback, state)
    await callback.answer()

@router.callback_query(F.data == "back_to_depth_from_confirm")
async def back_to_depth_from_confirm(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору глубины с экрана подтверждения."""
    # Импортируем здесь, чтобы избежать циклического импорта
    from bot.handlers.depth import send_depth_selection
    await state.set_state(OrderStates.selecting_depth)
    await send_depth_selection(callback.message, state) # Используем функцию из depth.py
    await callback.answer()

@router.callback_query(F.data == "cancel_order")
async def cancel_order_handler(callback: CallbackQuery, state: FSMContext):
    """Полная отмена заказа с экрана подтверждения."""
    await state.clear()
    await callback.message.edit_text("Заказ отменен.", reply_markup=None)
    # Можно добавить кнопку /start
    from bot.keyboards.common_kb import get_start_keyboard
    await callback.message.answer("Вы можете начать новый расчет.", reply_markup=get_start_keyboard())
    await callback.answer()

# --- Вспомогательная функция для инициации выбора оборудования --- 
async def send_equipment_selection(message: Message, state: FSMContext):
    """
    Отправка начального сообщения с выбором оборудования.
    Вызывается из другого хэндлера (например, depth.py).
    """
    await state.set_state(OrderStates.selecting_equipment)
    # Сбрасываем предыдущий выбор оборудования при входе
    await state.update_data(selected_adapter_id=None, selected_caisson_id=None, equipment_cost=0)
    
    # Создаем фейковый CallbackQuery для вызова update_equipment_message
    # Это немного хак, но позволяет переиспользовать логику обновления сообщения
    class FakeCallbackQuery:
        def __init__(self, msg):
            self.message = msg
        async def answer(self, *args, **kwargs): # Пустышка
            pass
            
    await update_equipment_message(FakeCallbackQuery(message), state)

