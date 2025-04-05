from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import json
import os

from bot.states.order_states import OrderStates
from bot.keyboards.district_kb import get_districts_keyboard

# Создание роутера
router = Router()

async def send_district_selection(message: Message, state: FSMContext):
    """
    Отправка сообщения с выбором района
    """
    # Установка состояния выбора района
    await state.set_state(OrderStates.selecting_district)
    
    # Очистка данных о предыдущем заказе
    await state.update_data(
        district_id=None,
        district_name=None,
        depth=None,
        selected_equipment={},
        total_cost=0
    )
    
    await message.answer(
        "🏙️ <b>Выберите район бурения:</b>",
        reply_markup=get_districts_keyboard()
    )

@router.callback_query(F.data.startswith("district_"))
async def process_district_selection(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик выбора района
    """
    # Получение ID выбранного района
    district_id = int(callback.data.split("_")[1])
    
    # Загрузка данных о районах
    with open(os.path.join("data", "districts.json"), "r", encoding="utf-8") as file:
        data = json.load(file)
    
    districts = data.get("districts", [])
    
    # Поиск выбранного района
    selected_district = next((d for d in districts if d["id"] == district_id), None)
    
    if not selected_district:
        await callback.answer("❌ Район не найден. Пожалуйста, выберите другой район.")
        return
    
    # Сохранение данных о выбранном районе
    await state.update_data(
        district_id=district_id,
        district_name=selected_district["name"],
        base_price=selected_district["base_price"]
    )
    
    # Переход к выбору глубины
    await state.set_state(OrderStates.selecting_depth)
    
    # Импорт здесь для избежания циклических импортов
    from bot.handlers.depth import send_depth_selection
    
    await callback.answer()
    await send_depth_selection(callback.message, state, district_id)

