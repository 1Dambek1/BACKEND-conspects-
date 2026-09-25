# SQLAlchemy — основы

SQLAlchemy — библиотека Python для работы с базой данных. Она позволяет описывать таблицы обычными классами Python и работать с ними через объекты.

В этом примере используется SQLite. Это простая база данных: она хранится в одном файле и хорошо подходит для обучения и небольших проектов.

Установка:

```bash
pip install sqlalchemy
```

## Полный пример

```python
from sqlalchemy import create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


engine = create_engine("sqlite:///test.db", echo=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    username: Mapped[str] = mapped_column(unique=True)
    age: Mapped[int]
    height: Mapped[int] = mapped_column(default=165)
    city: Mapped[str]
    salary: Mapped[int]

    def __repr__(self):
        return (
            f"User(id={self.id}, name={self.name}, "
            f"username={self.username}, age={self.age}, "
            f"height={self.height}, city={self.city}, "
            f"salary={self.salary})"
        )


Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()
```

Важно: в классе нужно именно `__tablename__` — с двумя подчёркиваниями с обеих сторон.

## Разбор кода

### `engine` — подключение к базе

```python
engine = create_engine("sqlite:///test.db", echo=False)
```

`engine` знает, где находится база и как к ней подключиться.

- `sqlite:///test.db` — создать или открыть файл `test.db` рядом с программой.
- `echo=False` — не выводить SQL-запросы в консоль. Для обучения можно поставить `echo=True` и смотреть, какой SQL отправляет SQLAlchemy.

### `Base` — основа для моделей

```python
class Base(DeclarativeBase):
    pass
```

От `Base` наследуются классы-таблицы. SQLAlchemy собирает информацию о таких классах и потом создаёт по ней таблицы.

### `User` — таблица `users`

```python
class User(Base):
    __tablename__ = "users"
```

Класс `User` — это таблица `users`. Один объект `User` — одна строка этой таблицы.

| Python-код | Что будет в базе |
| --- | --- |
| `id: Mapped[int]` | колонка `id` с числом |
| `mapped_column(primary_key=True)` | уникальный ID пользователя |
| `username: Mapped[str] = mapped_column(unique=True)` | уникальный `username` |
| `height: Mapped[int] = mapped_column(default=165)` | рост, по умолчанию `165` |
| `name: Mapped[str]` | обязательная текстовая колонка |

`Mapped[...]` показывает тип значения. `mapped_column(...)` добавляет настройки колонки.

### `__repr__` — удобный вывод объекта

Метод `__repr__` влияет только на то, как объект выглядит при `print(user)` или в консоли:

```python
print(user)
# User(id=1, name=Denis, username=dambek, ...)
```

На данные в базе он не влияет.

### Создание таблиц

```python
Base.metadata.create_all(engine)
```

SQLAlchemy создаст все таблицы, которых ещё нет. Если `users` уже существует, команда не удалит её и не создаст заново.

### `Session` — работа с данными

```python
Session = sessionmaker(bind=engine)
session = Session()
```

Сессия — это объект, через который добавляют, ищут, меняют и удаляют данные. После изменений нужен `commit()`, чтобы сохранить их в базе.

## Добавление пользователей

```python
users = [
    User(
        name="Denis",
        username="dambek",
        age=17,
        height=186,
        city="Irkutsk",
        salary=80000,
    ),
    User(
        name="Andrey",
        username="andrey_dev",
        age=23,
        height=180,
        city="Moscow",
        salary=150000,
    ),
]

session.add_all(users)
session.commit()
```

`User(...)` пока создаёт только Python-объект. `session.add_all(users)` готовит объекты к сохранению. `session.commit()` действительно записывает их в файл базы.

Если забыть `commit()`, после завершения программы данные не сохранятся.

Для одного пользователя можно использовать `add`:

```python
user = User(name="Maria", username="maria_ml", age=25, city="Moscow", salary=210000)
session.add(user)
session.commit()
```

Здесь `height` не передан, поэтому будет использовано значение по умолчанию — `165`.

## Получение данных — `select`

```python
statement = select(User)
users = session.scalars(statement).all()

for user in users:
    print(user)
```

Это примерно соответствует SQL:

```sql
SELECT * FROM users;
```

### Поиск с условием

```python
# пользователи из Иркутска
statement = select(User).where(User.city == "Irkutsk")
users = session.scalars(statement).all()

# один пользователь по username
statement = select(User).where(User.username == "dambek")
user = session.scalar(statement)
```

Полезные условия:

```python
select(User).where(User.age >= 18)
select(User).where(User.city.in_(["Irkutsk", "Kazan"]))
select(User).where(User.salary > 150000, User.age >= 25)
```

## Изменение пользователя

```python
user = session.scalar(select(User).where(User.username == "dambek"))

if user is not None:
    user.salary = 100000
    session.commit()
```

После поиска SQLAlchemy следит за объектом. Достаточно поменять его поле и вызвать `commit()`.

## Удаление пользователя

```python
user = session.scalar(select(User).where(User.username == "dambek"))

if user is not None:
    session.delete(user)
    session.commit()
```

## Ошибки и `rollback`

`username` уникальный. Если добавить второго пользователя с таким же `username`, база выдаст ошибку. После ошибки нужно отменить незавершённые изменения:

```python
from sqlalchemy.exc import IntegrityError

try:
    session.add(User(name="Other", username="dambek", age=20, city="Kazan", salary=90000))
    session.commit()
except IntegrityError:
    session.rollback()
    print("Такой username уже есть")
finally:
    session.close()
```

- `commit()` — сохранить изменения.
- `rollback()` — отменить незавершённые изменения после ошибки.
- `close()` — закрыть сессию, когда работа закончена.

## `text` — SQL руками

Иногда нужен обычный SQL-запрос. Тогда используют `text`:

```python
from sqlalchemy import text

result = session.execute(
    text("SELECT name, salary FROM users WHERE salary >= :min_salary"),
    {"min_salary": 150000},
)

for row in result:
    print(row.name, row.salary)
```

`:min_salary` — безопасный параметр. Не вставляй значения в SQL через f-строку: это может привести к SQL-инъекции.

## Связь с SQL

| SQL | SQLAlchemy |
| --- | --- |
| `INSERT INTO users ...` | `session.add(user)` + `session.commit()` |
| `SELECT * FROM users` | `session.scalars(select(User)).all()` |
| `SELECT ... WHERE city = ...` | `select(User).where(User.city == "Irkutsk")` |
| `UPDATE users ...` | изменить поле объекта + `session.commit()` |
| `DELETE FROM users ...` | `session.delete(user)` + `session.commit()` |

## Коротко

`engine` подключает базу, `Base` нужен для моделей, `User` описывает таблицу, а `session` работает с данными. Создал объект → добавил в сессию → вызвал `commit()` — данные появились в базе.
