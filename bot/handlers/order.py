from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
import json
import os
from datetime import datetime
import uuid
import logging

from bot.states.order_states import OrderStates
from bot.keyboards.common_kb import get_main_keyboard, get_confirm_keyboard
from bot.utils.pdf_generator import generate_order_pdf

# ID канала для уведомлений менеджеру
MANAGER_CHANNEL_ID = -1001910234699

# Создание роутера
router = Router()

@router.callback_query(F.data == "confirm_order")
async def confirm_order(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик подтверждения заказа
    """
    # Переход к вводу контактной информации
    await state.set_state(OrderStates.entering_contact_info)
    
    await callback.answer()
    await callback.message.edit_text(
        "📞 <b>Введите ваш номер телефона</b> для связи:\n\n"
        "Например: +7 (999) 123-45-67",
        reply_markup=get_confirm_keyboard(),
        parse_mode='HTML'
    )

@router.message(OrderStates.entering_contact_info)
async def process_contact_info(message: Message, state: FSMContext, bot: Bot):
    """
    Обработчик ввода контактной информации
    """
    # Сохранение контактной информации
    await state.update_data(
        phone=message.text,
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name
    )
    
    # Переход к завершению заказа
    await state.set_state(OrderStates.completing_order)
    
    # Получение данных о заказе
    data = await state.get_data()
    
    # Проверка наличия информации о районе
    district_name = data.get("district_name")
    if district_name is None or district_name == "None":
        # Пытаемся восстановить название района по его ID
        district_id = data.get("district_id")
        if district_id:
            try:
                # Загрузка данных о районах
                with open(os.path.join("data", "districts.json"), "r", encoding="utf-8") as file:
                    districts_data = json.load(file)
                
                # Поиск района по ID
                for district in districts_data.get("districts", []):
                    if district.get("id") == district_id:
                        district_name = district.get("name", "Неизвестный район")
                        # Обновляем данные с корректным именем района
                        await state.update_data(district_name=district_name)
                        break
            except Exception as e:
                logging.error(f"Ошибка при восстановлении названия района: {e}")
                district_name = "Неизвестный район"
        else:
            district_name = "Неизвестный район"
    
    # Генерация уникального ID заказа
    order_id = str(uuid.uuid4())[:8].upper()
    
    # Текущая дата и время
    order_date = datetime.now().strftime("%d.%m.%Y %H:%M")
    
    # Сохранение ID и даты заказа
    await state.update_data(
        order_id=order_id,
        order_date=order_date
    )
    
    # Получаем обновленные данные
    data = await state.get_data()
    
    # Формирование данных заказа для сохранения и отправки
    order_data = {
        "order_id": order_id,
        "user_id": data.get("user_id"),
        "username": data.get("username", "-"),
        "full_name": data.get("full_name", "-"),
        "phone": data.get("phone", "-"),
        "district_name": district_name,
        "depth": data.get("depth", 0),
        "ground_type": data.get("ground_type", "Неизвестный"),
        "price_per_meter": data.get("price_per_meter", 0),
        "drilling_cost": data.get("drilling_cost", 0),
        "equipment_cost": data.get("equipment_cost", 0),
        "total_cost": data.get("total_cost", 0),
        "selected_equipment": data.get("selected_equipment", {}),
        "equipment_details": data.get("equipment_details", []),
        "adapter_info": data.get("adapter_info", {}),
        "caisson_info": data.get("caisson_info", {}),
        "selected_adapter": data.get("selected_adapter", {}),
        "selected_caisson": data.get("selected_caisson", {}),
        "order_date": order_date,
        "status": "new"
    }
    
    # Сохранение заказа в JSON
    save_order(order_data)
    
    # Генерация PDF с деталями заказа
    try:
        try:
            pdf_path = generate_order_pdf(order_data)
            pdf_exists = True
        except Exception as e:
            logging.error(f"Ошибка при создании PDF для заказа {order_id}: {e}")
            pdf_path = None
            pdf_exists = False
    except Exception as e:
        logging.error(f"Ошибка при создании PDF для заказа {order_id}: {e}")
        pdf_path = None
        pdf_exists = False
    
    # Формирование сообщения для пользователя
    user_message = (
        f"✅ <b>Заказ #{order_id} успешно оформлен!</b>\n\n"
        f"📅 Дата: {order_date}\n"
        f"🏙️ Район: {district_name}\n"
        f"📏 Глубина: {order_data.get('depth')} м\n"
        f"🧱 Тип грунта: {order_data.get('ground_type')}\n"
        f"💰 Общая стоимость: {order_data.get('total_cost')} ₽\n\n"
        f"📞 Контактный телефон: {order_data.get('phone')}\n\n"
        f"Наш менеджер свяжется с вами в ближайшее время для подтверждения заказа."
    )
    
    # Отправка сообщения пользователю
    await message.answer(user_message, parse_mode='HTML')
    
    # Отправка PDF-файла пользователю, если он создан
    if pdf_exists and pdf_path:
        try:
        await message.answer_document(
                document=FSInputFile(pdf_path),
            caption=f"📄 Детали заказа #{order_id}"
        )
        except Exception as e:
             logging.error(f"Ошибка при отправке PDF пользователю {message.from_user.id} для заказа {order_id}: {e}")

    # Формирование сообщения для менеджера
    manager_message = (
        f"🔔 <b>Новый заказ! #{order_id}</b>\n\n"
        f"👤 <b>Клиент:</b> {order_data.get('full_name')} (@{order_data.get('username')})\n"
        f"📞 <b>Телефон:</b> {order_data.get('phone')}\n"
        f"📅 <b>Дата:</b> {order_date}\n"
        f"📍 <b>Район:</b> {district_name}\n"
        f"📏 <b>Глубина:</b> {order_data.get('depth')} м\n"
        f"🧱 <b>Тип грунта:</b> {order_data.get('ground_type')}\n"
        f"💰 <b>Стоимость бурения:</b> {order_data.get('drilling_cost')} ₽\n"
    )
    
    # Добавляем информацию об оборудовании, если есть
    if order_data.get('equipment_details'):
        manager_message += f"\n🔧 <b>Оборудование:</b>\n"
        for detail in order_data.get('equipment_details'):
            manager_message += f"- {detail}\n"
        manager_message += f"💰 <b>Стоимость оборудования:</b> {order_data.get('equipment_cost')} ₽\n"
        
    manager_message += f"\n💰 <b>Общая стоимость:</b> {order_data.get('total_cost')} ₽"

    # Отправка уведомления менеджеру
    try:
        await bot.send_message(MANAGER_CHANNEL_ID, manager_message, parse_mode='HTML')
        # Отправка PDF менеджеру, если он создан
        if pdf_exists and pdf_path:
             await bot.send_document(
                 MANAGER_CHANNEL_ID,
                 document=FSInputFile(pdf_path),
                 caption=f"📄 Детали заказа #{order_id} для менеджера"
             )
    except Exception as e:
        logging.error(f"Ошибка при отправке уведомления менеджеру в канал {MANAGER_CHANNEL_ID} для заказа {order_id}: {e}")
    
    # Сброс состояния
    await state.clear()
    
    # Отправка главного меню
    await message.answer(
        "Выберите действие:",
        reply_markup=get_main_keyboard()
    )

def save_order(order_data):
    """
    Сохранение заказа в JSON-файл
    """
    # Путь к файлу с заказами
    orders_file = os.path.join("data", "orders.json")
    
    # Загрузка существующих заказов
    if os.path.exists(orders_file):
        with open(orders_file, "r", encoding="utf-8") as file:
            data = json.load(file)
    else:
        data = {"orders": []}
    
    # Добавление нового заказа
    data["orders"].append(order_data)
    
    # Сохранение обновленных данных
    with open(orders_file, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

async def send_user_orders(message: Message):
    """
    Отправка списка заказов пользователя
    """
    user_id = message.from_user.id
    
    # Путь к файлу с заказами
    orders_file = os.path.join("data", "orders.json")
    
    # Проверка существования файла с заказами
    if not os.path.exists(orders_file):
        await message.answer("У вас пока нет заказов.")
        return
    
    # Загрузка заказов
    with open(orders_file, "r", encoding="utf-8") as file:
        data = json.load(file)
    
    # Фильтрация заказов пользователя
    user_orders = [order for order in data.get("orders", []) if order.get("user_id") == user_id]
    
    if not user_orders:
        await message.answer("У вас пока нет заказов.")
        return
    
    # Сортировка заказов по дате (от новых к старым)
    user_orders.sort(key=lambda x: datetime.strptime(x.get("order_date", "01.01.2000 00:00"), "%d.%m.%Y %H:%M"), reverse=True)
    
    # Отправляем каждый заказ отдельным сообщением с кнопкой для скачивания PDF
    for order in user_orders:
        order_id = order.get("order_id", "N/A")
        order_date = order.get("order_date", "N/A")
        district = order.get("district_name", "N/A")
        depth = order.get("depth", "N/A")
        total_cost = order.get("total_cost", "N/A")
        status = order.get("status", "new")
        
        # Статус заказа
        status_emoji = "🆕" if status == "new" else "✅" if status == "completed" else "🔄"
        
        message_text = (
            f"{status_emoji} <b>Заказ #{order_id}</b>\n"
            f"📅 Дата: {order_date}\n"
            f"🏙️ Район: {district}\n"
            f"📏 Глубина: {depth} м\n"
            f"💰 Стоимость: {total_cost} ₽\n"
        )
        
        # Создаем клавиатуру с кнопкой для скачивания PDF
        keyboard = InlineKeyboardBuilder()
        keyboard.add(InlineKeyboardButton(
            text="📄 Скачать PDF",
            callback_data=f"get_pdf_{order_id}"
        ))
        
        await message.answer(message_text, reply_markup=keyboard.as_markup(), parse_mode='HTML')

@router.callback_query(F.data.startswith("get_pdf_"))
async def get_order_pdf(callback: CallbackQuery):
    """
    Обработчик запроса на получение PDF-файла заказа
    """
    try:
        # Получение ID заказа из callback_data
        order_id = callback.data.replace("get_pdf_", "")
        
        # Путь к файлу с заказами
        orders_file = os.path.join("data", "orders.json")
        
        # Проверка существования файла с заказами
        if not os.path.exists(orders_file):
            await callback.answer("Файл с заказами не найден", show_alert=True)
            return
        
        # Загрузка заказов
        with open(orders_file, "r", encoding="utf-8") as file:
            data = json.load(file)
        
        # Поиск заказа по ID
        order = next((o for o in data.get("orders", []) if o.get("order_id") == order_id), None)
        
        if not order:
            await callback.answer("Заказ не найден", show_alert=True)
            return
        
        # Проверка, принадлежит ли заказ текущему пользователю
        if order.get("user_id") != callback.from_user.id:
            await callback.answer("У вас нет доступа к этому заказу", show_alert=True)
            return
        
        # Генерация PDF с деталями заказа
        try:
            pdf_path = generate_order_pdf(order)
            
            # Отправка PDF-файла
            await callback.message.answer_document(
                document=FSInputFile(pdf_path),
                caption=f"📄 Детали заказа #{order_id}"
            )
            
            await callback.answer()
        except Exception as e:
            await callback.answer(f"Ошибка при создании PDF", show_alert=True)
            import logging
            logging.error(f"Ошибка при создании PDF: {str(e)}")
    except Exception as e:
        await callback.answer("Произошла ошибка", show_alert=True)
        import logging
        logging.error(f"Ошибка при обработке запроса PDF: {str(e)}")

