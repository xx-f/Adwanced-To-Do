import sys
from datetime import datetime
from PyQt5 import QtWidgets, QtCore, QtGui
from uiDesign.design import Ui_MainWindow
from constants import COLORS, FONTS
import os
from dotenv import load_dotenv
import logging
import yagmail



logging.basicConfig(level=logging.DEBUG)

load_dotenv()

class EmailSenderApp(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        """
        Initializes the EmailSenderApp instance, setting up the UI and initializing its elements.
        
        Sets the minimum window size, creates the send button if it doesn't exist, and initializes the deadlines list and yagmail object.
        
        Connects the checkbox state change signal to the toggle_notification method, sets the current date and time in the date time edit field, and connects the send button click signal to the send_notification method.
        
        Parameters:
            None
        
        Returns:
            None
        """
        super().__init__()
        self.setupUi(self)

        self.setMinimumSize(1000, 600)

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
        """
        Includes or excludes the notification option.

        When the checkbox is checked, a new deadline is added to the list of deadlines, and the notification option is enabled.
        When the checkbox is unchecked, the notification option is disabled.
        """
        if state == QtCore.Qt.Checked:
            # Add a new deadline when the checkbox is checked
            self.add_deadline()
    
    def add_deadline(self):
        """Adds a new deadline to the list and updates the UI."""
        # Retrieve and trim the text from the name input field
        deadline_text = self.tdname.toPlainText().strip()
        # Retrieve the date and time from the dateTimeEdit widget
        deadline_datetime = self.dateTimeEdit.dateTime().toPyDateTime()
        
        # Check if the deadline description is empty
        if not deadline_text:
            # Show a warning message if the description is empty
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Введите описание напоминания")
            # Uncheck the notification checkbox
            self.checkBox.setChecked(False)
            return
            
        # Append the new deadline to the deadlines list
        self.deadlines.append({
            'datetime': deadline_datetime,
            'description': deadline_text,
            'notified': False
        })
        
        # Update the main body text with the new deadline
        current_text = self.tdmainbody.toPlainText()
        new_text = f"{deadline_datetime.strftime('%d.%m.%Y %H:%M')} - {deadline_text}\n{current_text}"
        self.tdmainbody.setPlainText(new_text)
        
        # Clear the name input field
        self.tdname.clear()
        
        # Set the line wrap mode for the main body text
        self.tdmainbody.setLineWrapMode(QtWidgets.QTextEdit.WidgetWidth)
        self.tdmainbody.setWordWrapMode(QtGui.QTextOption.WordWrap)
    
    def send_notification(self):
        """
        Sends a notification email with the latest deadline details.

        Checks if the email and reminder text are present. If not, prompts the user to enter the necessary information.
        Automatically adds a new deadline if the deadlines list is empty. Constructs the email subject and body
        and attempts to send the email. Notifies the user of success or failure.

        Returns:
            None
        """
        # Retrieve and trim the email from the input field
        email = self.emailInput.text().strip()
        if not email:
            # Show a warning message if the email field is empty
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Введите email получателя")
            return

        # Check if the reminder text is present
        if not self.tdname.toPlainText().strip():
            # Show a warning message if the reminder text is missing
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Введите текст напоминания")
            return

        # Automatically add a new deadline if none exist
        if not self.deadlines:
            self.add_deadline()

        # Construct the email subject and body
        subject = "Напоминание: " + self.deadlines[-1]['description']
        body = f"""
        <h2>Напоминание</h2>
        <p><strong>Дата и время:</strong> {self.deadlines[-1]['datetime'].strftime('%d.%m.%Y %H:%M')}</p>
        <p><strong>Описание:</strong> {self.deadlines[-1]['description']}</p>
        """
        
        # Attempt to send the email
        if self.send_email(subject, body, email):
            # Inform the user of successful email delivery
            QtWidgets.QMessageBox.information(self, "Успех", "Письмо успешно отправлено!")
        else:
            # Warn the user if the email could not be sent
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Не удалось отправить письмо")

    def send_email(self, subject, body, recipient):
        """
        Sends an email using yagmail SMTP client.

        Initializes the yagmail SMTP client on the first call if not already initialized. 
        Attempts to send an email with the given subject and body to the specified recipient. 
        Logs an error and returns False if the email cannot be sent.

        Parameters:
            subject (str): The subject of the email.
            body (str): The body content of the email.
            recipient (str): The recipient's email address.

        Returns:
            bool: True if the email was sent successfully, False otherwise.
        """
        try:
            # Initialize yagmail if it hasn't been initialized yet
            if self.yag is None:
                self.yag = yagmail.SMTP(
                    user=os.getenv('YANDEX_LOGIN'),
                    password=os.getenv('YANDEX_PASSWORD'),
                    host='smtp.yandex.ru',
                    port=465,
                    smtp_ssl=True,
                    oauth2_file=None,            # Skip config file check
                    soft_email_validation=False  # Disable soft email validation
                )
            
            # Send the email
            self.yag.send(
                to=recipient,
                subject=subject,
                contents=body
            )
            return True
        except Exception as e:
            # Log the error with exception information
            logging.error(f"Ошибка отправки: {repr(e)}", exc_info=True)
            return False

def main():
    """
    Initializes the application and its main window.

    Sets the Fusion style as the application style, then sets the application-wide
    palette to the custom colors defined in the COLORS dictionary. Finally, it
    creates the main window, shows it, and starts the application event loop.
    """
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Set the application-wide palette
    # The palette is used to set the colors for all widgets in the application
    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.Window, QtGui.QColor(COLORS['background']))
    palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor(COLORS['text']))
    palette.setColor(QtGui.QPalette.Button, QtGui.QColor(COLORS['primary']))
    palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor(COLORS['light_text']))
    palette.setColor(QtGui.QPalette.Base, QtGui.QColor(COLORS['background']))
    palette.setColor(QtGui.QPalette.Text, QtGui.QColor(COLORS['text']))
    app.setPalette(palette)
    
    # Create the main window
    window = EmailSenderApp()
    window.show()
    
    # Start the application event loop
    app.exec_()

if __name__ == "__main__":
    main()
