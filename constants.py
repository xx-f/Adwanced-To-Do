from PyQt5 import QtCore, QtGui

# Цвета
COLORS = {
    'primary': '#4a6fa5',
    'secondary': '#166088',
    'background': '#f5f7fa',
    'text': '#333333',
    'light_text': '#ffffff'
}

# Шрифты
FONTS = {
    'title': QtGui.QFont('Arial', 14, QtGui.QFont.Bold),
    'subtitle': QtGui.QFont('Arial', 10),
    'regular': QtGui.QFont('Arial', 9)
}

# Размеры
WINDOW_SIZE = QtCore.QSize(1100, 650)
PADDING = 20
SPACING = 15

# Тексты
TEXTS = {
    'window_title': 'Advanced To Do',
    'main_label': 'Advanced To Do',
    'group_box_title': 'Создание напоминания',
    'name_label': 'Краткое название для напоминания',
    'notification_text': 'Получить уведомление',
    'email_label': 'Email получателя:',
    'email_placeholder': 'example@email.com',
    'send_button': 'Отправить',
    'body_placeholder': 'Здесь будут отображаться ваши напоминания' 
}

# Размеры и позиции элементов
WINDOW_SIZE = QtCore.QSize(800, 400)
GROUP_BOX_POS = QtCore.QRect(10, 40, 780, 350)

# Элементы ввода
INPUT_FIELDS = {
    'name': {
        'geometry': QtCore.QRect(20, 60, 300, 30),
        'label': 'Краткое название для напоминания',
        'label_geometry': QtCore.QRect(20, 40, 250, 16)
    },
    'datetime': {
        'geometry': QtCore.QRect(20, 120, 150, 25)
    },
    'notification': {
        'geometry': QtCore.QRect(20, 100, 150, 20),
        'text': 'Получить уведомление'
    },
    'email': {
        'input_geometry': QtCore.QRect(20, 180, 250, 25),
        'label': 'Email получателя:',
        'label_geometry': QtCore.QRect(20, 160, 150, 16),
        'placeholder': 'Введите email получателя'
    },
    'send_button': {
        'geometry': QtCore.QRect(300, 250, 120, 40),
        'text': 'Отправить'
    },
    'main_body': {
        'geometry': QtCore.QRect(550, 40, 500, 450), 
        'min_height': 300 
    }
}
