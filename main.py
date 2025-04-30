import sys
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from PyQt5 import QtWidgets, QtCore
import uiDesign.design as design
import os
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
load_dotenv()


class EmailSenderApp(QtWidgets.QMainWindow, design.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        
        # Проверяем наличие элементов перед подключением
        if hasattr(self, 'sendButton'):  # если кнопка есть в UI
            self.sendButton.clicked.connect(self.send_emails)
        else:
            print("Warning: sendButton not found in UI")
            
        if hasattr(self, 'addDeadlineButton'):
            self.addDeadlineButton.clicked.connect(self.add_deadline)
        else:
            print("Warning: addDeadlineButton not found in UI")
            
        # Настройка таблицы дедлайнов
        self.deadlinesTable.setColumnCount(2)
        self.deadlinesTable.setHorizontalHeaderLabels(["Дедлайн", "Описание"])
        self.deadlinesTable.horizontalHeader().setStretchLastSection(True)

        #Список дедлайнов
        self.deadlines = []

        #Настройки SMTP 
        self.smtp_settings = {
            'server': 'smtp.gmail.com',
            'port': 587,
            'login': os.getenv('GMAIL_USER'),
            'password': os.getenv('GMAIL_PASSWORD')
        }

    def add_deadline(self):
        """Добавление нового дедлайна"""
        deadline_date = self.deadlineDate.date().toString("dd.MM.yyyy")
        deadline_time = self.deadlineTime.time().toString("hh:mm")
        deadline_datetime_str = f"{deadline_date} {deadline_time}"
        deadline_description = self.deadlineDescription.toPlainText()
        
        try:
            deadline_datetime = datetime.strptime(deadline_datetime_str, "%d.%m.%Y %H:%M")
            self.deadlines.append({
                'datetime': deadline_datetime,
                'description': deadline_description,
                'notified': False
            })
            
            # Добавляем в таблицу
            row_position = self.deadlinesTable.rowCount()
            self.deadlinesTable.insertRow(row_position)
            self.deadlinesTable.setItem(row_position, 0, QtWidgets.QTableWidgetItem(deadline_datetime_str))
            self.deadlinesTable.setItem(row_position, 1, QtWidgets.QTableWidgetItem(deadline_description))
            
            self.statusbar.showMessage(f"Дедлайн добавлен: {deadline_datetime_str}", 3000)
            
        except ValueError as e:
            self.statusbar.showMessage(f"Ошибка формата даты: {str(e)}", 5000)
    
    def check_deadlines(self):
        """Проверка дедлайнов и отправка уведомлений"""
        now = datetime.now()
        
        for deadline in self.deadlines:
            if not deadline['notified'] and now >= deadline['datetime']:
                # Отправляем уведомление
                subject = f"Напоминание: дедлайн {deadline['datetime'].strftime('%d.%m.%Y %H:%M')}"
                body = f"""\
                <html>
                  <body>
                    <p>Добрый день!</p>
                    <p>Напоминаем о дедлайне:</p>
                    <p><strong>{deadline['description']}</strong></p>
                    <p>Дата и время: {deadline['datetime'].strftime('%d.%m.%Y %H:%M')}</p>
                    <p>Пожалуйста, не забудьте выполнить задачу в срок.</p>
                  </body>
                </html>
                """
                
                if self.send_email(subject, body):
                    deadline['notified'] = True
                    self.statusbar.showMessage(f"Уведомление о дедлайне отправлено: {deadline['description']}", 3000)
    
    def send_emails(self):
        """Отправка писем по шаблону (шаблон можно менять)"""
        recipients = self.recipientsText.toPlainText().split(',')
        subject = self.subjectText.text()
        template = self.templateText.toPlainText()

        for recipient in recipients:
            recipient = recipient.strip()
            if recipient:
                # Персонализация шаблона
                personalized_body = template.replace("{имя}", recipient.split('@')[0])
                
                if self.send_email(subject, personalized_body, recipient):
                    self.statusbar.showMessage(f"Письмо отправлено: {recipient}", 3000)
                else:
                    self.statusbar.showMessage(f"Ошибка отправки: {recipient}", 5000)
    
    def send_email(self, subject, body, recipient=None):
        """Функция отправки email"""
        if recipient is None:
            recipient = self.defaultRecipient.text() or self.smtp_settings['login']
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.smtp_settings['login']
            msg['To'] = recipient
            msg['Subject'] = subject
            
            # Добавляем HTML тело письма
            msg.attach(MIMEText(body, 'html'))
            
            # Подключение и отправка
            with smtplib.SMTP(self.smtp_settings['server'], self.smtp_settings['port']) as server:
                server.starttls()
                server.login(self.smtp_settings['login'], self.smtp_settings['password'])
                server.send_message(msg)
            
            return True
        except Exception as e:
            print(f"Ошибка отправки письма: {str(e)}")
            return False
        

# class exampleApp(QtWidgets.QMainWindow, design.Ui_MainWindow):
#     def __init__(self):
#         super().__init__()
#         self.setupUi(self)

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = EmailSenderApp()
    window.show()
    app.exec_()

if __name__ == '__main__': 
    main()