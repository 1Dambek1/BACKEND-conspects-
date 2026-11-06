# Pydantic Settings — настройки приложения

API заметок нужен адрес базы. На компьютере это может быть SQLite, а в Docker — PostgreSQL. С Pydantic Settings код в обоих случаях одинаковый: меняется только настройка `DATABASE_URL`.

В Pydantic 2 за это отвечает отдельный пакет: `python -m pip install "pydantic-settings>=2,<3"`. В команде установки у имени дефис, а в Python-импорте — подчёркивание.

## Два файла: что нужно и откуда взять

В корне учебного проекта создай `config.py`:

```python
from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: SecretStr
    app_name: str = "Мои заметки"
    debug: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

Рядом положи файл `.env`:

```dotenv
DATABASE_URL=sqlite:///notes.db
DEBUG=true
```

Теперь в Python:

```python
from config import get_settings

settings = get_settings()
print(settings.app_name)  # Мои заметки
print(settings.debug)     # True — bool, хотя в файле было слово true
```

`database_url` обязателен. Если настройка отсутствует и в окружении, и в файле, ошибка появится при создании `Settings()`. Адрес может содержать пароль: `SecretStr` маскирует его при обычном выводе. Настоящее значение для подключения берут через `settings.database_url.get_secret_value()`.

## Какое значение победит

Для источников в этом примере порядок такой: **аргумент `Settings(...)` → переменная окружения → `.env` → значение в классе**. Например, если в `.env` стоит `DEBUG=true`, а Docker передал `DEBUG=false`, приложение получит `False`.

Файл `.env` здесь ищется в папке, **из которой запущена команда**. Запускай приложение и Alembic из корня проекта. В Git обычно кладут `.env.example` с учебными значениями, а настоящий `.env` добавляют в `.gitignore`.

## Подключаем к FastAPI и PostgreSQL

В приложении можно использовать настройки сразу при старте. В примере из [конспекта про Pydantic](<Pydantic — проверка данных.md>) замени `app = FastAPI()` на:

```python
from config import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name, debug=settings.debug)
```

`@lru_cache` сохраняет настройки после первого вызова в процессе. Повторный запрос не перечитывает файл. После изменения настроек перезапусти приложение.

Для PostgreSQL с драйвером psycopg в `.env` меняется одна строка. Пример для приложения в сети Compose, где сервис базы называется `postgres`:

```dotenv
DATABASE_URL=postgresql+psycopg://app:demo@postgres:5432/backend
```

Подставь данные своей учебной базы. Если запускаешь Python на компьютере, адресом будет `localhost` и опубликованный порт. Этот же `get_settings()` использует [Alembic](<Alembic — миграции базы данных.md>), чтобы менять именно ту базу, к которой подключено приложение.

Подробнее: [как Pydantic Settings читает настройки](https://docs.pydantic.dev/latest/concepts/pydantic_settings/).
