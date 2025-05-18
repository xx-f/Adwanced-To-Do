import sys
from PyQt5 import QtWidgets, QtCore, QtGui
from uiDesign.design import Ui_MainWindow
from constants import COLORS, FONTS
import os
from dotenv import load_dotenv
import logging
import yagmail
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
import pytz
from datetime import datetime, timedelta
from database import *
from fpdf import FPDF
import sqlite3
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


create_table()


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
load_dotenv()



class PDF(FPDF):
    def __init__(self):
        super().__init__()
        # Добавляем поддержку кириллицы через специальный шрифт
        self.add_page()
        self.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)
        self.add_font('DejaVu', 'B', 'DejaVuSans-Bold.ttf', uni=True)
        self.set_auto_page_break(auto=True, margin=15)
    
    def header(self):
        self.set_font('DejaVu', 'B', 14)
        self.cell(0, 10, 'История напоминаний', 0, 1, 'C')
        self.ln(5)
        
    def footer(self):
        self.set_y(-15)
        self.set_font('DejaVu', 'I', 8)
        self.cell(0, 10, f'Страница {self.page_no()}', 0, 0, 'C')

def export_db_to_pdf(self):
    """Экспортирует данные из database.db в PDF с поддержкой кириллицы"""
    try:
        # Подключаемся к базе данных
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name, description, date FROM advToDo ORDER BY date DESC")
        db_data = cursor.fetchall()
        conn.close()

        if not db_data:
            QtWidgets.QMessageBox.information(self, "Информация", "База данных пуста")
            return

        # Создаем PDF документ
        pdf = PDF()
        pdf.add_page()
        pdf.set_font('DejaVu', '', 10)

        # Информация о экспорте
        pdf.cell(0, 10, f'Дата экспорта: {datetime.now().strftime("%d.%m.%Y %H:%M")}', 0, 1)
        pdf.ln(10)

        # Данные из базы
        for name, description, date in db_data:
            try:
                date_obj = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
                date_str = date_obj.strftime("%d.%m.%Y %H:%M")
            except:
                date_str = date

            # Дата
            pdf.set_font('DejaVu', 'B', 10)
            pdf.cell(40, 10, 'Дата:', 0, 0)
            pdf.set_font('DejaVu', '', 10)
            pdf.cell(0, 10, date_str, 0, 1)
            
            # Название
            pdf.set_font('DejaVu', 'B', 10)
            pdf.cell(40, 10, 'Название:', 0, 0)
            pdf.set_font('DejaVu', '', 10)
            pdf.multi_cell(0, 10, name)
            
            # Описание
            pdf.set_font('DejaVu', 'B', 10)
            pdf.cell(40, 10, 'Описание:', 0, 0)
            pdf.set_font('DejaVu', '', 10)
            if description:
                pdf.multi_cell(0, 10, description)
            else:
                pdf.cell(0, 10, 'Нет описания', 0, 1)
            
            pdf.ln(5)

        # Сохраняем файл
        file_name = f"database_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf.output(file_name)

        # Показываем сообщение об успехе
        QtWidgets.QMessageBox.information(
            self,
            "Экспорт базы данных",
            f"Данные успешно экспортированы в:\n{file_name}"
        )

    except Exception as e:
        QtWidgets.QMessageBox.critical(
            self,
            "Ошибка экспорта",
            f"Не удалось экспортировать данные:\n{str(e)}"
        )

