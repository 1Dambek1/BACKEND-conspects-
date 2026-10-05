# SQLAlchemy — связи и загрузка

В SQL связь таблиц задаётся внешним ключом (`FOREIGN KEY`). В SQLAlchemy внешний ключ описывает связь в базе, а `relationship()` даёт удобный доступ к связанным объектам Python.

Пример: пользователь и его профиль, пользователь и товары, а также пользователи и товары через таблицу-связку. Код написан в стиле SQLAlchemy 2.x.

## Один-к-одному

Один пользователь может иметь один профиль. Уникальность `user_id` в базе обеспечивает `unique=True`.

```python
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)

    profile: Mapped["Profile"] = relationship(back_populates="user")


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    bio: Mapped[str | None]

    user: Mapped["User"] = relationship(back_populates="profile")
```

`Profile.user_id` — внешний ключ в базе. `User.profile` и `Profile.user` — Python-атрибуты, которые связывают объекты в обе стороны. `back_populates` указывает друг на друга.

По аннотации `Mapped["Profile"]` видно, что у пользователя один профиль, а не список профилей.

## Один-ко-многим и многие-к-одному

Один пользователь может иметь несколько товаров. Внешний ключ находится в таблице товаров.

```python
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str]

    products: Mapped[list["Product"]] = relationship(back_populates="user")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    price: Mapped[float]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    user: Mapped["User"] = relationship(back_populates="products")
```

- `User.products` — список товаров пользователя.
- `Product.user` — пользователь, которому принадлежит товар.
- `ForeignKey("users.id")` создаёт внешний ключ на колонку `users.id`.

Когда добавлен товар, SQLAlchemy может связать объекты напрямую:

```python
user = User(username="denis")
product = Product(name="Keyboard", price=5000, user=user)

session.add(product)
session.commit()
```

Можно задать связь и со стороны пользователя:

```python
user.products.append(Product(name="Mouse", price=2500))
session.commit()
```

## Многие-ко-многим с таблицей-связкой

В твоём примере один пользователь может иметь разные товары, а один товар может встречаться у разных пользователей. Таблица `user_products` соединяет их. В ней ещё хранится `quantity` — количество товара.

Если у таблицы-связки есть свои данные (`quantity`, дата добавления, цена покупки), её нужно описать отдельной моделью. Этот вариант называется моделью-связкой.

```python
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str]

    user_products: Mapped[list["UserProduct"]] = relationship(
        back_populates="user"
    )


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    price: Mapped[float]

    user_products: Mapped[list["UserProduct"]] = relationship(
        back_populates="product"
    )


class UserProduct(Base):
    __tablename__ = "user_products"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), primary_key=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"), primary_key=True
    )
    quantity: Mapped[int] = mapped_column(default=1)

    user: Mapped["User"] = relationship(back_populates="user_products")
    product: Mapped["Product"] = relationship(back_populates="user_products")
```

Теперь `quantity` принадлежит объекту `UserProduct`, поэтому к нему можно обратиться напрямую:

```python
link = UserProduct(user=user, product=product, quantity=2)
session.add(link)
session.commit()

print(link.user.username)
print(link.product.name)
print(link.quantity)
```

Названия моделей можно оставить как в твоём проекте (`UserProducts`, `Products`). Важно, чтобы `relationship()` и `back_populates` ссылались на правильные атрибуты и чтобы внешний ключ указывал на существующую таблицу.

### Почему не `secondary` в этом примере?

Упрощённую связь многие-ко-многим можно описать через `secondary="user_products"`, если таблица-связка нужна только для хранения двух внешних ключей. Но в проекте `user_products` хранит ещё и `quantity`, поэтому модель-связка даёт доступ к этому полю и удобнее для работы.

## `selectinload` — загрузить связанные объекты заранее

По умолчанию связанный объект часто загружается при обращении к атрибуту. Если загружать список пользователей, а потом для каждого отдельно читать товары, получится много отдельных запросов к базе.

`selectinload()` загружает сначала основные объекты, затем связанные данные отдельным запросом с `IN (...)`. Для списка объектов это позволяет не отправлять по запросу на каждую строку.

### Загрузить товары пользователя через модель-связку

```python
from sqlalchemy import select
from sqlalchemy.orm import selectinload

statement = select(User).options(
    selectinload(User.user_products).selectinload(UserProduct.product)
)

users = session.scalars(statement).all()

for user in users:
    print(user.username)
    for link in user.user_products:
        print(link.product.name, link.quantity)
```

Здесь загружаются:

1. Пользователи.
2. Связанные с ними строки `UserProduct`.
3. Товары для каждой строки-связки.

Для связи один-ко-многим синтаксис короче:

```python
statement = select(User).options(selectinload(User.products))
users = session.scalars(statement).all()
```

`selectinload()` задаётся для конкретного запроса. Он не меняет сами таблицы или связи, а указывает SQLAlchemy, как получить связанные объекты.

## Коротко

`ForeignKey` создаёт связь в базе. `relationship()` связывает Python-модели. Список `Mapped[list[...]]` используют для коллекции, а `Mapped["... "]` — для одного связанного объекта. В `user_products` есть `quantity`, поэтому удобнее описать её отдельной моделью `UserProduct`. `selectinload()` заранее загружает связанные объекты для выбранного запроса.

## Документация

- [Основные виды связей в SQLAlchemy](https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html)
- [Загрузка связей и selectinload](https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html)
