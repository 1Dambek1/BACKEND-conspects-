# Docker — базовые команды

На Windows сначала запусти Docker Desktop в режиме Linux-контейнеров. Команды ниже можно вводить в PowerShell. Каждый блок — отдельный пример.

## Проверить Docker

```bash
docker version
docker compose version
```

`docker version` показывает клиент и сервер Docker. Ошибка подключения к серверу часто означает, что Docker Engine ещё не запущен.

## Скачать образ

```bash
docker pull redis:7-alpine
docker images
```

`pull` скачивает образ. `images` показывает локальные образы. `7-alpine` — тег выбранного варианта Redis.

## Создать и запустить контейнер

```bash
docker run -d --name study-redis -p 127.0.0.1:6379:6379 redis:7-alpine
```

| Часть команды | Значение |
| --- | --- |
| `run` | Создать новый контейнер и запустить |
| `-d` | Работать в фоне |
| `--name study-redis` | Дать контейнеру имя |
| `-p 127.0.0.1:6379:6379` | Открыть порт Redis только на этом компьютере |
| `redis:7-alpine` | Использовать этот образ |

Если образа нет локально, Docker попробует его скачать.

## Посмотреть контейнеры и логи

```bash
docker ps
docker ps -a
docker logs --tail 50 study-redis
docker logs -f study-redis
```

- `ps` — работающие контейнеры.
- `ps -a` — все контейнеры, включая остановленные.
- `logs` — сообщения программы.
- `logs -f` — следить за новыми сообщениями. `Ctrl+C` прекращает просмотр, контейнер продолжает работать.

## Выполнить команду внутри контейнера

```bash
docker exec study-redis redis-cli ping
```

Ответ `PONG` означает, что Redis ответил.

Открыть командную строку внутри:

```bash
docker exec -it study-redis sh
```

`-it` нужен для интерактивной работы. Выйти можно командой `exit`. У маленьких образов часто есть `sh`, а `bash` может отсутствовать.

## Остановить и снова запустить

```bash
docker stop study-redis
docker start study-redis
docker restart study-redis
```

`start` запускает уже созданный контейнер. Повторный `run` создаёт новый, поэтому занятое имя вызовет ошибку.

## Сохранить данные Redis

Следующий пример создаёт другой контейнер с отдельным именем и volume:

```bash
docker volume create study-redis-data
docker run -d --name study-redis-store -v study-redis-data:/data redis:7-alpine redis-server --appendonly yes
```

`-v study-redis-data:/data` подключает volume к папке `/data`. Redis записывает изменения в AOF-файл благодаря `--appendonly yes`.

## Удалить ненужное

Удаление контейнера убирает его собственные файлы. Делай это, когда контейнер больше не нужен:

```bash
docker stop study-redis
docker rm study-redis
```

Образ и именованные volumes при этом сохраняются. Их удаление — отдельные команды:

```bash
docker image rm redis:7-alpine
docker volume rm study-redis-data
```

Команды показаны как примеры: Docker может отказать в удалении используемого ресурса. Удаление volume стирает хранящиеся в нём данные.

## Ещё полезные команды

| Команда | Что посмотреть |
| --- | --- |
| `docker inspect study-redis` | Подробные настройки контейнера, если он существует |
| `docker stats` | Расход CPU и памяти работающими контейнерами |
| `docker system df` | Сколько места занимают образы, контейнеры и volumes |
| `docker network ls` | Сети Docker |
| `docker volume ls` | Volumes |
| `docker build -t my-backend:1.0 .` | Собрать образ по Dockerfile в текущей папке |

## Когда сервисов несколько

Из папки с `compose.yaml`:

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f backend
docker compose exec backend sh
docker compose stop
docker compose start
docker compose down
```

`up` создаёт или обновляет сервисы, `stop` останавливает, `start` запускает существующие, а `down` убирает контейнеры проекта и его обычную сеть. Именованные volumes после обычного `down` сохраняются.

Полный пример: [Compose для backend, Redis, Celery, Flower и PostgreSQL](<Docker Compose — запуск backend и сервисов.md>).

## Документация

- [docker run](https://docs.docker.com/reference/cli/docker/container/run/)
- [docker exec](https://docs.docker.com/reference/cli/docker/container/exec/)
- [docker compose up](https://docs.docker.com/reference/cli/docker/compose/up/)
- [docker compose down](https://docs.docker.com/reference/cli/docker/compose/down/)
