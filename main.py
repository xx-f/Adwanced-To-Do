import sys
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from PyQt5 import QtWidgets, QtCore
import uiDesign.design as design

class EmailSenderApp(QtWidgets.QMainWindow, design.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # Настройка соединений кнопок с функциями
        self.sendButton.clicked.connect(self.send_emails)
        self.addDeadlineButton.clicked.connect(self.add_deadline)
        
        # Настройка таблицы дедлайнов
        self.deadlinesTable.setColumnCount(2)
        self.deadlinesTable.setHorizontalHeaderLabels(["Дедлайн", "Описание"])
        self.deadlinesTable.horizontalHeader().setStretchLastSection(True)

        #Список дедлайнов
        self.deadlines = []

        #Настройки SMTP 
        self.smtp_settings = {
            'server': 'gmail.com'
            
        }

# class exampleApp(QtWidgets.QMainWindow, design.Ui_MainWindow):
#     def __init__(self):
#         super().__init__()
#         self.setupUi(self)

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = exampleApp()
    window.show()
    app.exec_()

if __name__ == '__main__': 
    main()