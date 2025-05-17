import sys
from datetime import datetime
from PyQt5 import QtWidgets, QtCore, QtGui
from uiDesign.design import Ui_MainWindow
from constants import COLORS, FONTS
import os
from dotenv import load_dotenv
import logging
import yagmail
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from database import *
from fpdf import FPDF
import sqlite3


create_table()


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
load_dotenv()


class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, self._to_latin1('История напоминаний (из базы данных)'), 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, self._to_latin1(f'Страница {self.page_no()}'), 0, 0, 'C')

    def _to_latin1(self, text):
        """Конвертирует текст в latin-1 с заменой неподдерживаемых символов"""
        if isinstance(text, str):
            return text.encode('latin-1', errors='replace').decode('latin-1')
        return str(text)

    def safe_multi_cell(self, w, h, txt, border=0, align='J', fill=False):
        """Безопасное добавление текста с обработкой кириллицы"""
        safe_txt = self._to_latin1(txt)
        self.multi_cell(w, h, safe_txt, border, align, fill)


class EmailSenderApp(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setMinimumSize(1000, 600)

        # Инициализация планировщика
        self.scheduler = BackgroundScheduler(daemon=True)
        self.scheduler.start()
        
        # Инициализация
        self.deadlines = []
        self.yag = None
        
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
        subject = "Напоминание: " + deadline['description']
        
        details_html = f"<p><strong>Подробности:</strong> {deadline['details']}</p>" if deadline['details'] else ""
        body = f"""
        <h2>Напоминание</h2>
        <p><strong>Дата и время:</strong> {deadline['datetime'].strftime('%d.%m.%Y %H:%M')}</p>
        <p><strong>Описание:</strong> {deadline['description']}</p>
        {details_html}
        """
        
        job_id = f"email_{deadline['datetime'].timestamp()}_{recipient}"
        
        self.scheduler.add_job(
            self.send_email,
            DateTrigger(run_date=deadline['datetime']),
            args=[subject, body, recipient],
            id=job_id,
            misfire_grace_time=60
        )
        logging.info(f"Задача {job_id} запланирована на {deadline['datetime']}")

    def send_email(self, subject, body, recipient):
        """Отправляет email (вызывается планировщиком)"""
        try:
            if self.yag is None:
                self.yag = yagmail.SMTP(
                    user=os.getenv('YANDEX_LOGIN'),
                    password=os.getenv('YANDEX_PASSWORD'),
                    host='smtp.yandex.ru',
                    port=465,
                    smtp_ssl=True
                )
            
            self.yag.send(
                to=recipient,
                subject=subject,
                contents=body
            )
            logging.info(f"Письмо успешно отправлено на {recipient}")
            
            if hasattr(self, 'isVisible') and self.isVisible():
                QtWidgets.QMessageBox.information(
                    self,
                    "Успешная отправка",
                    f"Письмо было отправлено на {recipient}"
                )
        except Exception as e:
            error_msg = f"Ошибка отправки: {str(e)}"
            logging.error(error_msg, exc_info=True)
            
            if hasattr(self, 'isVisible') and self.isVisible():
                QtWidgets.QMessageBox.critical(
                    self,
                    "Ошибка отправки",
                    error_msg
                )

    def export_db_to_pdf(self):
        """Экспортирует только данные из database.db в PDF с обработкой кириллицы"""
        try:
            # Подключаемся к базе данных
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            
            # Получаем все записи из базы данных
            cursor.execute("SELECT name, description, date FROM advToDo ORDER BY date DESC")
            db_data = cursor.fetchall()
            conn.close()

            if not db_data:
                QtWidgets.QMessageBox.information(self, "Информация", "База данных пуста")
                return

            # Создаем PDF документ
            pdf = PDF()
            pdf.add_page()
            pdf.set_font("Arial", size=10)

            # Добавляем информацию о источнике данных
            pdf.cell(0, 10, pdf._to_latin1("Данные экспортированы из database.db"), 0, 1)
            pdf.ln(5)

            # Добавляем данные из базы в PDF
            for name, description, date in db_data:
                try:
                    # Парсим дату из базы данных
                    date_obj = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
                    date_str = date_obj.strftime("%d.%m.%Y %H:%M")
                except:
                    date_str = date  # Если не удалось распарсить, оставляем как есть
                
                # Используем безопасный метод для добавления текста
                pdf.safe_multi_cell(0, 10, 
                    f"Дата: {date_str}\n"
                    f"Заголовок: {name}\n"
                    f"Описание: {description if description else 'Нет описания'}\n", 
                    border=1)
                pdf.ln(5)

            # Сохраняем файл
            file_name = f"database_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf.output(file_name)

            # Показываем сообщение об успехе
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Information)
            msg.setWindowTitle("Экспорт базы данных")
            msg.setText(f"Данные из database.db успешно экспортированы в PDF")
            msg.setInformativeText(f"Файл сохранен как: {file_name}")
            msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msg.exec_()

        except sqlite3.Error as e:
            QtWidgets.QMessageBox.critical(self, "Ошибка базы данных", 
                f"Ошибка при работе с базой данных:\n{str(e)}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Ошибка экспорта", 
                f"Не удалось экспортировать данные:\n{str(e)}")
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