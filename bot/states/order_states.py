from aiogram.fsm.state import State, StatesGroup

class OrderStates(StatesGroup):
    """
    Состояния для процесса заказа
    """
    # Выбор района
    selecting_district = State()
    
    # Выбор глубины
    selecting_depth = State()
    
    # Выбор оборудования
    selecting_equipment = State()
    
    # Выбор компонентов оборудования
    selecting_components = State()
    
    # Подтверждение заказа
    confirming_order = State()
    
    # Ввод контактной информации
    entering_contact_info = State()
    
    # Завершение заказа
    completing_order = State()

