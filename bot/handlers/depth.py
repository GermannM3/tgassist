from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.states.order_states import OrderStates
from bot.keyboards.depth_kb import get_depths_keyboard
from bot.keyboards.district_kb import get_districts_keyboard

# Создание роутера
router = Router()

async def send_depth_selection(message: Message, state: FSMContext, district_id: int):
    """
    Отправка сообщения с выбором глубины
    """
    # Получение данных о выбранном районе
    data = await state.get_data()
    district_name = data.get("district_name", "Неизвестный район")
    
    await message.edit_text(
        f"🏙️ <b>Выбранный район:</b> {district_name}\n\n"
        f"📏 <b>Выберите необходимую глубину бурения:</b>",
        reply_markup=get_depths_keyboard(district_id)
    )

@router.callback_query(F.data.startswith("depth_"))
async def process_depth_selection(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик выбора глубины
    """
    # Получение выбранной глубины
    depth = int(callback.data.split("_")[1])
    
    # Получение данных о заказе
    data = await state.get_data()
    district_id = data.get("district_id", 1)
    district_name = data.get("district_name", "Неизвестный район")
    
    # Загрузка данных о районах
    import json
    import os
    
    with open(os.path.join("data", "districts.json"), "r", encoding="utf-8") as file:
        districts_data = json.load(file)
    
    # Поиск выбранного района
    selected_district = next((d for d in districts_data.get("districts", []) if d["id"] == district_id), None)
    
    if not selected_district:
        await callback.answer("❌ Район не найден. Пожалуйста, выберите другой район.")
        return
    
    # Определение типа грунта и цены на основе глубины
    ground_types = selected_district.get("ground_types", {})
    ground_type = "Неизвестный"
    price_per_meter = selected_district.get("base_price", 0)
    
    # Проверка каждого типа грунта
    for gtype, info in ground_types.items():
        min_depth = info.get("min_depth", 0)
        max_depth = info.get("max_depth", 0)
        if min_depth <= depth <= max_depth:
            if gtype == "sand":
                ground_type = "Песок"
            elif gtype == "limestone":
                ground_type = "Известняк"
            elif gtype == "limestone_shallow":
                ground_type = "Известняк (верхний слой)"
            elif gtype == "limestone_deep":
                ground_type = "Известняк (нижний слой)"
            price_per_meter = info.get("price_per_meter", price_per_meter)
            break
    
    # Расчет базовой стоимости бурения
    drilling_cost = price_per_meter * depth
    
    # Сохранение данных о выбранной глубине, типе грунта и стоимости
    await state.update_data(
        depth=depth,
        ground_type=ground_type,
        price_per_meter=price_per_meter,
        drilling_cost=drilling_cost,
        total_cost=drilling_cost  # Начальная общая стоимость равна стоимости бурения
    )
    
    # Переход к выбору типа техники
    await state.set_state(OrderStates.selecting_equipment_type)
    
    # Создаем клавиатуру для выбора техники
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="УРБ (3200 ₽/м)", callback_data="equipment_type_urb")
    builder.button(text="МГБУ (3500 ₽/м)", callback_data="equipment_type_mgbu")
    builder.adjust(1)
    
    await callback.message.edit_text(
        f"🚜 <b>Выберите тип техники для бурения:</b>\n\n"
        f"📍 <b>Район:</b> {district_name}\n"
        f"📏 <b>Глубина:</b> {depth} м (Грунт: {ground_type})\n"
        f"💰 <b>Базовая стоимость бурения:</b> {drilling_cost} ₽",
        reply_markup=builder.as_markup(),
        parse_mode='HTML'
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_districts")
async def back_to_districts(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик кнопки "Назад" при выборе глубины
    """
    # Возврат к выбору района
    await state.set_state(OrderStates.selecting_district)
    
    # Импорт здесь для избежания циклических импортов
    from bot.handlers.district import send_district_selection
    
    await callback.answer()
    await send_district_selection(callback.message, state)

