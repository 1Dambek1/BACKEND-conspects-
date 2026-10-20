# Docker — образы и Dockerfile

Образ содержит всё, что нужно для запуска программы: Python, библиотеки, исходный код и настройки запуска. Для нашего backend соберём образ `backend-study:local`.

## Как читать название образа

```text
python:3.12-slim
redis:7-alpine
postgres:17-alpine
backend-study:local
```

До `:` указано имя, после — тег, то есть название варианта образа.

- `python:3.12-slim` — Python 3.12 с небольшим Linux-окружением.
- `redis:7-alpine` — Redis 7 на базе Alpine Linux.
- `postgres:17-alpine` — PostgreSQL 17 на базе Alpine Linux.
- `backend-study:local` — название нашего локального образа.

`latest` — обычный тег, который выбрал автор образа. Он не гарантирует конкретную версию. Теги могут обновляться; для привязки к точному содержимому используют digest вида `image@sha256:...`.

## Готовый образ и свой образ

Redis и PostgreSQL можно взять из Docker Hub:

```bash
docker pull redis:7-alpine
docker pull postgres:17-alpine
```

В Python-образ нужно добавить наш код и зависимости. Это описывается в `Dockerfile`.

## Dockerfile для backend

Готовые файлы находятся в [примере](<примеры/docker-compose/>). Dockerfile лежит рядом с `requirements.txt` и папкой `app`.

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN useradd --create-home appuser
COPY app ./app
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:api", "--host", "0.0.0.0", "--port", "8000"]
```

| Инструкция | Что делает в этом примере |
| --- | --- |
| `FROM` | Берёт готовый Python-образ за основу |
| `ENV` | Отключает `.pyc` и буферизацию вывода, чтобы логи появлялись сразу |
| `WORKDIR /app` | Выбирает рабочую папку внутри контейнера |
| `COPY` | Копирует файлы в образ |
| `RUN pip install ...` | Устанавливает библиотеки при сборке |
| `RUN useradd ...` | Создаёт обычного пользователя Linux |
| `USER appuser` | Запускает приложение от этого пользователя |
| `EXPOSE` | Указывает, какой порт использует приложение |
| `CMD` | Задаёт команду запуска контейнера по умолчанию |

`RUN` выполняется при сборке образа. `CMD` задаёт действие при старте контейнера.

## Зачем копировать requirements отдельно

Docker повторно использует подходящие результаты предыдущих шагов сборки — это кеш.

Если поменялся только `app/main.py`, слой установки библиотек можно взять из кеша: `requirements.txt` остался прежним. Если сразу скопировать весь проект перед `pip install`, любое изменение кода будет заново запускать шаг установки.

`--no-cache-dir` относится к кешу загрузок **pip**. Кеш слоёв Docker продолжает работать.

В учебном `requirements.txt` указаны диапазоны версий. Для повторяемой сборки проекта фиксируют версии зависимостей в lock-файле или точном списке.

## `.dockerignore`

Этот файл исключает ненужные файлы из контекста сборки — набора файлов, доступных Docker при сборке.

```gitignore
.git
.env
.env.*
.venv
__pycache__
**/__pycache__
*.pyc
**/*.pyc
```

Локальное виртуальное окружение и пароли не нужны в образе. `.gitignore` управляет Git, а `.dockerignore` — файлами сборки Docker.

## Собрать и посмотреть образ

Из папки `примеры/docker-compose`:

```bash
docker build -t backend-study:local .
docker images
docker image inspect backend-study:local
```

`-t` задаёт имя и тег. Точка в конце означает текущую папку как контекст сборки.

Можно проверить Python внутри образа:

```bash
docker run --rm backend-study:local python --version
```

Команда `python --version` заменит стандартный `CMD`. `--rm` удалит этот временный контейнер после завершения. Полный backend с Redis и PostgreSQL запускается в [следующем конспекте](<Docker Compose — запуск backend и сервисов.md>).

## Один образ, разные программы

В нашем образе установлены FastAPI, Celery и Flower. Из него создаются три вида контейнеров:

| Сервис | Основная команда |
| --- | --- |
| `backend` | `uvicorn app.main:api ...` |
| `celery` | `celery -A app.celery_conn:app worker ...` |
| `flower` | `celery -A app.celery_conn:app flower ...` |

В Compose поле `command` заменяет `CMD` образа. Каждый контейнер при этом работает отдельно.

## Как обновить код

Код в этом образе копируется при сборке. После изменения исходников:

```bash
docker compose up -d --build
```

Обычный `docker compose restart` перезапускает старые контейнеры с уже имеющимися файлами. Для включения нового кода нужна пересборка и создание контейнеров из обновлённого образа.

## Отправить образ в Docker Hub

Если нужно передать готовый образ другому человеку, его можно опубликовать в registry. Пример команд, где `YOUR_NAME` заменяется на имя аккаунта Docker Hub:

```bash
docker login
docker tag backend-study:local YOUR_NAME/backend-study:1.0
docker push YOUR_NAME/backend-study:1.0
```

`tag` добавляет образу имя, а `push` загружает его в registry. Исходный код и Dockerfile обычно хранят в GitHub, собранный образ — в registry.

## Документация

- [Образы Docker](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-an-image/)
- [Инструкции Dockerfile](https://docs.docker.com/reference/dockerfile/)
- [Контекст сборки и .dockerignore](https://docs.docker.com/build/concepts/context/)
- [Кеш сборки](https://docs.docker.com/build/cache/)
