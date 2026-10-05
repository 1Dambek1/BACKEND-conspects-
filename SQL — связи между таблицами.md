# SQL — связи между таблицами

Связь показывает, как строки одной таблицы относятся к строкам другой. Для этого используют внешний ключ (`FOREIGN KEY`). Он хранит ID строки из другой таблицы.

Ниже три основные связи: один-к-одному, один-ко-многим и многие-ко-многим.

## Один-к-одному

Одна запись связана максимум с одной записью в другой таблице. Например, у пользователя один профиль.

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE
);

CREATE TABLE profiles (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE,
    bio TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

`profiles.user_id` указывает на пользователя. `UNIQUE` не даёт создать два профиля для одного пользователя. `NOT NULL` означает, что профиль не может быть без пользователя.

Пример данных:

```sql
INSERT INTO users (id, username) VALUES (1, 'denis');
INSERT INTO profiles (id, user_id, bio) VALUES (1, 1, 'Учу backend');
```

Получить пользователя вместе с профилем:

```sql
SELECT users.username, profiles.bio
FROM users
JOIN profiles ON profiles.user_id = users.id;
```

## Один-ко-многим и многие-к-одному

Один пользователь может иметь много товаров, а каждый товар принадлежит одному пользователю. Внешний ключ находится в таблице «многие» — здесь в `products`.

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE
);

CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    user_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

Добавим пользователя и его товары:

```sql
INSERT INTO users (id, username) VALUES (1, 'denis');

INSERT INTO products (name, price, user_id)
VALUES ('Keyboard', 5000, 1), ('Mouse', 2500, 1);
```

Получить товары пользователя:

```sql
SELECT users.username, products.name, products.price
FROM users
JOIN products ON products.user_id = users.id
WHERE users.id = 1;
```

Направление «один-ко-многим»: `User → Products`. Обратное направление «многие-к-одному»: каждый `Product → User`. Это две стороны одной связи.

## Многие-ко-многим

У пользователя может быть много товаров, и один товар может быть у многих пользователей. Нельзя положить несколько ID в одно поле. Для такой связи создают третью таблицу-связку.

Например, `user_products` связывает пользователей с товарами и хранит количество каждого товара:

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE
);

CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    price REAL NOT NULL
);

CREATE TABLE user_products (
    user_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (user_id, product_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);
```

`PRIMARY KEY (user_id, product_id)` — составной первичный ключ: одна и та же пара «пользователь — товар» встречается только один раз. `quantity` — дополнительное поле связи.

Добавить товар пользователю:

```sql
INSERT INTO user_products (user_id, product_id, quantity)
VALUES (1, 10, 2);
```

Получить все товары пользователя:

```sql
SELECT users.username, products.name, products.price, user_products.quantity
FROM user_products
JOIN users ON users.id = user_products.user_id
JOIN products ON products.id = user_products.product_id
WHERE users.id = 1;
```

## Как выбрать связь

| Ситуация | Связь | Где хранится внешний ключ |
| --- | --- | --- |
| У пользователя один профиль | Один-к-одному | `profiles.user_id` с `UNIQUE` |
| У пользователя много товаров, товар принадлежит одному пользователю | Один-ко-многим | `products.user_id` |
| Пользователь может выбрать много товаров, товар может быть у многих пользователей | Многие-ко-многим | В таблице-связке `user_products` |

`JOIN` нужен, чтобы получить данные сразу из нескольких связанных таблиц. В SQLAlchemy связь тоже строится на внешних ключах, а `relationship()` помогает переходить от объекта одной модели к связанным объектам.
