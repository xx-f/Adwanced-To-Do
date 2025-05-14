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

logging.basicConfig(level=logging.DEBUG)
load_dotenv()

class EmailSenderApp(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setMinimumSize(1000, 600)

        # Инициализация планировщика
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()

        # Проверка и инициализация элементов
        if not hasattr(self, 'sendButton'):
            self.sendButton = QtWidgets.QPushButton("Отправить", self)
            self.sendButton.setGeometry(340, 110, 100, 25)

        # Инициализация
        self.deadlines = []
        self.yag = None
        
        # Подключение сигналов
        self.checkBox.stateChanged.connect(self.toggle_notification)
        self.dateTimeEdit.setDateTime(QtCore.QDateTime.currentDateTime())
        self.sendButton.clicked.connect(self.send_notification)

    def toggle_notification(self, state):
        if state == QtCore.Qt.Checked:
            self.add_deadline()
    
    def add_deadline(self):
        deadline_text = self.tdname.toPlainText().strip()
        deadline_details = self.tdDetails.toPlainText().strip()  # Получаем подробное описание
        deadline_datetime = self.dateTimeEdit.dateTime().toPyDateTime()

        if not deadline_text:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Введите описание напоминания")
            self.checkBox.setChecked(False)
            return

        self.deadlines.append({
            'datetime': deadline_datetime,
            'description': deadline_text,
            'details': deadline_details,  # Сохраняем подробное описание
            'notified': False
        })

        current_text = self.tdmainbody.toPlainText()
        # Добавляем подробное описание, если оно есть
        details_text = f"\n{deadline_details}" if deadline_details else ""
        new_text = f"{deadline_datetime.strftime('%d.%m.%Y %H:%M')} - {deadline_text}{details_text}\n\n{current_text}"
        self.tdmainbody.setPlainText(new_text)
        self.tdname.clear()
        self.tdDetails.clear()  # Очищаем поле подробного описания
        self.tdmainbody.setLineWrapMode(QtWidgets.QTextEdit.WidgetWidth)
        self.tdmainbody.setWordWrapMode(QtGui.QTextOption.WordWrap)


    
    def send_notification(self):
        email = self.emailInput.text().strip()
        if not email:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Введите email получателя")
            return

        if not self.tdname.toPlainText().strip():
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Введите текст напоминания")
            return

        if not self.deadlines:
            self.add_deadline()

        # Получаем последнее добавленное напоминание
        last_deadline = self.deadlines[-1]
        
        # Планируем отправку на указанное время
        self.schedule_email(last_deadline, email)
        
        QtWidgets.QMessageBox.information(
            self, 
            "Успех", 
            f"Письмо запланировано на {last_deadline['datetime'].strftime('%d.%m.%Y %H:%M')}"
        )

    def schedule_email(self, deadline, recipient):
        """Планирует отправку email на указанное время"""
        subject = "Напоминание: " + deadline['description']
        # Добавляем подробное описание в тело письма, если оно есть
        details_html = f"<p><strong>Подробности:</strong> {deadline['details']}</p>" if deadline['details'] else ""
        body = f"""
        <h2>Напоминание</h2>
        <p><strong>Дата и время:</strong> {deadline['datetime'].strftime('%d.%m.%Y %H:%M')}</p>
        <p><strong>Описание:</strong> {deadline['description']}</p>
        {details_html}
        """
        
        self.scheduler.add_job(
            self.send_email,
            DateTrigger(run_date=deadline['datetime']),
            args=[subject, body, recipient],
            id=f"email_{deadline['datetime'].timestamp()}"
        )

    def send_email(self, subject, body, recipient):
        """Отправляет email (вызывается планировщиком)"""
        try:
            if self.yag is None:
                self.yag = yagmail.SMTP(
                    user=os.getenv('YANDEX_LOGIN'),
                    password=os.getenv('YANDEX_PASSWORD'),
                    host='smtp.yandex.ru',
                    port=465,
                    smtp_ssl=True,
                    oauth2_file=None,
                    soft_email_validation=False
                )
            
            self.yag.send(
                to=recipient,
                subject=subject,
                contents=body
            )
            logging.info(f"Письмо успешно отправлено на {recipient}")
        except Exception as e:
            logging.error(f"Ошибка отправки: {repr(e)}", exc_info=True)
            # Можно добавить уведомление пользователю об ошибке

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
    app.exec_()

if __name__ == "__main__":
    main()