import os
import time
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Использование Agg бэкенда для работы без GUI
from fpdf import FPDF
from vercel_blob import put # Импортируем функцию put
import io # Для работы с байтами в памяти

# Получаем токен из переменных окружения
BLOB_READ_WRITE_TOKEN = os.environ.get('BLOB_READ_WRITE_TOKEN')

# Функция для генерации PDF заказа (уже исправлена)
def generate_order_pdf(order_data: dict) -> str | None:
    """
    Генерация PDF-файла с данными заказа и загрузка в Vercel Blob
    Возвращает URL файла в Vercel Blob или None в случае ошибки.
    """
    if not BLOB_READ_WRITE_TOKEN:
        print("Ошибка: Токен BLOB_READ_WRITE_TOKEN не найден в переменных окружения.")
        return None

    # Создание PDF в памяти
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', '', 12)

    # Заголовок
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Заказ на бурение скважины', ln=True, align='C')
    pdf.ln(10)

    # Основная информация
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Информация о заказе:', ln=True)
    pdf.set_font('Arial', '', 12)

    # Данные заказа
    data = [
        ["№ заказа:", str(order_data.get("order_id", "Не указан"))],
        ["Дата заказа:", str(order_data.get("order_date", "-"))],
        ["Район:", str(order_data.get("district_name", "Не указан"))],
        ["Глубина:", f"{str(order_data.get('depth', 0))} м"],
        ["Тип грунта:", str(order_data.get("ground_type", "Не указан"))],
        ["Цена за метр:", f"{str(order_data.get('price_per_meter', 0))} ₽"],
        ["Стоимость бурения:", f"{str(order_data.get('drilling_cost', 0))} ₽"]
    ]
    # Вывод данных заказа
    for item in data:
        pdf.cell(60, 10, item[0], border=0)
        pdf.cell(0, 10, item[1], border=0, ln=True)
    pdf.ln(5)

    # Оборудование
    equipment_details = order_data.get("equipment_details", [])
    adapter_info = order_data.get("adapter_info", {})
    caisson_info = order_data.get("caisson_info", {})

    if equipment_details or adapter_info or caisson_info:
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Выбранное оборудование:', ln=True)
        pdf.set_font('Arial', '', 12)

        if adapter_info:
            pdf.cell(0, 10, f"Адаптер: {adapter_info.get('name', 'Не указан')} - {adapter_info.get('price', 0)} ₽", ln=True)

        if caisson_info:
            pdf.cell(0, 10, f"Кессон: {caisson_info.get('name', 'Не указан')} - {caisson_info.get('price', 0)} ₽", ln=True)

        pdf.cell(0, 10, f"Стоимость оборудования: {str(order_data.get('equipment_cost', 0))} ₽", ln=True)
        pdf.ln(5)

    # Общая стоимость
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, f"ОБЩАЯ СТОИМОСТЬ: {str(order_data.get('total_cost', 0))} ₽", ln=True)
    pdf.ln(10)

    # Информация о клиенте
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Информация о клиенте:', ln=True)
    pdf.set_font('Arial', '', 12)

    pdf.cell(0, 10, f"ФИО: {str(order_data.get('full_name', 'Не указано'))}", ln=True)
    pdf.cell(0, 10, f"Телефон: {str(order_data.get('phone', 'Не указан'))}", ln=True)

    # Получение PDF как байтов
    pdf_bytes = pdf.output(dest='S').encode('latin-1')

    # Имя файла в Blob хранилище
    filename = f"orders/order_{order_data.get('order_id', int(time.time()))}.pdf"

    try:
        # Загрузка в Vercel Blob
        blob_result = put(
            pathname=filename,
            body=pdf_bytes,
            options={'token': BLOB_READ_WRITE_TOKEN} # Передаем токен
        )
        print(f"PDF успешно загружен: {blob_result['url']}")
        return blob_result['url'] # Возвращаем URL загруженного файла
    except Exception as e:
        print(f"Ошибка при загрузке PDF в Vercel Blob: {e}")
        return None

# Функция для генерации PDF аналитики (Заглушка)
def generate_analytics_pdf(analytics_data):
    """
    Генерация PDF-файла с аналитикой (Требует переписывания на fpdf2)
    """
    print("Предупреждение: Функция generate_analytics_pdf еще не реализована с fpdf2.")
    # Тут должен быть код генерации PDF аналитики с использованием FPDF
    # В данный момент возвращаем None или можем создать пустой PDF как заглушку
    return None
    # Пример заглушки с пустым PDF:
    # pdf = FPDF()
    # pdf.add_page()
    # pdf.set_font('Arial', '', 12)
    # pdf.cell(0, 10, 'Аналитика (в разработке)', ln=True, align='C')
    # pdf_bytes = pdf.output(dest='S').encode('latin-1')
    # filename = f"analytics/analytics_{int(time.time())}.pdf"
    # try:
    #     blob_result = put(pathname=filename, body=pdf_bytes, options={'token': BLOB_READ_WRITE_TOKEN})
    #     return blob_result['url']
    # except Exception as e:
    #     print(f"Ошибка при загрузке заглушки PDF аналитики: {e}")
    #     return None

