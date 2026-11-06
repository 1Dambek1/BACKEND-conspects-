# Alembic — миграции базы данных

В таблице `notes` уже есть заметки. Теперь у заметки появился тег. Если просто дописать `tag` в Python-классе, в существующей таблице столбец не появится. **Миграция** — файл с шагом изменения базы. Alembic запускает такие файлы по порядку и запоминает применённую версию в таблице `alembic_version`.

Ниже два изменения: сначала создадим `notes`, потом добавим к ней тег. Начни с **отдельной пустой учебной базы**. Самый короткий путь — SQLite: сервер для неё не нужен. Для PostgreSQL шаги те же, но сама база должна уже существовать и быть доступна.

## 1. Где таблица и как к ней подключиться

Из корня проекта выполни:

```bash
python -m pip install alembic "SQLAlchemy>=2,<3" "pydantic-settings>=2,<3"
alembic init migrations
```

Первая команда ставит библиотеки, вторая один раз создаёт `alembic.ini`, `migrations/env.py` и папку `migrations/versions/` для истории изменений.

Возьми `config.py` из [конспекта про настройки](<Pydantic Settings — настройки приложения.md>) и положи рядом `.env` со строкой `DATABASE_URL=sqlite:///notes.db`. Для PostgreSQL используй адрес своей базы и поставь драйвер: `python -m pip install "psycopg[binary]"`.

Рядом создай `models.py`. Это SQLAlchemy-модель: она описывает столбцы таблицы.

```python
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    priority: Mapped[int]
```

В созданном `migrations/env.py` **замени строку** `target_metadata = None` следующим блоком. Переменная `config` уже объявлена выше в шаблоне:

```python
from config import get_settings
from models import Base

target_metadata = Base.metadata
url = get_settings().database_url.get_secret_value()
config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
```

Теперь Alembic знает **куда подключиться** (URL) и **с чем сравнивать базу** (`Base.metadata`). Замена `%` нужна для формата настроек Alembic, например если в URL есть `%40`. При нескольких файлах моделей импортируй их до сравнения, чтобы все таблицы попали в `metadata`.

## 2. Создаём первую версию

```bash
alembic revision --autogenerate -m "create notes"
```

Открой новый файл в `migrations/versions/`. В `upgrade()` ожидается `op.create_table("notes", ...)`, а в `downgrade()` — обратный шаг. Пока создан только файл. Чтобы таблица появилась в базе:

```bash
alembic upgrade head
alembic current
```

`head` — последняя версия в этой цепочке. `current` покажет, до какой версии обновлена выбранная база. В этом примере создание таблиц поручено миграциям: если заранее вызвать `create_all()`, Alembic уже увидит существующую таблицу и не предложит её создать.

## 3. Добавляем тег, сохраняя старые заметки

Внутри класса `Note` добавь поле:

```python
    tag: Mapped[str | None] = mapped_column(String(50))
```

Создай вторую миграцию:

```bash
alembic revision --autogenerate -m "add tag to notes"
```

Проверь, что новый файл меняет только нужный столбец. Внутри должны быть примерно такие операции:

```python
def upgrade():
    op.add_column("notes", sa.Column("tag", sa.String(50), nullable=True))


def downgrade():
    op.drop_column("notes", "tag")
```

Применяй через `alembic upgrade head`. У старых заметок `tag` будет `NULL`, остальные поля сохранятся. Если поле обязано быть заполнено, сначала добавь его как необязательное, заполни существующие строки, затем отдельным шагом установи `NOT NULL`.

## Посмотреть историю и откатить шаг

| Команда | Что произойдёт в примере |
| --- | --- |
| `alembic history` | Покажет обе миграции и порядок между ними |
| `alembic current` | Покажет версию именно этой базы |
| `alembic downgrade -1` | После второй миграции уберёт столбец `tag` **вместе с записанными тегами** |
| `alembic upgrade head` | Создаст столбец снова; удалённые значения не восстановятся |

`--autogenerate` предлагает изменения для проверки. Например, переименование столбца может выглядеть как удаление старого и добавление нового — это потеряет данные, если применить как есть. Проверенный файл миграции коммитят в Git вместе с изменением модели, чтобы остальные применили тот же шаг.

Подробнее: [команды Alembic](https://alembic.sqlalchemy.org/en/latest/tutorial.html) и [что умеет автогенерация](https://alembic.sqlalchemy.org/en/latest/autogenerate.html).
