from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.keyboards.common_kb import get_main_keyboard
from bot.states.order_states import OrderStates

# Создание роутера
router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    """
    Обработчик команды /start
    """
    await message.answer(
        f"👋 Здравствуйте, {message.from_user.first_name}!\n\n"
        f"Я бот для расчета стоимости бурения скважин.\n"
        f"Выберите действие на клавиатуре ниже или воспользуйтесь командой /help для получения справки.",
        reply_markup=get_main_keyboard()
    )

@router.message(Command("help"))
@router.message(F.text == "ℹ️ Помощь")
async def cmd_help(message: Message):
    """
    Обработчик команды /help
    """
    help_text = (
        "🔍 <b>Как пользоваться ботом:</b>\n\n"
        "1. Нажмите кнопку <b>\"🔍 Новый расчет\"</b> для начала расчета\n"
        "2. Выберите район бурения\n"
        "3. Выберите необходимую глубину\n"
        "4. Выберите требуемое оборудование\n"
        "5. Подтвердите заказ\n\n"
        "📋 <b>Доступные команды:</b>\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать справку\n"
        "/cancel - Отменить текущую операцию\n\n"
        "Если у вас возникли вопросы или проблемы, обратитесь к администратору."
    )
    
    await message.answer(help_text, reply_markup=get_main_keyboard(), parse_mode='HTML')

@router.message(Command("cancel"))
@router.callback_query(F.data == "cancel")
async def cmd_cancel(message_or_query: Message | CallbackQuery, state: FSMContext):
    """
    Обработчик команды /cancel и кнопки "Отмена"
    """
    # Сброс состояния
    await state.clear()
    
    if isinstance(message_or_query, CallbackQuery):
        await message_or_query.message.edit_text(
            "❌ Операция отменена. Выберите действие на клавиатуре ниже.",
        )
        await message_or_query.message.answer(
            "Главное меню",
            reply_markup=get_main_keyboard()
        )
        await message_or_query.answer()
    else:
        await message_or_query.answer(
            "❌ Операция отменена. Выберите действие на клавиатуре ниже.",
            reply_markup=get_main_keyboard()
        )

@router.message(F.text == "🔍 Новый расчет")
async def new_calculation(message: Message, state: FSMContext):
    """
    Обработчик кнопки "Новый расчет"
    """
    # Переход к выбору района
    await state.set_state(OrderStates.selecting_district)
    
    # Импорт здесь для избежания циклических импортов
    from bot.handlers.district import send_district_selection
    
    await send_district_selection(message, state)

@router.message(F.text == "📋 Мои заказы")
async def my_orders(message: Message):
    """
    Обработчик кнопки "Мои заказы"
    """
    # Импорт здесь для избежания циклических импортов
    from bot.handlers.order import send_user_orders
    
    await send_user_orders(message)

