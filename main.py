import sys
from datetime import datetime
from PyQt5 import QtWidgets, QtCore, QtGui
from uiDesign.design import Ui_MainWindow
import os
from dotenv import load_dotenv
import logging
import yagmail  # Добавляем импорт yagmail

logging.basicConfig(level=logging.DEBUG)

load_dotenv()

class EmailSenderApp(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # Проверка и инициализация элементов
        if not hasattr(self, 'sendButton'):
            self.sendButton = QtWidgets.QPushButton("Отправить", self)
            self.sendButton.setGeometry(340, 110, 100, 25)

        # Инициализация
        self.deadlines = []
        self.yag = None  # Будет инициализирован при первой отправке
        
        # Подключение сигналов
        self.checkBox.stateChanged.connect(self.toggle_notification)
        self.dateTimeEdit.setDateTime(QtCore.QDateTime.currentDateTime())
        self.sendButton.clicked.connect(self.send_notification)

    def toggle_notification(self, state):
        """Включение/выключение уведомлений"""
        if state == QtCore.Qt.Checked:
            self.add_deadline()
    
    def add_deadline(self):
        """Добавление нового дедлайна"""
        deadline_text = self.tdname.toPlainText().strip()
        deadline_datetime = self.dateTimeEdit.dateTime().toPyDateTime()
        
        if not deadline_text:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Введите описание напоминания")
            self.checkBox.setChecked(False)
            return
            
        self.deadlines.append({
            'datetime': deadline_datetime,
            'description': deadline_text,
            'notified': False
        })
        
        current_text = self.tdmainbody.toPlainText()
        new_text = f"{deadline_datetime.strftime('%d.%m.%Y %H:%M')} - {deadline_text}\n{current_text}"
        self.tdmainbody.setPlainText(new_text)
        self.tdname.clear()
    
    def send_notification(self):
        email = self.emailInput.text().strip()
        if not email:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Введите email получателя")
            return

        if not self.tdname.toPlainText().strip():
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Введите текст напоминания")
            return

        # Автоматически добавляем в список дедлайнов
        if not self.deadlines:
            self.add_deadline()

        # Отправляем email
        subject = "Напоминание: " + self.deadlines[-1]['description']
        body = f"""
        <h2>Напоминание</h2>
        <p><strong>Дата и время:</strong> {self.deadlines[-1]['datetime'].strftime('%d.%m.%Y %H:%M')}</p>
        <p><strong>Описание:</strong> {self.deadlines[-1]['description']}</p>
        """
        
        if self.send_email(subject, body, email):
            QtWidgets.QMessageBox.information(self, "Успех", "Письмо успешно отправлено!")
        else:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Не удалось отправить письмо")

    def send_email(self, subject, body, recipient):
        try:
            # Инициализируем yagmail при первом вызове
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
            return True
        except Exception as e:
            logging.error(f"Ошибка отправки: {repr(e)}", exc_info=True)
            return False

def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Настройка палитры для тёмной темы
    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.Window, QtGui.QColor(53, 53, 53))
    palette.setColor(QtGui.QPalette.WindowText, QtCore.Qt.white)
    app.setPalette(palette)
    
    window = EmailSenderApp()
    window.show()
    app.exec_()

if __name__ == '__main__':
    main()