class EmailSenderApp(QtWidgets.QMainWindow, Ui_MainWindow):
    email_sent_signal = QtCore.pyqtSignal(str, str)  # recipient, time
    email_error_signal = QtCore.pyqtSignal(str)      # error_msg

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setMinimumSize(1000, 600)

        # Подключаем сигналы к слотам
        self.email_sent_signal.connect(self.show_email_sent_message)
        self.email_error_signal.connect(self.show_email_error_message)

        self.scheduler = BackgroundScheduler(
            timezone='Europe/Moscow',  # Укажите ваш часовой пояс
            daemon=True,
            job_defaults={
                'misfire_grace_time': 300,
                'coalesce': True,
                'max_instances': 3
            }
        )
        self.scheduler.start()
        
        self.deadlines = []
        self.yag = None  # Теперь не храним соединение постоянно
        
        # Подключение сигналов
        self.checkBox.stateChanged.connect(self.toggle_notification)
        self.dateTimeEdit.setDateTime(QtCore.QDateTime.currentDateTime())
        

        # Проверяем, существует ли кнопка sendButton перед подключением
        if hasattr(self, 'sendButton'):
            self.sendButton.clicked.connect(self.send_email_notification)
        else:
            logging.warning("Кнопка sendButton не найдена в интерфейсе")

        # Добавляем кнопку экспорта
        self.exportButton = QtWidgets.QPushButton("Экспорт БД в PDF", self.groupBox)
        self.exportButton.setGeometry(460, 140, 150, 25)
        self.exportButton.setFont(FONTS['regular'])
        self.exportButton.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['secondary']};
                color: {COLORS['light_text']};
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary']};
            }}
        """)
        self.exportButton.clicked.connect(self.export_db_to_pdf)

    def toggle_notification(self, state):
        if state == QtCore.Qt.Checked:
            self.add_deadline()
    
    def add_deadline(self):
        deadline_text = self.tdname.toPlainText().strip()
        deadline_details = self.tdDetails.toPlainText().strip()
        deadline_datetime = self.dateTimeEdit.dateTime().toPyDateTime()
        print(f"[DEBUG] Получено из интерфейса: {deadline_datetime}")


        if not deadline_text:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Введите описание напоминания")
            self.checkBox.setChecked(False)
            return

        self.deadlines.append({
            'datetime': deadline_datetime,
            'description': deadline_text,
            'details': deadline_details,
            'notified': False
        })

        insert_deadline(deadline_text, deadline_details, deadline_datetime)


        current_text = self.tdmainbody.toPlainText()

        details_text = f"\n{deadline_details}" if deadline_details else ""
        new_text = f"{deadline_datetime.strftime('%d.%m.%Y %H:%M')} - {deadline_text}{details_text}\n\n{current_text}"
        self.tdmainbody.setPlainText(new_text)
        self.tdname.clear()
        self.tdDetails.clear()
        self.tdmainbody.setLineWrapMode(QtWidgets.QTextEdit.WidgetWidth)
        self.tdmainbody.setWordWrapMode(QtGui.QTextOption.WordWrap)
        
        # Автоматически отжимаем чекбокс после создания дедлайна
        self.checkBox.setChecked(False)

    def send_email_notification(self):
        """Обработчик нажатия кнопки отправки"""
        email = self.emailInput.text().strip()
        if not email:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Введите email получателя")
            return

        if not self.tdname.toPlainText().strip():
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Введите текст напоминания")
            return

        if not self.deadlines:
            self.add_deadline()


        last_deadline = self.deadlines[-1]

        self.schedule_email(last_deadline, email)

        
        # Уведомление об успешной планировке
        success_msg = QtWidgets.QMessageBox()
        success_msg.setIcon(QtWidgets.QMessageBox.Information)
        success_msg.setWindowTitle("Успешно!")
        success_msg.setText(f"Напоминание запланировано!")
        success_msg.setInformativeText(
            f"Письмо будет отправлено на адрес:\n{email}\n"
            f"в указанное время:\n{last_deadline['datetime'].strftime('%d.%m.%Y %H:%M')}"
        )
        success_msg.exec_()

    def schedule_email(self, deadline, recipient):
        """Планирует отправку email на указанное время"""
        now = datetime.now()
        deadline_time = deadline['datetime']

        if deadline_time <= now:
            QtWidgets.QMessageBox.warning(
                self,
                "Ошибка",
                f"Укажите время в будущем!\n"
                f"Сейчас: {now.strftime('%d.%m.%Y %H:%M')}\n"
                f"Указано: {deadline_time.strftime('%d.%m.%Y %H:%M')}"
            )
            return

        subject = "Напоминание: " + deadline['description']
        body = f"""
        <h2>Напоминание</h2>
        <p><strong>Дата и время:</strong> {deadline_time.strftime('%d.%m.%Y %H:%M')}</p>
        <p><strong>Описание:</strong> {deadline['description']}</p>
        """

        job_id = f"email_{deadline_time.timestamp()}_{recipient}"

        try:
            self.scheduler.remove_job(job_id)
        except:
            pass
        
        # Передаем deadline_time вместо всего deadline
        self.scheduler.add_job(
            self.send_email,
            DateTrigger(run_date=deadline_time),
            args=[subject, body, recipient, deadline_time],  # Добавляем deadline_time в аргументы
            id=job_id
        )

        QtWidgets.QMessageBox.information(
            self,
            "Запланировано",
            f"Письмо будет отправлено в {deadline_time.strftime('%d.%m.%Y %H:%M')}"
        )
    def send_email(self, subject, body, recipient, deadline_time):
        """Отправляет email (вызывается планировщиком)"""
        try:
            yag = yagmail.SMTP(
                user=os.getenv('YANDEX_LOGIN'),
                password=os.getenv('YANDEX_PASSWORD'),
                host='smtp.yandex.ru',
                port=465,
                smtp_ssl=True
            )

            yag.send(to=recipient, subject=subject, contents=body)
            logging.info(f"Письмо успешно отправлено на {recipient}")

            # Используем переданное deadline_time
            self.email_sent_signal.emit(recipient, deadline_time.strftime('%d.%m.%Y %H:%M'))

        except Exception as e:
            error_msg = f"Ошибка отправки: {str(e)}"
            logging.error(error_msg, exc_info=True)
            self.email_error_signal.emit(error_msg)

        finally:
            if 'yag' in locals():
                try:
                    yag.close()
                except:
                    pass

    def export_db_to_pdf(self):
        """Экспортирует данные из database.db в PDF с поддержкой кириллицы"""
        try:
            # Подключаемся к базе данных
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute("SELECT name, description, date FROM advToDo ORDER BY date DESC")
            db_data = cursor.fetchall()
            conn.close()
    
            if not db_data:
                QtWidgets.QMessageBox.information(self, "Информация", "База данных пуста")
                return
    
            # Создаем PDF документ с поддержкой Unicode
            pdf = FPDF()
            pdf.add_page()
            
            # Добавляем шрифты DejaVu с поддержкой кириллицы
            pdf.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)
            pdf.add_font('DejaVu', 'B', 'DejaVuSans-Bold.ttf', uni=True)
            pdf.set_font('DejaVu', '', 10)
    
            # Заголовок
            pdf.set_font('DejaVu', 'B', 14)
            pdf.cell(0, 10, 'История напоминаний', 0, 1, 'C')
            pdf.ln(5)
    
            # Информация о экспорте
            pdf.set_font('DejaVu', '', 10)
            pdf.cell(0, 10, f'Дата экспорта: {datetime.now().strftime("%d.%m.%Y %H:%M")}', 0, 1)
            pdf.ln(10)
    
            # Данные из базы
            for name, description, date in db_data:
                try:
                    date_obj = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
                    date_str = date_obj.strftime("%d.%m.%Y %H:%M")
                except:
                    date_str = date
    
                # Дата
                pdf.set_font('DejaVu', 'B', 10)
                pdf.cell(40, 10, 'Дата:', 0, 0)
                pdf.set_font('DejaVu', '', 10)
                pdf.cell(0, 10, date_str, 0, 1)
                
                # Название
                pdf.set_font('DejaVu', 'B', 10)
                pdf.cell(40, 10, 'Название:', 0, 0)
                pdf.set_font('DejaVu', '', 10)
                pdf.multi_cell(0, 10, name)
                
                # Описание
                pdf.set_font('DejaVu', 'B', 10)
                pdf.cell(40, 10, 'Описание:', 0, 0)
                pdf.set_font('DejaVu', '', 10)
                if description:
                    pdf.multi_cell(0, 10, description)
                else:
                    pdf.cell(0, 10, 'Нет описания', 0, 1)
                
                pdf.ln(5)
    
            # Сохраняем файл
            file_name = f"database_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf.output(file_name)
    
            # Показываем сообщение об успехе
            QtWidgets.QMessageBox.information(
                self,
                "Экспорт базы данных",
                f"Данные успешно экспортированы в:\n{file_name}"
            )
    
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Ошибка экспорта",
                f"Не удалось экспортировать данные:\n{str(e)}"
            )
    def show_email_sent_message(self, recipient, deadline_time):
        """Показывает сообщение об успешной отправке (вызывается через сигнал)"""
        QtWidgets.QMessageBox.information(
            self,
            "Успешно!",
            f"Письмо отправлено на {recipient}\nВремя: {deadline_time}"
        )

    def show_email_error_message(self, error_msg):
        """Показывает сообщение об ошибке (вызывается через сигнал)"""
        QtWidgets.QMessageBox.critical(
            self,
            "Ошибка отправки",
            error_msg
        )
def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    
    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.Window, QtGui.QColor(COLORS['background']))
    palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor(COLORS['text']))
    palette.setColor(QtGui.QPalette.Button, QtGui.QColor(COLORS['primary']))
    palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor(COLORS['light_text']))
    palette.setColor(QtGui.QPalette.Base, QtGui.QColor(COLORS['background']))
    palette.setColor(QtGui.QPalette.Text, QtGui.QColor(COLORS['text']))
    app.setPalette(palette)
    
    window = EmailSenderApp()
    window.show()
    app.aboutToQuit.connect(window.scheduler.shutdown)
    sys.exit(app.exec_())
if __name__ == "__main__":
    main()