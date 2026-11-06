# Pydantic — проверка данных

Допустим, в API заметок пришёл запрос `{"title": "Купить хлеб", "priority": "2"}`. Обработчику нужны непустой заголовок и число от 1 до 3. В Pydantic эти правила можно описать один раз в классе, а потом получать уже проверенные данные.

Пример для Python 3.10+ и Pydantic 2. Установка: `python -m pip install "pydantic>=2,<3"`.

## Описываем заметку

Создай файл `schemas.py`:

```python
from pydantic import BaseModel, ConfigDict, Field


class NoteCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    title: str = Field(min_length=1, max_length=100)
    priority: int = Field(default=2, ge=1, le=3)
    tag: str | None = Field(default=None, max_length=50)
```

- `title` обязателен. Пробелы по краям убираются, поэтому заголовок из одних пробелов не пройдёт проверку.
- `priority` можно пропустить: получится `2`. Границы `ge=1` и `le=3` включают и 1, и 3.
- `tag` — строка до 50 символов. Его можно пропустить или передать `null`. Запись `str | None` **без значения по умолчанию** разрешила бы `null`, но поле всё равно пришлось бы передать.
- `extra="forbid"` помогает заметить опечатку: если написать `priorty`, Pydantic сообщит о незнакомом поле.

## Пробуем на словаре

```python
from schemas import NoteCreate

note = NoteCreate.model_validate({"title": "  Купить хлеб  ", "priority": "2"})
print(note.priority)      # 2 (int)
print(note.model_dump())  # {'title': 'Купить хлеб', 'priority': 2, 'tag': None}
```

`model_validate()` проверяет вход. В обычном режиме Pydantic умеет преобразовать строку `"2"` в число. `model_dump()` возвращает словарь, а `model_dump_json()` — строку JSON.

Если данные не подходят, в Python возникает `ValidationError`:

```python
from pydantic import ValidationError
from schemas import NoteCreate

try:
    NoteCreate(title="Купить хлеб", priority=9)
except ValidationError as exc:
    print(exc.errors()[0]["loc"])  # ('priority',)
```

## Что меняется в FastAPI

В `main.py` добавим предпросмотр заметки. Так можно попробовать проверку до подключения базы:

```python
from fastapi import FastAPI
from schemas import NoteCreate

app = FastAPI()


@app.post("/notes/preview", response_model=NoteCreate)
def preview_note(note: NoteCreate):
    return note
```

Установи `python -m pip install fastapi uvicorn`, запусти `uvicorn main:app --reload` и открой [страницу запросов](http://127.0.0.1:8000/docs). Отправь `{"title":"Купить хлеб"}`: в ответе будут `priority: 2` и `tag: null`. Поменяй приоритет на `9` — FastAPI вернёт HTTP `422` с указанием поля, а обработчик не запустится.

Добавление `tag` в эту схему разрешает принимать тег в API. Чтобы сохранять его в уже существующей таблице, нужен ещё один шаг: [миграция Alembic](<Alembic — миграции базы данных.md>).

Подробнее: [модели Pydantic](https://docs.pydantic.dev/latest/concepts/models/) и [правила для полей](https://docs.pydantic.dev/latest/concepts/fields/).
