# Пример запуска backend через Docker Compose

FastAPI, Redis, Celery worker, Flower и PostgreSQL для локального обучения.

Подробный разбор: [конспект Docker Compose](<../../Docker Compose — запуск backend и сервисов.md>).

Включи Docker Desktop с Linux-контейнерами. Выполняй команды из этой папки.

При первом запуске создай `.env`:

```powershell
Copy-Item .env.example .env
```

В Linux/WSL для этого используется `cp .env.example .env`.

Запуск:

```bash
docker compose config --quiet
docker compose up -d --build
```

- [Swagger](http://localhost:8000/docs) — API и отправка задач.
- [Проверка базы](http://localhost:8000/health/db) — подключение к PostgreSQL.
- [Flower](http://localhost:5555) — мониторинг Celery.

В Swagger отправь `POST /tasks/add` с числами `2` и `3`, затем проверь полученный ID через `GET /tasks/{task_id}`. После выполнения результат — `5`.

Запустить три worker-контейнера:

```bash
docker compose up -d --scale celery=3
```

В каждом worker-е по два процесса. Все они используют одну очередь Redis.

Логи и завершение:

```bash
docker compose logs -f celery
docker compose down
```

Обычный `down` сохраняет volumes PostgreSQL и Redis. Флаг `-v` удаляет их вместе с данными.
