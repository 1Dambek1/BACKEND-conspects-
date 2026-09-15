# FastAPI — основы

FastAPI — библиотека Python для создания API. Она сама проверяет входные данные и создаёт страницу с документацией: `/docs`.

Установка:

```bash
pip install fastapi "uvicorn[standard]"
uvicorn main:app --reload
```

`main` — файл `main.py`, `app` — приложение внутри него. `--reload` перезапускает сервер после сохранения кода.

## Минимальное приложение

```python
from fastapi import FastAPI

app = FastAPI(title="Notes API")


@app.get("/")
def read_root():
    return {"message": "API работает"}
```

Декоратор `@app.get("/")` связывает HTTP-метод `GET` и путь `/` с функцией `read_root`. Значение, возвращённое функцией, FastAPI преобразует в JSON.

## HTTP-методы: GET, POST, PUT

Пусть есть временное хранилище заметок. В реальном проекте вместо словаря будет база данных.

```python
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

app = FastAPI()
notes: dict[int, dict] = {}


class NoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    text: str = Field(min_length=1)


class Note(BaseModel):
    id: int
    title: str
    text: str
```

### GET — получить данные

`GET` не должен менять состояние сервера. Обычно применяется для получения списка или одного ресурса.

```python
@app.get("/notes", response_model=list[Note])
def get_notes():
    return list(notes.values())


@app.get("/notes/{note_id}", response_model=Note)
def get_note(note_id: int):
    note = notes.get(note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Заметка не найдена")
    return note
```

`note_id: int` — число в адресе запроса. Если передать не число, FastAPI вернёт `422`: данные не прошли проверку.

### POST — создать ресурс

`POST` обычно создаёт новый ресурс. Тело запроса описывается Pydantic-моделью.

```python
@app.post("/notes", response_model=Note, status_code=status.HTTP_201_CREATED)
def create_note(payload: NoteCreate):
    note_id = len(notes) + 1
    note = {"id": note_id, **payload.model_dump()}
    notes[note_id] = note
    return note
```

Пример запроса:

```http
POST /notes
Content-Type: application/json

{
  "title": "HTTP",
  "text": "Статус-коды показывают результат запроса"
}
```

Успешный ответ: `201 Created` и созданный объект в JSON.

### PUT — полностью заменить ресурс

`PUT` полностью заменяет ресурс. Если отправить один и тот же запрос несколько раз, результат будет тем же.

```python
@app.put("/notes/{note_id}", response_model=Note)
def replace_note(note_id: int, payload: NoteCreate):
    if note_id not in notes:
        raise HTTPException(status_code=404, detail="Заметка не найдена")

    note = {"id": note_id, **payload.model_dump()}
    notes[note_id] = note
    return note
```

Для частичного обновления обычно используют `PATCH`, а не `PUT`.

| Метод | Назначение | Обычно успешный статус | Идемпотентен |
| --- | --- | --- | --- |
| `GET` | Получить данные | `200 OK` | Да |
| `POST` | Создать ресурс | `201 Created` | Нет |
| `PUT` | Полностью заменить ресурс | `200 OK` | Да |
| `PATCH` | Изменить часть ресурса | `200 OK` | Зависит от кода |
| `DELETE` | Удалить ресурс | `204 No Content` | Да |

## Pydantic: схемы и валидация

Pydantic-модель — это описание данных. FastAPI берёт JSON от клиента, проверяет его и передаёт в функцию готовый объект.

```python
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    age: int = Field(ge=18, le=120)
    email: EmailStr
    is_active: bool = True
```

| Элемент | Значение |
| --- | --- |
| `str`, `int`, `bool` | ожидаемые типы полей |
| `Field(...)` | метаданные и ограничения: `min_length`, `ge`, `le` и другие |
| `EmailStr` | проверка формата email; требуется пакет `email-validator` |
| `payload.model_dump()` | превращает модель в словарь (Pydantic v2) |
| `response_model=...` | проверяет и фильтрует JSON ответа |

Важное правило: входные и выходные схемы лучше разделять. Например, `UserCreate` содержит пароль для создания пользователя, но `UserOut` никогда не должен возвращать пароль клиенту.

```python
class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
```

## APIRouter: разбиение API по модулям

Когда адресов API много, их раскладывают по файлам. `APIRouter` — это группа связанных адресов, которую подключают к главному приложению.

Структура проекта:

```text
app/
├── main.py
└── routers/
    └── notes.py
```

`app/routers/notes.py`:

