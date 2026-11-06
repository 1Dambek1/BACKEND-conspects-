# Авторизация в FastAPI — пароли, JWT и сессии

Денис вошёл в приложение и открыл заметку № 2. Серверу нужно ответить на два разных вопроса:

- **Аутентификация:** «Кто прислал запрос?» При входе сервер проверяет пароль. В следующих запросах узнаёт пользователя по JWT или по ID сессии.
- **Авторизация:** «Может ли этот пользователь читать заметку № 2?» Даже правильный пароль не даёт доступа к чужим заметкам.

**Argon2id** нужен для проверки пароля. **JWT и серверная сессия** — два способа запомнить вход. Собери блоки Python из разделов 1–4 в один `main.py`. В конце есть команды, чтобы попробовать оба варианта.

## 1. Проверяем пароль через Argon2id

Установка для Python 3.10+: `python -m pip install fastapi uvicorn "pwdlib[argon2]" "PyJWT>=2,<3"`. Пакет для JWT называется **PyJWT**, в коде он импортируется как `jwt`.

```python
import os

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, SecretStr
from pwdlib import PasswordHash

app = FastAPI()
passwords = PasswordHash.recommended()

# Учебный пользователь. В настоящем приложении хеш записывают
# в базу при регистрации и читают из базы при входе.
user = {"id": "7", "login": "denis",
        "password_hash": passwords.hash(os.environ["DEMO_PASSWORD"])}


class Login(BaseModel):
    login: str
    password: SecretStr


def authenticate(data: Login) -> str:
    ok = passwords.verify(data.password.get_secret_value(), user["password_hash"])
    if not ok or data.login != user["login"]:
        raise HTTPException(401, "Неверный логин или пароль")
    return user["id"]
```

При регистрации `hash()` берёт пароль, добавляет случайную **соль** и считает хеш Argon2id. Соль и параметры уже входят в строку хеша. Поэтому два хеша одного пароля обычно разные. При входе `verify()` берёт соль из сохранённого хеша и проверяет введённый пароль. Расшифровывать ничего не нужно. Argon2id расходует память и время, чтобы перебор украденных хешей был дороже. [Подробнее о хранении паролей](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html).

## 2. Вход через JWT: клиент предъявляет подписанный токен

После проверки пароля сервер выдаёт строку из трёх частей: `заголовок.данные.подпись`. Данные подписанного JWT можно прочитать, поэтому в них кладём ID пользователя и срок действия. Подпись позволяет обнаружить подмену: если заменить ID на чужой, проверка не пройдёт.

```python
from datetime import datetime, timedelta, timezone

import jwt
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

key = os.environ["JWT_SECRET"]
bearer = HTTPBearer(auto_error=False)


@app.post("/login/token")
def login_token(data: Login):
    uid = authenticate(data)
    expires = datetime.now(timezone.utc) + timedelta(minutes=15)
    token = jwt.encode({"sub": uid, "exp": expires}, key, algorithm="HS256")
    return {"access_token": token, "token_type": "bearer"}


def jwt_user(auth: HTTPAuthorizationCredentials | None = Depends(bearer)) -> str:
    denied = HTTPException(401, "Нужен действующий токен",
                           headers={"WWW-Authenticate": "Bearer"})
    if auth is None:
        raise denied
    try:
        payload = jwt.decode(auth.credentials, key, algorithms=["HS256"],
                             options={"require": ["sub", "exp"]})
    except jwt.InvalidTokenError:
        raise denied
    return payload["sub"]
```

