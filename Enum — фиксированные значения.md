# Enum — фиксированные значения

У заказа пиццы есть статус: новый, готовится, доставлен или отменён. Если писать строки вручную в разных местах, легко получить опечатку: `"cokking"` вместо `"cooking"`.

**Enum** — класс с заранее заданными вариантами. В коде можно обращаться к `OrderStatus.COOKING`, а клиенту отправлять понятную строку `"cooking"`. Модуль `enum` уже входит в Python, отдельно устанавливать его не нужно.

## Объявляем статусы

```python
from enum import Enum


class OrderStatus(str, Enum):
    NEW = "new"
    COOKING = "cooking"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
```

`Enum` задаёт перечисление, а `str` делает его элементы также строками — это удобно для JSON и API. Класс не даёт создать новый вариант простым вызовом `OrderStatus("что угодно")`: значение должно быть объявлено заранее.

## Имя, значение и сравнение

```python
status = OrderStatus.COOKING

print(status.name)   # COOKING — имя в Python
print(status.value)  # cooking — значение для API

if status == OrderStatus.COOKING:
    print("Пицца готовится")

print(OrderStatus("cooking") == OrderStatus.COOKING)  # True
print(OrderStatus["COOKING"] == OrderStatus.COOKING)  # True
```

Скобки `(...)` ищут по **значению**, квадратные скобки `[...]` — по **имени**. `OrderStatus("COOKING")` вызовет `ValueError`, потому что значение у нас написано маленькими буквами.

Получить список всех разрешённых строк:

```python
values = [status.value for status in OrderStatus]
print(values)  # ['new', 'cooking', 'delivered', 'cancelled']
```

В Python 3.11+ вместо `class OrderStatus(str, Enum)` можно использовать `class OrderStatus(StrEnum)` с импортом `from enum import StrEnum`. Для числовых вариантов есть `IntEnum`. В этом конспекте используем строковые статусы. [Перечисления в Python](https://docs.python.org/3/library/enum.html).

## Pydantic: принять только объявленный статус

Добавь к классу `OrderStatus` схему на Pydantic 2:

```python
from pydantic import BaseModel


class StatusInput(BaseModel):
    status: OrderStatus = OrderStatus.NEW


payload = StatusInput(status="cooking")
print(payload.status == OrderStatus.COOKING)  # True
print(payload.model_dump(mode="json"))       # {'status': 'cooking'}
```

Строка `"cooking"` после проверки стала элементом `OrderStatus.COOKING`. Если статус не передан, используется `NEW`. Если передать `"burnt"`, Pydantic выдаст `ValidationError`.

Обычный `model_dump()` сохраняет элемент Enum в словаре в режиме Python. `model_dump(mode="json")` возвращает словарь со строкой, а `model_dump_json()` — готовую строку JSON. [Enum в Pydantic](https://docs.pydantic.dev/latest/api/standard_library_types/#enums).

## FastAPI: статус в JSON и в адресе

В `main.py` размести определения `OrderStatus` и `StatusInput` из примеров выше, затем этот код:

```python
from fastapi import FastAPI

app = FastAPI()


@app.post("/orders/status-preview", response_model=StatusInput)
def preview_status(payload: StatusInput):
    return payload


@app.get("/orders/statuses/{status}")
def explain_status(status: OrderStatus):
    messages = {
        OrderStatus.NEW: "Заказ принят",
        OrderStatus.COOKING: "Пицца готовится",
        OrderStatus.DELIVERED: "Заказ доставлен",
        OrderStatus.CANCELLED: "Заказ отменён",
    }
    return {"status": status, "message": messages[status]}
```

Установи `python -m pip install fastapi uvicorn` и запусти `uvicorn main:app --reload`. Открой [Swagger](http://127.0.0.1:8000/docs): у параметра статуса появятся разрешённые варианты.

| Запрос | Результат |
| --- | --- |
| `POST /orders/status-preview` с `{"status":"cooking"}` | `200`, в ответе `{"status":"cooking"}` |
| Тот же запрос с `{}` | `200`, статус по умолчанию — `"new"` |
| Тот же запрос с `{"status":"burnt"}` | `422`, неизвестный статус |
| `GET /orders/statuses/delivered` | `200`, сообщение «Заказ доставлен» |
| `GET /orders/statuses/unknown` | `422`, обработчик не запустится |

Это предпросмотр: в базу он ничего не записывает. Enum проверяет допустимое значение, а правила переходов — отдельная логика. Например, запретить переход из `DELIVERED` в `NEW` и проверить права оператора нужно в коде изменения заказа. [Enum в параметрах FastAPI](https://fastapi.tiangolo.com/tutorial/path-params/#predefined-values).

## Как хранить в SQLAlchemy

В Python есть `enum.Enum`, а в SQLAlchemy — свой тип колонки `Enum`. Чтобы не путаться, импортируем тип колонки под именем `SAEnum`:

```python
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[OrderStatus] = mapped_column(
        SAEnum(
            OrderStatus,
            name="order_status",
            values_callable=lambda statuses: [item.value for item in statuses],
            validate_strings=True,
        ),
        default=OrderStatus.NEW,
    )
```

Здесь используется тот же класс `OrderStatus`. `values_callable` говорит сохранять значения `"new"`, `"cooking"` и другие. **Без этой настройки SQLAlchemy по умолчанию сохраняет имена**: `"NEW"`, `"COOKING"`. `validate_strings=True` дополнительно проверяет строки, переданные через SQLAlchemy. `default` подставляет `NEW` при вставке через SQLAlchemy, если статус не указан; это не SQL-настройка `DEFAULT` на стороне базы. [Тип Enum в SQLAlchemy](https://docs.sqlalchemy.org/en/20/core/type_basics.html#sqlalchemy.types.Enum).

При чтении через ORM снова получишь элемент Enum и сможешь сравнить `order.status == OrderStatus.NEW`. В PostgreSQL такая колонка обычно использует отдельный тип базы `order_status`. В SQLite вместо него будет строковая колонка: сама по себе она не запретит произвольную строку, записанную напрямую через SQL. Для ограничения в базе при таком хранении нужен `CHECK` (у `SAEnum` есть параметр `create_constraint=True`).

Если таблица уже существует, её меняют через [Alembic](<Alembic — миграции базы данных.md>). Добавление нового варианта в Python не обновляет существующий ENUM PostgreSQL: нужна миграция типа базы, которую следует проверить отдельно — автогенерация не обязана подготовить её за тебя.
