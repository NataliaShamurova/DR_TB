2. Описание проекта
Функциональные возможности бота
Основные функции:
1.	Запись на прием: пользователи могут выбрать удобное время для записи к ветеринарному врачу.
2.	Просмотр заявок: бот позволяет пользователям просматривать свои активные заявки.
3.	Изменение записи: возможность корректировать время посещения.
4.	Удаление записи: функция удаления заявки, если необходимость в визите отпала.
Дополнительные функции:
1.	Валидация данных при записи, чтобы избежать ошибок (например, проверка на пересечение записей).

Меню пользователя
Реализованы инлайн-кнопки:
- запись на прием – при нажатии на кнопку пользователь может зарегистрироваться на определенную дату и время приема. 
Для дальнейшей коммуникации ему будет предложено ввести имя и номер телефона. При выборе конкретной даты есть возможность забронировать место на удобное ему время. 
При этом время, на которое уже кто-то записался для выбора недоступно.	
- О нас – просто информация о клинике
	- Получить список – возможность увидеть все свои заявки (их может быть несколько, на разное время и даты), изменять время посещения или дату и, при необходимости удалять их.
 

Панель администратора
Вход осуществляется через команду /admin. Чтобы добавить администратора нужно добавить в список id администраторов  
 

3.Архитектура и структура проекта
Структура проекта

1.	.venv – виртуальное окружение
2.	Папка Common 
text_for.py – файл, в котором хранится  подписи и информация описание «о нас»
3.	Папка db
      engine.py для настройки и инициализации подключения к базе данных в проекте с использованием SQLAlchemy. 
	models.py Этот файл содержит описание моделей для работы с базой данных в рамках Telegram-бота с использованием SQLAlchemy.
	Orm_query – содержит настройки основных параметров соединения с базой данных. Он предоставляет централизованный доступ к базе данных для всех моделей и операций с данными.
4.	Папка handlers
       handlers_admin: Модуль содержит обработчики для взаимодействия администратора с ботом.
      handlers_user: Модуль предназначен для обработки пользовательских запросов, обеспечивая доступ к функциям бота и обработку команд.
5.	Kbrd - папка с файлами настроек клавиатур
6.	Logs – папка с файлами логов
7.	Middlewares 
Файл db содержит промежуточные слои (middlewares) для обработки запросов и взаимодействия между ботом и внешними ресурсами. Отвечает за подключение к базе данных, выполнение запросов и управление данными.
8.	.env: Файл для хранения конфиденциальной информации, такой как токен бота, параметры подключения к базе данных и другие настройки. Используется для защиты чувствительных данных и удобной конфигурации проекта.
9.	Logging_config: файл с настройками логирования
10.	Main: Главный файл проекта, отвечающий за запуск Telegram-бота. Включает настройку и инициализацию всех компонентов, таких как обработчики, миддлвары и соединение с базой данных.

Логика работы бота
Логика работы бота основывается на взаимодействии пользователя с ботом через Telegram, обработке запросов с помощью обработчиков (handlers) и сохранении/извлечении данных из базы данных.
1.	Инициирование взаимодействия
Пользователь отправляет сообщение или команду боту в Telegram (например, команду /start или запрос на запись). Бот получает запрос через Telegram API и передает его в обработчик.
2.	Обработка запросов
Взаимодействие строится на следующих этапах:
o	Обработчики команд: направляют пользователя в соответствующий сценарий.
o	Обработчики данных: обрабатывают ввод пользователя, включая выбор даты, времени или подтверждение действий.
o	Валидация ввода: перед сохранением заявки бот проверяет данные пользователя на корректность (отсутствие пересечений записей).
3.	Взаимодействие с базой данных
o	Запись данных: при создании новой заявки данные пользователя (имя, время записи, контактная информация) сохраняются в базу данных.
o	Извлечение данных: бот запрашивает информацию из базы для отображения активных заявок пользователя.
o	Обновление данных: при изменении времени или других параметров заявки бот обновляет соответствующую запись в базе данных.
o	Удаление данных: пользователь может удалить заявку, что инициирует удаление соответствующей записи из базы.
4.	Ответ пользователю
После выполнения операции (создания, изменения или удаления записи) бот отправляет пользователю сообщение с результатом действия. Например
Таким образом, логика работы бота состоит в четком и последовательном обмене данными между пользователем, обработчиками запросов и базой данных, что обеспечивает стабильность и удобство работы системы.

Используемые библиотеки и технологии

SQLAlchemy	2.0.36	
aiofiles	24.1.0	
aiogram	3.15.0	
aiosqlite	0.20.0	
annotated-types	0.7.0	
magic-filter	1.0.12	
multidict	6.1.0	
pip	24.3.1	
propcache	0.2.0	
python-dotenv	1.0.1	
typing_extensions	4.12.2	
Asyncpg 0.29.0

Реализована возможность работы с базами данных как с SQlite, так и POStgreSQL