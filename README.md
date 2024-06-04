# <img alt="RDTS.ico" height="22" src="RDTS.ico" width="22"/>  RDTS server

#### Инструкция по развертыванию

- Предварительно установите программу `Docker Desktop` по ссылке https://www.docker.com/products/docker-desktop/ и откройте её
- Перейдите в корневую директорию `radiation_detector_testing_system-server-`
- Введите команду `docker-compose up -d` для запуска сервера и базы данных
- Далее введите команду `docker exec -it backend bash` для выполнения команд внутри контейнера `backend` ИЛИ войдите в Docker Desktop в раздел Containers и выберите контейнер backend
- Здесь введите команду `python3 server/rdtsserver/scripts/create_roles.py` для инициализации ролей в базе данных ИЛИ в приложении в контейнере backend выберите Exec и введите ту же команду
- Здесь же отредактируйте файл `server/rdtsserver/scripts/create_admin.py`, задав логин и пароль по своему желанию ИЛИ в приложении в контейнере backend выберите Files, найдите этот файл и отредактируйте его
- Запустите скрипт командой `python3 server/rdtsserver/scripts/create_admin.py` ИЛИ в приложении в контейнере backend выберите Exec и введите ту же команду
- Выйдите из контейнера командой `exit`
- Теперь сервер запущен и готов к работе