```python
from fastapi import APIRouter

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("/")
def get_notes():
    return []


@router.get("/{note_id}")
def get_note(note_id: int):
    return {"id": note_id}
```

`app/main.py`:

```python
from fastapi import FastAPI
from app.routers import notes

app = FastAPI()
app.include_router(notes.router)
```

`prefix="/notes"` добавится ко всем путям роутера, а `tags=["notes"]` объединит их в один раздел документации `/docs`.

## Depends: зависимости

`Depends` запускает общий код до обработчика. Так удобно получать подключение к базе, проверять пользователя или его права.

```python
from fastapi import Depends, FastAPI, Header, HTTPException, status

app = FastAPI()


def require_api_key(x_api_key: str = Header()):
    if x_api_key != "secret-key":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный API-ключ",
        )
    return x_api_key


@app.get("/private")
def read_private(api_key: str = Depends(require_api_key)):
    return {"message": "Доступ разрешён"}
```

Перед выполнением `read_private` FastAPI вызовет `require_api_key`. Если зависимость выбросит исключение, обработчик не запустится. Зависимость может возвращать значение, которое попадёт в параметр `api_key`.

Типичная зависимость для БД использует `yield`, чтобы гарантированно закрыть сессию:

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/")
def get_notes(db: Session = Depends(get_db)):
    return db.query(NoteModel).all()
```

Код после `yield` выполнится после обработки запроса — даже если возникла ошибка.

## HTTP-статусы: 100, 200, 300, 400, 500

HTTP-код — число в ответе сервера. Первая цифра показывает тип ответа. `1xx` — не ошибка, а служебная информация; `4xx` — ошибся клиент; `5xx` — проблема на сервере.

| Класс | Смысл | Частые коды |
| --- | --- | --- |
| `1xx` | Информация: обработка продолжается | `100 Continue`, `101 Switching Protocols` |
| `2xx` | Успех | `200 OK`, `201 Created`, `204 No Content` |
| `3xx` | Перенаправление | `301 Moved Permanently`, `302 Found`, `307 Temporary Redirect`, `308 Permanent Redirect` |
| `4xx` | Проблема в запросе клиента | `400`, `401`, `403`, `404`, `409`, `422` |
| `5xx` | Ошибка на сервере | `500`, `502`, `503`, `504` |

### Часто используемые коды

- `200 OK` — запрос успешно обработан, ответ содержит данные.
- `201 Created` — ресурс создан; типичный ответ на `POST`.
- `204 No Content` — успех без тела ответа, например после удаления.
- `301` / `308` — постоянное перенаправление; `302` / `307` — временное. `307` и `308` сохраняют исходный HTTP-метод.
- `400 Bad Request` — сервер не может обработать некорректный запрос.
- `401 Unauthorized` — аутентификация отсутствует или неуспешна. Часто требуется заголовок `WWW-Authenticate`.
- `403 Forbidden` — пользователь известен, но прав недостаточно.
- `404 Not Found` — ресурс или путь не найден.
- `409 Conflict` — конфликт состояния, например email уже занят.
- `422 Unprocessable Content` — структура запроса понятна, но данные не проходят валидацию. FastAPI возвращает его автоматически при ошибке Pydantic.
- `500 Internal Server Error` — необработанная ошибка приложения. Не следует возвращать клиенту технические детали или traceback.
- `502 Bad Gateway`, `503 Service Unavailable`, `504 Gateway Timeout` — проблемы с прокси, зависимым сервисом или его доступностью.

## Обработка ошибок в FastAPI

Для ожидаемых ошибок используют `HTTPException`:

```python
from fastapi import HTTPException, status


def get_user_or_404(user_id: int):
    user = users.get(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )
    return user
```

Для конфликта при создании:

```python
if email in registered_emails:
    raise HTTPException(status_code=409, detail="Email уже используется")
```

Практика для API:

1. Выбирай код по смыслу, а не всегда `200`.
2. Возвращай клиенту понятный `detail`, но не секреты, SQL и traceback.
3. Не превращай ошибки клиента в `500`: заранее проверяй входные данные и бизнес-правила.
4. Логируй необработанные ошибки на сервере.
5. Описывай ожидаемые ответы в документации FastAPI через `response_model`, `status_code` и `responses`.

## Коротко

`APIRouter` делит API на модули, Pydantic проверяет входные и формирует безопасные ответы, а `Depends` переиспользует общую логику. `GET` читает, `POST` создаёт, `PUT` заменяет. Статусы `2xx` означают успех, `4xx` — неверные действия клиента, `5xx` — проблемы сервера.
