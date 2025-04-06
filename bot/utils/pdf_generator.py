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

# Пути к шрифтам
FONT_DIR = "fonts"
FONT_REGULAR_PATH = os.path.join(FONT_DIR, "DejaVuSansCondensed.ttf")
FONT_BOLD_PATH = os.path.join(FONT_DIR, "DejaVuSansCondensed-Bold.ttf") # Добавили путь к жирному

# Функция для генерации PDF заказа
def generate_order_pdf(order_data: dict) -> str | None:
    """
    Генерация PDF-файла с данными заказа и загрузка в Vercel Blob
    Возвращает URL файла в Vercel Blob или None в случае ошибки.
    """
    if not BLOB_READ_WRITE_TOKEN:
        print("Ошибка: Токен BLOB_READ_WRITE_TOKEN не найден в переменных окружения.")
        return None

    # Проверяем наличие файлов шрифтов
    fonts_available = os.path.exists(FONT_REGULAR_PATH) and os.path.exists(FONT_BOLD_PATH)
    use_dejavu = True

    if not fonts_available:
        print(f"Ошибка: Файлы шрифтов DejaVu не найдены в {FONT_DIR}")
        # Пытаемся использовать Arial как запасной вариант
        use_dejavu = False
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font('Arial', '', 12) # Используем Arial
            print("Предупреждение: Используется запасной шрифт Arial.")
        except RuntimeError:
             print("Критическая ошибка: Ни DejaVu, ни Arial не доступны.")
             return None # Не можем создать PDF
    else:
        # Создание PDF в памяти
        pdf = FPDF()
        pdf.add_page()
        # Добавляем ОБА шрифта: обычный и жирный
        try:
            pdf.add_font('DejaVu', '', FONT_REGULAR_PATH, uni=True)
            pdf.add_font('DejaVu', 'B', FONT_BOLD_PATH, uni=True) # Добавляем жирный стиль
            pdf.set_font('DejaVu', '', 12) # Устанавливаем DejaVu по умолчанию
        except Exception as e:
            print(f"Критическая ошибка при добавлении шрифтов DejaVu: {e}")
            print("Попытка использовать Arial...")
            use_dejavu = False
            try:
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font('Arial', '', 12)
                print("Предупреждение: Используется запасной шрифт Arial.")
            except RuntimeError:
                print("Критическая ошибка: Ни DejaVu, ни Arial не доступны.")
                return None

    # Определяем имя шрифта для использования (DejaVu или Arial)
    font_family = 'DejaVu' if use_dejavu else 'Arial'

    # Заголовок
    pdf.set_font(font_family, 'B', 16) # Используем жирный стиль выбранного шрифта
    pdf.cell(0, 10, 'Заказ на бурение скважины', ln=True, align='C')
    pdf.ln(10)

    # Основная информация
    pdf.set_font(font_family, 'B', 14)
    pdf.cell(0, 10, 'Информация о заказе:', ln=True)
    pdf.set_font(font_family, '', 12)

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
    equipment_details = order_data.get("equipment_details", []) # Эта переменная сейчас не используется, но оставим
    adapter_info = order_data.get("adapter_info", {})
    caisson_info = order_data.get("caisson_info", {})

    if adapter_info or caisson_info:
        pdf.set_font(font_family, 'B', 14)
        pdf.cell(0, 10, 'Выбранное оборудование:', ln=True)
        pdf.set_font(font_family, '', 12)

        if adapter_info:
            pdf.cell(0, 10, f"Адаптер: {adapter_info.get('name', 'Не указан')} - {adapter_info.get('price', 0)} ₽", ln=True)

        if caisson_info:
            pdf.cell(0, 10, f"Кессон: {caisson_info.get('name', 'Не указан')} - {caisson_info.get('price', 0)} ₽", ln=True)

        pdf.cell(0, 10, f"Стоимость оборудования: {str(order_data.get('equipment_cost', 0))} ₽", ln=True)
        pdf.ln(5)

    # Общая стоимость
    pdf.set_font(font_family, 'B', 14)
    pdf.cell(0, 10, f"ОБЩАЯ СТОИМОСТЬ: {str(order_data.get('total_cost', 0))} ₽", ln=True)
    pdf.ln(10)

    # Информация о клиенте
    pdf.set_font(font_family, 'B', 14)
    pdf.cell(0, 10, 'Информация о клиенте:', ln=True)
    pdf.set_font(font_family, '', 12)

    pdf.cell(0, 10, f"ФИО: {str(order_data.get('full_name', 'Не указано'))}", ln=True)
    pdf.cell(0, 10, f"Телефон: {str(order_data.get('phone', 'Не указан'))}", ln=True)

    # Получение PDF как байтов
    try:
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
    except UnicodeEncodeError:
        print("Предупреждение: Ошибка кодирования PDF в latin-1, пробую UTF-8")
        pdf_bytes = pdf.output(dest='S').encode('utf-8')
    except Exception as e:
        print(f"Критическая ошибка при генерации байтов PDF: {e}")
        return None

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
    return None

