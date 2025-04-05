from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import json
import os
import logging

from bot.states.order_states import OrderStates
from bot.keyboards.equipment_kb import (
    get_equipment_categories_keyboard,
    get_equipment_components_keyboard,
    get_selected_equipment_keyboard,
    get_caissons_keyboard,
    get_confirm_keyboard
)

# Создание роутера
router = Router()

async def send_equipment_selection(message: Message, state: FSMContext):
    """
    Отправка сообщения с выбором оборудования
    """
    try:
        # Получение данных о заказе
        data = await state.get_data()
        district_name = data.get("district_name", "Неизвестный район")
        depth = data.get("depth", 0)
        drilling_cost = data.get("drilling_cost", 0)
        ground_type = data.get("ground_type", "Неизвестный")
        price_per_meter = data.get("price_per_meter", 0)
        
        await message.edit_text(
            f"🏙️ <b>Район:</b> {district_name}\n"
            f"📏 <b>Глубина:</b> {depth} м\n"
            f"🧱 <b>Тип грунта:</b> {ground_type}\n"
            f"💵 <b>Цена за метр:</b> {price_per_meter} ₽\n"
            f"💰 <b>Стоимость бурения:</b> {drilling_cost} ₽\n\n"
            f"🔧 <b>Выберите необходимое оборудование:</b>",
            reply_markup=get_equipment_categories_keyboard(),
            parse_mode='HTML'
        )
    except Exception as e:
        # Обработка ошибок (например, если сообщение слишком старое)
        logging.error(f"Ошибка при отправке выбора оборудования: {str(e)}")
        try:
            await message.answer(
                f"🔧 <b>Выберите необходимое оборудование:</b>",
                reply_markup=get_equipment_categories_keyboard()
            )
        except Exception as inner_e:
            logging.error(f"Не удалось восстановиться после ошибки: {str(inner_e)}")

