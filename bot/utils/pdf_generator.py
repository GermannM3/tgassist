from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
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

# Регистрация шрифтов
def register_fonts():
    """
    Регистрация шрифтов для PDF
    """
    fonts_dir = os.path.join("bot", "utils", "fonts")
    os.makedirs(fonts_dir, exist_ok=True) # Убедимся, что директория существует
    
    # Пути к файлам шрифтов
    dejavu_path = os.path.join(fonts_dir, "DejaVuSans.ttf")
    dejavu_bold_path = os.path.join(fonts_dir, "DejaVuSans-Bold.ttf")

    # Проверка наличия файлов шрифтов
    if os.path.exists(dejavu_path) and os.path.exists(dejavu_bold_path):
        pdfmetrics.registerFont(TTFont('DejaVuSans', dejavu_path))
        pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', dejavu_bold_path))
    else:
        # Если файлы шрифтов не найдены, можно вывести предупреждение или использовать запасные шрифты
        print("Предупреждение: Файлы шрифтов DejaVuSans не найдены в bot/utils/fonts/")
        # Можно зарегистрировать стандартные шрифты как запасной вариант
        # pdfmetrics.registerFont(TTFont('Times-Roman', 'Times-Roman')) 
        # pdfmetrics.registerFont(TTFont('Times-Bold', 'Times-Bold'))

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
            # pdf.cell(0, 10, f"Описание: {adapter_info.get('description', '')}", ln=True) # Убрал описание для краткости

        if caisson_info:
            pdf.cell(0, 10, f"Кессон: {caisson_info.get('name', 'Не указан')} - {caisson_info.get('price', 0)} ₽", ln=True)
            # pdf.cell(0, 10, f"Описание: {caisson_info.get('description', '')}", ln=True) # Убрал описание для краткости

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
    # ... (конец кода заполнения PDF)

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

def generate_analytics_pdf(analytics_data):
    """
    Генерация PDF-файла с аналитикой
    """
    # Создание директории для PDF, если её нет
    pdf_dir = os.path.join("data", "pdf")
    os.makedirs(pdf_dir, exist_ok=True)
    
    # Путь к файлу
    timestamp = int(time.time())
    filepath = os.path.join(pdf_dir, f"analytics_{timestamp}.pdf")
    
    # Создание документа
    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Содержимое документа
    content = []
    
    # Создание стилей
    styles = getSampleStyleSheet()
    
    # Проверяем, существует ли уже стиль Title
    if 'Title' not in styles:
        styles.add(ParagraphStyle(
            name='Title',
            parent=styles['Heading1'],
            fontSize=18,
            alignment=1,
            spaceAfter=12
        ))
    
    # Заголовок
    content.append(Paragraph("Аналитический отчет", styles['Title']))
    content.append(Spacer(1, 12))
    
    # Основная информация
    total_stats = analytics_data.get("total_stats", {})
    
    content.append(Paragraph("<b>Общая статистика:</b>", styles['Heading2']))
    content.append(Spacer(1, 6))
    
    # Таблица с общей статистикой
    data = []
    data.append(["Всего заказов:", str(total_stats.get("total_orders", 0))])
    data.append(["Средняя стоимость заказа:", f"{total_stats.get('avg_order_cost', 0)} ₽"])
    data.append(["Общая выручка:", f"{total_stats.get('total_revenue', 0)} ₽"])
    data.append(["Средняя глубина:", f"{total_stats.get('avg_depth', 0)} м"])
    
    # Создание таблицы
    table = Table(data, colWidths=[200, 250])
    table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    content.append(table)
    content.append(Spacer(1, 20))
    
    # Популярные районы
    popular_districts = analytics_data.get("popular_districts", [])
    if popular_districts:
        content.append(Paragraph("<b>Популярные районы:</b>", styles['Heading2']))
        content.append(Spacer(1, 6))
        
        districts_data = [["Район", "Количество заказов"]]
        for district in popular_districts:
            districts_data.append([district.get("name", ""), str(district.get("count", 0))])
        
        districts_table = Table(districts_data, colWidths=[300, 150])
        districts_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        content.append(districts_table)
        content.append(Spacer(1, 20))
    
    # Популярные глубины
    popular_depths = analytics_data.get("popular_depths", [])
    if popular_depths:
        content.append(Paragraph("<b>Популярные глубины:</b>", styles['Heading2']))
        content.append(Spacer(1, 6))
        
        depths_data = [["Глубина (м)", "Количество заказов"]]
        for depth in popular_depths:
            depths_data.append([str(depth.get("depth", 0)), str(depth.get("count", 0))])
        
        depths_table = Table(depths_data, colWidths=[300, 150])
        depths_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        content.append(depths_table)
        content.append(Spacer(1, 20))
    
    # Популярное оборудование
    popular_equipment = analytics_data.get("popular_equipment", [])
    if popular_equipment:
        content.append(Paragraph("<b>Популярное оборудование:</b>", styles['Heading2']))
        content.append(Spacer(1, 6))
        
        equipment_data = [["Оборудование", "Количество заказов"]]
        for equipment in popular_equipment:
            equipment_data.append([equipment.get("name", ""), str(equipment.get("count", 0))])
        
        equipment_table = Table(equipment_data, colWidths=[300, 150])
        equipment_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        content.append(equipment_table)
    
    # Добавление даты создания отчета
    content.append(Spacer(1, 20))
    report_date = datetime.now().strftime("%d.%m.%Y %H:%M")
    content.append(Paragraph(f"Дата создания отчета: {report_date}", styles['Normal']))
    
    # Сборка документа
    doc.build(content)
    
    return filepath

