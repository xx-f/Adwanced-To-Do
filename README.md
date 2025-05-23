# "Advanced To-Do Editor"

**О проекте**


Десктопное приложение для управления задачами с расширенными возможностями редактирования. Сочетает простоту to-do листа с возможностью автоматической рассылки уведомлений на email.


**📋 Ключевые особенности**

-	Богатое редактирование: Добавление и форматирование текстовых напоминаний
-	Email-уведомления: Автоматическая отправка напоминаний с деталями задачи
-	Тёмная тема: Встроенная поддержка тёмного интерфейса
-	Работа с расписанием: Настройка дедлайнов через интерактивный календарь


**🛠 Технологический стек**
- 	Язык программирования: Python 3.11
- 	GUI-фреймворк: PyQt5
- 	Библиотеки:
	- 	yagmail – для работы с email
	- 	python-dotenv – управление переменными окружения
	- 	logging – система логирования ошибок
   	-	apscheduler - для отправки четко в нужную дату
      -	reportlab - для улучшения дизайна (не использовалась активно)
    - 	sqlite3 - формирование базы данных
      -	fpdf - для скачивания базы данных в формате pdf




**⚙️ Установка и настройка**
1.  Установка зависимостей
2. pip install PyQt5 yagmail python-dotenv apscheduler reportlab fpdf 		(рекомендуем устанавливать каждую отдельно, но можно сделать быстрее)
4.  Настройка почтового аккаунта
5. 	Создайте файл .env в корне проекта
6.	Добавьте учетные данные Yandex или любой другой почты:
	- YANDEX_LOGIN=ваш_логин
	- YANDEX_PASSWORD=ваш_пароль
 
###### для работы требуется создать пароль приложения в аккаунте yandex.



# 🖥 Использование приложения

**Интерфейс**

1.	Поле ввода названия – краткое описание задачи
2.	Календарь и время – выбор даты/времени дедлайна
3.	Чекбокс уведомлений – активация системы напоминаний
4.	История задач – список всех активных напоминаний
5.	Поле email – адрес получателя уведомлений

**Основные действия**

1.	Введите описание задачи
2.	Установите дату и время дедлайна
3.	Активируйте чекбокс "Получить уведомление"
4.	Введите email получателя
5.	Нажмите "Отправить"



# 🚨 Обработка ошибок

Приложение логирует все события в консоль.
В случае ошибок:

-	Проверьте наличие файла .env с корректными данными
-	Убедитесь в наличии интернет-соединения
-	Проверьте правильность формата email
-	Для детальной информации смотрите вывод в консоли


# 📄 Лицензия

Проект распространяется под лицензией MIT. Безоговорочные права на пользование и редактирование проекта имеют:

-	https://github.com/xx-f		Даниил Заячников
-	https://github.com/existenceXomg	Владислав Лыткин
-	https://github.com/teacher-ikt		Светлана Лазарева


# 📬 Контакты

Для обратной связи и предложений:

-	projectlytkin@yandex.ru