В следующем запросе клиент отправляет заголовок `Authorization: Bearer <access_token>`. Сервер проверяет подпись и срок действия (`exp`), затем берёт ID из `sub`. Допустимый алгоритм сервер задаёт сам. [Проверка токена в PyJWT](https://pyjwt.readthedocs.io/en/stable/api.html#jwt.decode).

## 3. Проверяем право на конкретную заметку

```python
notes = {
    1: {"owner_id": "7", "title": "Мой список покупок"},
    2: {"owner_id": "8", "title": "Чужая заметка"},
}


@app.get("/notes/{note_id}")
def read_note(note_id: int, uid: str = Depends(jwt_user)):
    note = notes.get(note_id)
    if note is None:
        raise HTTPException(404, "Заметка не найдена")
    if note["owner_id"] != uid:
        raise HTTPException(403, "Нет доступа к этой заметке")
    return {"title": note["title"]}
```

Без токена Денис получит **401**. С действующим токеном он получит свою заметку № 1, но при запросе № 2 получит **403**: сервер его узнал, прав не хватило. Владельца берём из сохранённой заметки, а ID читателя — из проверенного токена. Поле `user_id`, которое клиент сам прислал в запросе, не доказывает, кто он.

## 4. Альтернатива JWT: серверная сессия

Представь номерок в гардеробе. Браузеру дают случайный номер, а сервер оставляет у себя запись «этот номер → пользователь 7, до такого-то времени». При следующем запросе браузер сам отправляет номер в cookie. Сервер может аннулировать его, удалив запись.

```python
import secrets
from time import monotonic

from fastapi import Cookie, Response

sessions: dict[str, tuple[str, float]] = {}
ttl = 30 * 60  # 30 минут


@app.post("/login/session")
def login_session(data: Login, response: Response, sid: str | None = Cookie(None)):
    uid = authenticate(data)
    if sid:
        sessions.pop(sid, None)
    new_id = secrets.token_urlsafe(32)
    sessions[new_id] = (uid, monotonic() + ttl)
    response.set_cookie("sid", new_id, max_age=ttl, httponly=True,
                        secure=True, samesite="lax", path="/")
    return {"message": "Вход выполнен"}


def session_user(sid: str | None = Cookie(None)) -> str:
    entry = sessions.get(sid) if sid else None
    if entry is None or entry[1] <= monotonic():
        if sid:
            sessions.pop(sid, None)
        raise HTTPException(401, "Нужно войти")
    return entry[0]


@app.get("/me")
def me(uid: str = Depends(session_user)):
    return {"user_id": uid}


@app.post("/logout")
def logout(response: Response, sid: str | None = Cookie(None)):
    if sid:
        sessions.pop(sid, None)
    response.delete_cookie("sid", path="/", secure=True, httponly=True, samesite="lax")
    return {"message": "Выход выполнен"}
```

`HttpOnly` закрывает cookie от чтения через JavaScript, `Secure` предназначен для HTTPS, `SameSite=Lax` ограничивает отправку cookie с другого сайта. Для запросов, меняющих данные, добавляют защиту от **CSRF**: например, сервер проверяет CSRF-токен. [Как защищают сессии](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html).

Словарь годится для опыта с одним процессом: при перезапуске все выйдут из аккаунта, а у второго worker-а будет свой словарь. В общем Redis тот же принцип выглядит так: `SET session:<id> 7 EX 1800` при входе, `GET` при запросе, `DEL` при выходе. Redis сам удалит запись через 30 минут.

Чтобы защитить заметки через сессию, в `read_note` замени `Depends(jwt_user)` на `Depends(session_user)`. Проверка владельца остаётся той же.

| Что сравниваем | JWT из примера | Серверная сессия |
| --- | --- | --- |
| Что присылает клиент | Подписанный токен в заголовке | Случайный ID в cookie |
| Как узнать пользователя | Проверить подпись и `exp`, прочитать `sub` | Найти действующую запись по ID |
| Что происходит при выходе | Клиент стирает токен. Его копия всё ещё действует до `exp`, если нет отдельного механизма отзыва | Сервер удаляет запись. Даже скопированный ID больше не подходит |

## Как попробовать

Перед запуском задай две переменные. В PowerShell для локального опыта:

```powershell
$env:DEMO_PASSWORD = "tolko-dlya-ucheby"
$env:JWT_SECRET = python -c "import secrets; print(secrets.token_hex(32))"
uvicorn main:app --reload
```

Открой [Swagger](http://127.0.0.1:8000/docs). В `POST /login/token` отправь `{"login":"denis","password":"tolko-dlya-ucheby"}`. Скопируй `access_token` в **Authorize** и сравни ответы `GET /notes/1` и `GET /notes/2`.

Для сценария с cookie открой приложение по **HTTPS**. Локально тот же сценарий можно пройти без сертификата: установи `python -m pip install httpx`, а затем выполни в Python с теми же переменными окружения:

```python
from fastapi.testclient import TestClient
from main import app

with TestClient(app, base_url="https://testserver") as browser:
    browser.post("/login/session", json={"login": "denis", "password": "tolko-dlya-ucheby"})
    print(browser.get("/me").json())         # {'user_id': '7'}
    browser.post("/logout")
    print(browser.get("/me").status_code)    # 401
```

Секрет подписи должен быть одинаковым у всех экземпляров API и храниться вне Git. В общем проекте его удобно читать через [Pydantic Settings](<Pydantic Settings — настройки приложения.md>).
