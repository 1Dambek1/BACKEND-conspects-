# SQL — основы

SQL — язык, через который программа работает с базой данных: создаёт таблицы, добавляет данные, ищет, меняет и удаляет их.

Представь таблицу `users`:

| id | name | username | age | city | salary |
| --- | --- | --- | --- | --- | --- |
| 1 | Denis | dambek | 17 | Irkutsk | 80000 |
| 2 | Maria | maria_ml | 25 | Moscow | 210000 |

## Главные команды

### Создать таблицу — `CREATE TABLE`

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    username TEXT UNIQUE NOT NULL,
    age INTEGER NOT NULL,
    height INTEGER DEFAULT 165,
    city TEXT NOT NULL,
    salary INTEGER NOT NULL
);
```

- `PRIMARY KEY` — уникальный номер строки.
- `NOT NULL` — поле обязательно.
- `UNIQUE` — одинаковые значения запрещены. Например, два пользователя не могут иметь один `username`.
- `DEFAULT 165` — если рост не передали, база подставит `165`.

### Добавить данные — `INSERT`

```sql
INSERT INTO users (name, username, age, height, city, salary)
VALUES ('Denis', 'dambek', 17, 186, 'Irkutsk', 80000);
```

### Получить данные — `SELECT`

```sql
-- все поля и все пользователи
SELECT * FROM users;

-- только имя и город
SELECT name, city FROM users;

-- пользователи из Иркутска
SELECT * FROM users WHERE city = 'Irkutsk';

-- пользователи с зарплатой от 150 000
SELECT name, salary FROM users WHERE salary >= 150000;
```

### Сортировка и ограничение — `ORDER BY`, `LIMIT`

```sql
-- три самых высокооплачиваемых пользователя
SELECT name, salary
FROM users
ORDER BY salary DESC
LIMIT 3;
```

- `ASC` — по возрастанию, это значение по умолчанию.
- `DESC` — по убыванию.
- `LIMIT` — сколько строк вернуть.

### Изменить данные — `UPDATE`

```sql
UPDATE users
SET salary = 100000
WHERE username = 'dambek';
```

Всегда указывай `WHERE`, если не нужно изменить все строки таблицы.

### Удалить данные — `DELETE`

```sql
DELETE FROM users
WHERE username = 'dambek';
```

Без `WHERE` команда удалит все строки:

```sql
DELETE FROM users;
```

## Условия — `WHERE`

```sql
-- несколько условий одновременно
SELECT * FROM users
WHERE city = 'Moscow' AND age >= 22;

-- хотя бы одно условие
SELECT * FROM users
WHERE city = 'Irkutsk' OR city = 'Kazan';

-- поиск по списку
SELECT * FROM users
WHERE city IN ('Irkutsk', 'Kazan');

-- поиск по части текста
SELECT * FROM users
WHERE username LIKE 'alex%';
```

`%` означает «любое количество символов». `alex%` найдёт `alex_backend`.

## Подсчёты — `COUNT`, `AVG`, `MAX`, `MIN`

```sql
-- сколько всего пользователей
SELECT COUNT(*) FROM users;

-- средняя зарплата
SELECT AVG(salary) FROM users;

-- самая большая зарплата
SELECT MAX(salary) FROM users;
```

## Группировка — `GROUP BY`

```sql
-- количество пользователей в каждом городе
SELECT city, COUNT(*) AS users_count
FROM users
GROUP BY city;
```

## Связи таблиц

Одна таблица может ссылаться на другую через внешний ключ (`FOREIGN KEY`). Например, у каждого заказа есть пользователь:

```sql
CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    total INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

Чтобы получить заказ вместе с именем пользователя, используют `JOIN`:

```sql
SELECT orders.id, users.name, orders.total
FROM orders
JOIN users ON orders.user_id = users.id;
```

## Коротко

`CREATE` создаёт таблицы, `INSERT` добавляет данные, `SELECT` читает, `UPDATE` меняет, `DELETE` удаляет. SQLAlchemy позволяет делать то же самое из Python-кода, не записывая большинство SQL-запросов руками.