@router.callback_query(F.data.startswith("ecat_"))
async def process_equipment_category_selection(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик выбора категории оборудования
    """
    try:
        # Получение кода категории
        category_id = callback.data.split("_")[1]
        
        # Загрузка маппинга категорий
        try:
            with open(os.path.join("data", "category_codes.json"), "r", encoding="utf-8") as file:
                categories_data = json.load(file)
                
            # Получаем имя категории из маппинга
            if category_id in categories_data.get("categories", {}):
                category = categories_data["categories"][category_id]
            else:
                await callback.answer("Ошибка: категория не найдена.", show_alert=True)
                return
        except Exception as e:
            await callback.answer(f"Ошибка данных", show_alert=True)
            logging.error(f"Ошибка при загрузке маппинга категорий: {str(e)}")
            return
        
        # Сохранение текущей категории
        await state.update_data(current_category=category)
        
        # Получение данных о заказе
        data = await state.get_data()
        selected_equipment = data.get("selected_equipment", {})
        
        # Получение выбранных компонентов для текущей категории
        selected_components = selected_equipment.get(category, [])
        
        # Переход к выбору компонентов
        await state.set_state(OrderStates.selecting_components)
        
        try:
            await callback.answer()
        except Exception as e:
            logging.warning(f"Не удалось ответить на callback: {str(e)}")
            
        try:
            await callback.message.edit_text(
                f"🔧 <b>Категория:</b> {category}\n\n"
                f"Выберите компоненты оборудования:",
                reply_markup=get_equipment_components_keyboard(category, selected_components),
                parse_mode='HTML'
            )
        except Exception as e:
            logging.error(f"Ошибка при редактировании сообщения: {str(e)}")
            try:
                await callback.message.answer(
                    f"🔧 <b>Категория:</b> {category}\n\n"
                    f"Выберите компоненты оборудования:",
                    reply_markup=get_equipment_components_keyboard(category, selected_components)
                )
            except Exception as inner_e:
                logging.error(f"Не удалось восстановиться после ошибки: {str(inner_e)}")
    except Exception as e:
        logging.error(f"Необработанная ошибка в process_equipment_category_selection: {str(e)}")
        try:
            await callback.answer("Произошла ошибка. Попробуйте еще раз.", show_alert=True)
        except:
            pass

@router.callback_query(F.data.startswith("comp_"))
async def process_component_selection(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик выбора компонента оборудования
    """
    try:
        # Получение кода компонента
        component_id = callback.data.split("_")[1]
        
        # Получение данных о заказе
        data = await state.get_data()
        current_category = data.get("current_category", "")
        
        # Загрузка маппинга компонентов
        try:
            with open(os.path.join("data", "component_codes.json"), "r", encoding="utf-8") as file:
                components_data = json.load(file)
                
            # Получаем имя компонента из маппинга
            if components_data.get("category") == current_category and component_id in components_data.get("components", {}):
                component = components_data["components"][component_id]
            else:
                await callback.answer("Ошибка: компонент не найден.", show_alert=True)
                return
        except Exception as e:
            await callback.answer("Ошибка данных", show_alert=True)
            logging.error(f"Ошибка при загрузке маппинга компонентов: {str(e)}")
            return
        
        # Получение выбранного оборудования
        selected_equipment = data.get("selected_equipment", {})
        
        # Инициализация списка компонентов для категории, если его нет
        if current_category not in selected_equipment:
            selected_equipment[current_category] = []
        
        # Добавление или удаление компонента из списка
        if component in selected_equipment[current_category]:
            selected_equipment[current_category].remove(component)
        else:
            selected_equipment[current_category].append(component)
        
        # Обновление данных о выбранном оборудовании
        await state.update_data(selected_equipment=selected_equipment)
        
        # Получение обновленного списка выбранных компонентов
        selected_components = selected_equipment.get(current_category, [])
        
        try:
            await callback.answer()
        except Exception as e:
            logging.warning(f"Не удалось ответить на callback: {str(e)}")
            
        try:
            await callback.message.edit_text(
                f"🔧 <b>Категория:</b> {current_category}\n\n"
                f"Выберите компоненты оборудования:",
                reply_markup=get_equipment_components_keyboard(current_category, selected_components),
                parse_mode='HTML'
            )
        except Exception as e:
            logging.error(f"Ошибка при редактировании сообщения: {str(e)}")
            try:
                await callback.message.answer(
                    f"🔧 <b>Категория:</b> {current_category}\n\n"
                    f"Выберите компоненты оборудования:",
                    reply_markup=get_equipment_components_keyboard(current_category, selected_components)
                )
            except Exception as inner_e:
                logging.error(f"Не удалось восстановиться после ошибки: {str(inner_e)}")
    except Exception as e:
        logging.error(f"Необработанная ошибка в process_component_selection: {str(e)}")
        try:
            await callback.answer("Произошла ошибка. Попробуйте еще раз.", show_alert=True)
        except:
            pass

@router.callback_query(F.data == "confirm_components")
async def confirm_components(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик подтверждения выбора компонентов
    """
    # Возврат к выбору категорий оборудования
    await state.set_state(OrderStates.selecting_equipment)
    
    # Получение данных о заказе
    data = await state.get_data()
    district_name = data.get("district_name", "Неизвестный район")
    depth = data.get("depth", 0)
    drilling_cost = data.get("drilling_cost", 0)
    
    await callback.answer()
    await callback.message.edit_text(
        f"🏙️ <b>Район:</b> {district_name}\n"
        f"📏 <b>Глубина:</b> {depth} м\n"
        f"💰 <b>Стоимость бурения:</b> {drilling_cost} ₽\n\n"
        f"🔧 <b>Выберите необходимое оборудование:</b>",
        reply_markup=get_equipment_categories_keyboard(),
        parse_mode='HTML'
    )

@router.callback_query(F.data == "back_to_equipment_categories")
async def back_to_equipment_categories(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик кнопки "Назад" при выборе компонентов
    """
    # Возврат к выбору категорий оборудования
    await state.set_state(OrderStates.selecting_equipment)
    
    # Получение данных о заказе
    data = await state.get_data()
    district_name = data.get("district_name", "Неизвестный район")
    depth = data.get("depth", 0)
    drilling_cost = data.get("drilling_cost", 0)
    
    await callback.answer()
    await callback.message.edit_text(
        f"🏙️ <b>Район:</b> {district_name}\n"
        f"📏 <b>Глубина:</b> {depth} м\n"
        f"💰 <b>Стоимость бурения:</b> {drilling_cost} ₽\n\n"
        f"🔧 <b>Выберите необходимое оборудование:</b>",
        reply_markup=get_equipment_categories_keyboard(),
        parse_mode='HTML'
    )

@router.callback_query(F.data == "finish_equipment")
async def finish_equipment_selection(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик завершения выбора оборудования
    """
    # Получение данных о заказе
    data = await state.get_data()
    district_name = data.get("district_name", "Неизвестный район")
    depth = data.get("depth", 0)
    drilling_cost = data.get("drilling_cost", 0)
    ground_type = data.get("ground_type", "Неизвестный")
    price_per_meter = data.get("price_per_meter", 0)
    selected_equipment = data.get("selected_equipment", {})
    
    # Расчет стоимости оборудования
    equipment_cost = 0
    equipment_details = []
    
    # Загрузка данных об оборудовании
    with open(os.path.join("data", "equipment.json"), "r", encoding="utf-8") as file:
        equipment_data = json.load(file).get("equipment_data", {})
    
    # Расчет стоимости выбранного оборудования
    for category, components in selected_equipment.items():
        if category in equipment_data and components:
            category_data = equipment_data[category]
            for component in components:
                if component in category_data:
                    component_price = category_data[component]
                    equipment_cost += component_price
                    equipment_details.append(f"{component} ({component_price} ₽)")
    
    # Расчет общей стоимости
    total_cost = drilling_cost + equipment_cost
    
    # Обновление данных о стоимости
    await state.update_data(
        equipment_cost=equipment_cost,
        total_cost=total_cost,
        equipment_details=equipment_details
    )
    
    # Переход к подтверждению заказа
    await state.set_state(OrderStates.confirming_order)
    
    # Формирование сообщения с деталями заказа
    message_text = (
        f"📋 <b>Детали заказа:</b>\n\n"
        f"🏙️ <b>Район:</b> {district_name}\n"
        f"📏 <b>Глубина:</b> {depth} м\n"
        f"🧱 <b>Тип грунта:</b> {ground_type}\n"
        f"💵 <b>Цена за метр:</b> {price_per_meter} ₽\n"
        f"💰 <b>Стоимость бурения:</b> {drilling_cost} ₽\n\n"
    )
    
    if equipment_details:
        message_text += f"🔧 <b>Выбранное оборудование:</b>\n"
        for detail in equipment_details:
            message_text += f"- {detail}\n"
        message_text += f"\n💰 <b>Стоимость оборудования:</b> {equipment_cost} ₽\n"
    
    message_text += f"\n💰 <b>Общая стоимость:</b> {total_cost} ₽\n\n"
    message_text += "Подтвердите заказ или вернитесь к выбору оборудования."
    
    await callback.answer()
    await callback.message.edit_text(
        message_text,
        reply_markup=get_selected_equipment_keyboard(selected_equipment),
        parse_mode='HTML'
    )

@router.callback_query(F.data == "back_to_depth")
async def back_to_depth(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик кнопки "Назад" при выборе оборудования
    """
    # Возврат к выбору глубины
    await state.set_state(OrderStates.selecting_depth)
    
    # Получение данных о заказе
    data = await state.get_data()
    district_id = data.get("district_id", 1)
    
    # Импорт здесь для избежания циклических импортов
    from bot.handlers.depth import send_depth_selection
    
    await callback.answer()
    await send_depth_selection(callback.message, state, district_id)

@router.callback_query(F.data.startswith("edit_"))
async def edit_equipment(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик редактирования выбранного оборудования
    """
    # Получение кода категории
    category_id = callback.data.split("_")[1]
    
    # Загрузка маппинга категорий
    try:
        with open(os.path.join("data", "edit_codes.json"), "r", encoding="utf-8") as file:
            categories_data = json.load(file)
            
        # Получаем имя категории из маппинга
        if category_id in categories_data.get("categories", {}):
            category = categories_data["categories"][category_id]
        else:
            await callback.answer("Ошибка: категория не найдена. Попробуйте еще раз.")
            return
    except Exception as e:
        await callback.answer(f"Ошибка при загрузке данных: {str(e)}")
        return
    
    # Сохранение текущей категории
    await state.update_data(current_category=category)
    
    # Получение данных о заказе
    data = await state.get_data()
    selected_equipment = data.get("selected_equipment", {})
    
    # Получение выбранных компонентов для текущей категории
    selected_components = selected_equipment.get(category, [])
    
    # Переход к выбору компонентов
    await state.set_state(OrderStates.selecting_components)
    
    await callback.answer()
    await callback.message.edit_text(
        f"🔧 <b>Категория:</b> {category}\n\n"
        f"Выберите компоненты оборудования:",
        reply_markup=get_equipment_components_keyboard(category, selected_components),
        parse_mode='HTML'
    )

@router.callback_query(F.data == "add_equipment")
async def add_equipment(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик добавления оборудования
    """
    # Возврат к выбору категорий оборудования
    await state.set_state(OrderStates.selecting_equipment)
    
    # Получение данных о заказе
    data = await state.get_data()
    district_name = data.get("district_name", "Неизвестный район")
    depth = data.get("depth", 0)
    drilling_cost = data.get("drilling_cost", 0)
    
    await callback.answer()
    await callback.message.edit_text(
        f"🏙️ <b>Район:</b> {district_name}\n"
        f"📏 <b>Глубина:</b> {depth} м\n"
        f"💰 <b>Стоимость бурения:</b> {drilling_cost} ₽\n\n"
        f"🔧 <b>Выберите необходимое оборудование:</b>",
        reply_markup=get_equipment_categories_keyboard()
    )

@router.callback_query(F.data.startswith("select_adapter_"))
async def process_adapter_selection(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик выбора адаптера
    """
    adapter_id = callback.data.replace("select_adapter_", "")
    
    # Загрузка данных об оборудовании
    with open(os.path.join("data", "equipment.json"), "r", encoding="utf-8") as file:
        data = json.load(file)
    
    # Поиск выбранного адаптера
    adapter = next((a for a in data.get("equipment", {}).get("adapters", []) if a["id"] == adapter_id), None)
    
    if not adapter:
        await callback.answer("❌ Адаптер не найден")
        return
    
    # Сохранение данных об адаптере
    await state.update_data(
        selected_adapter=adapter,
        equipment_cost=adapter["price"]
    )
    
    # Переход к выбору кессона
    await state.set_state(OrderStates.selecting_caisson)
    
    # Отправка сообщения с выбором кессона
    await callback.message.edit_text(
        "🛢️ Выберите кессон:\n\n"
        "Кессон - это герметичная камера для размещения оборудования скважины.",
        reply_markup=get_caissons_keyboard()
    )
    
    await callback.answer()

@router.callback_query(F.data.startswith("select_caisson_"))
async def process_caisson_selection(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик выбора кессона
    """
    caisson_id = callback.data.replace("select_caisson_", "")
    
    # Загрузка данных об оборудовании
    with open(os.path.join("data", "equipment.json"), "r", encoding="utf-8") as file:
        data = json.load(file)
    
    # Поиск выбранного кессона
    caisson = next((c for c in data.get("equipment", {}).get("caissons", []) if c["id"] == caisson_id), None)
    
    if not caisson:
        await callback.answer("❌ Кессон не найден")
        return
    
    # Получение данных о выбранном адаптере
    data = await state.get_data()
    adapter = data.get("selected_adapter")
    
    # Расчет общей стоимости оборудования
    total_equipment_cost = adapter["price"] + caisson["price"]
    
    # Сохранение данных о кессоне и обновление общей стоимости
    await state.update_data(
        selected_caisson=caisson,
        equipment_cost=total_equipment_cost,
        adapter_info=adapter,
        caisson_info=caisson,
        equipment_details=[
            f"Адаптер: {adapter['name']} - {adapter['price']} ₽",
            f"Описание: {adapter['description']}",
            f"Кессон: {caisson['name']} - {caisson['price']} ₽",
            f"Описание: {caisson['description']}"
        ]
    )
    
    # Формирование сообщения с выбранным оборудованием
    message_text = (
        "✅ Выбранное оборудование:\n\n"
        f"🔧 Адаптер: {adapter['name']}\n"
        f"📝 {adapter['description']}\n"
        f"💰 Стоимость: {adapter['price']} ₽\n\n"
        f"🛢️ Кессон: {caisson['name']}\n"
        f"📝 {caisson['description']}\n"
        f"💰 Стоимость: {caisson['price']} ₽\n\n"
        f"💵 Общая стоимость оборудования: {total_equipment_cost} ₽\n\n"
        "Подтвердите выбор оборудования:"
    )
    
    # Переход к подтверждению заказа
    await state.set_state(OrderStates.confirming_order)
    
    await callback.message.edit_text(
        message_text,
        reply_markup=get_confirm_keyboard(),
        parse_mode='HTML'
    )
    
    await callback.answer()

