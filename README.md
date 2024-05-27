# <img alt="RDTS.ico" height="22" src="RDTS.ico" width="22"/>  RDTS server

#### Инструкция по развертыванию

- Предварительно установите программу `Docker Desktop` по ссылке https://www.docker.com/products/docker-desktop/ и откройте его
- Перейдите в корневую директорию `radiation_detector_testing_system-server-`
- Введите команду `docker-compose up -d --build` для запуска сервера и базы данных
- Далее введите команду `docker exec -it backend bash` для выполнения команд внутри контейнера `backend`
- Здесь введите команду `python3 server/rdtsserver/scripts/create_roles.py` для инициализации ролей в базе данных
- Отредактируйте файл `server/rdtsserver/scripts/create_admin.py`, задав логин и пароль по своему желанию
- Запустите скрипт командой `python3 server/rdtsserver/scripts/create_admin.py`
- Теперь сервер запущен и готов к работе



