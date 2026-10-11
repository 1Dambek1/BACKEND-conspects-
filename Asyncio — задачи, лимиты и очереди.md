# Asyncio — задачи, лимиты и очереди

В ноутбуке показаны основные инструменты `asyncio`: параллельный запуск ожиданий, таймауты, ограничение числа запросов, блокировка общего счётчика и очередь задач для нескольких работников.

Асинхронность полезна, когда программа часто **ждёт**: ответ сервера, базу данных или файл. Пока одна задача ждёт на `await`, event loop может запустить другую. Обычный код, который долго считает и не делает `await`, остановит остальные задачи в этом event loop.

## Запуск нескольких задач — `gather`

```python
import asyncio


async def get_data(seconds: int):
    await asyncio.sleep(seconds)  # изображаем ожидание ответа
    return f"Данные получены за {seconds} сек."


async def main():
    results = await asyncio.gather(
        get_data(1),
        get_data(2),
        get_data(3),
    )
    print(results)


asyncio.run(main())
```

`asyncio.gather()` запускает переданные операции вместе и возвращает результаты в том же порядке, в котором задачи были переданы. Здесь общее ожидание будет около трёх секунд, а не шести.

В Jupyter Notebook event loop уже запущен, поэтому обычно пишут `await main()` в ячейке. В обычном Python-файле используют `asyncio.run(main())`.

## Результаты по мере готовности — `as_completed`

Иногда не нужно ждать самую медленную задачу, чтобы начать обрабатывать остальные результаты:

```python
async def main():
    tasks = [get_data(3), get_data(1), get_data(2)]

    for task in asyncio.as_completed(tasks):
        result = await task
        print(result)
```

Результаты приходят по готовности: сначала примерно через секунду, потом через две, потом через три. Это удобно, например, если нужно показывать пользователю готовые результаты поиска, не дожидаясь всех источников.

## Ограничить число запросов — `Semaphore`

Если создать тысячу запросов сразу, можно перегрузить внешний API или собственный сервер. `asyncio.Semaphore(5)` разрешает одновременно выполнять участок кода максимум пяти задачам.

```python
import asyncio

semaphore = asyncio.Semaphore(5)


async def send_request(number: int):
    async with semaphore:
        print(f"Запрос {number} отправлен")
        await asyncio.sleep(1)  # ожидание ответа API
        return f"Ответ {number}"


async def main():
    results = await asyncio.gather(
        *(send_request(number) for number in range(20))
    )
    print(results)


asyncio.run(main())
```

Будет создано 20 задач, но одновременно внутри `async with semaphore` окажутся максимум пять. Остальные подождут, пока разрешение освободится.

Для реального API дополнительно учитывают лимиты сервиса, обрабатывают ошибки и настраивают таймаут соединения.

## Ограничить время ожидания — `wait_for`

Если сервис не отвечает, можно прекратить ожидание через заданное время:

```python
async def main():
    try:
        result = await asyncio.wait_for(
            get_data(5),
            timeout=2,
        )
        print(result)
    except TimeoutError:
        print("Сервис не ответил вовремя")
```

`wait_for` ждёт не дольше двух секунд. При таймауте он отменяет ожидаемую задачу и вызывает `TimeoutError`. Поэтому в реальном коде отмену важно не скрывать и при необходимости освобождать ресурсы в `finally`.

Не используй голый `except:`: он ловит почти все исключения, в том числе отмену задачи. Перехватывай ожидаемые ошибки, например `TimeoutError`.

## Защитить общее значение — `Lock`

Несколько асинхронных задач могут менять общие данные. Если между чтением и записью есть `await`, другая задача может вмешаться. `asyncio.Lock` позволяет только одной задаче одновременно находиться в защищённом участке.

```python
counter = 0
lock = asyncio.Lock()


async def increment():
    global counter
    async with lock:
        current = counter
        await asyncio.sleep(0)  # уступаем управление другим задачам
        counter = current + 1


async def main():
    await asyncio.gather(*(increment() for _ in range(1000)))
    print(counter)  # 1000


asyncio.run(main())
```

Без блокировки несколько задач могут прочитать одно значение и перезаписать результат друг друга. `async with lock` автоматически освобождает блокировку после выхода из участка, даже если случилась ошибка.

`asyncio.Lock` предназначен для задач одного event loop. Для обычных потоков применяют блокировки из `threading`.

## Очередь и рабочие задачи — `asyncio.Queue`

Очередь разделяет тех, кто создаёт работу, и тех, кто её выполняет. Например, обработчик API кладёт задание в очередь, а несколько работников обрабатывают задания.

```python
import asyncio


async def producer(queue: asyncio.Queue):
    for number in range(10):
        await queue.put(number)
        print(f"Добавили задачу {number}")


async def worker(queue: asyncio.Queue, worker_id: int):
    while True:
        item = await queue.get()
        try:
            print(f"Работник {worker_id} обрабатывает {item}")
            await asyncio.sleep(1)
        finally:
            queue.task_done()


async def main():
    queue = asyncio.Queue(maxsize=5)

    workers = [
        asyncio.create_task(worker(queue, worker_id))
        for worker_id in range(3)
    ]

    await producer(queue)
    await queue.join()  # ждём, пока все добавленные задачи обработаны

    for task in workers:
        task.cancel()

    await asyncio.gather(*workers, return_exceptions=True)


asyncio.run(main())
```

- `queue.put(item)` кладёт задачу. Если очередь заполнена, `put` ждёт свободного места.
- `queue.get()` забирает задачу. Если очередь пуста, работник ждёт.
- `queue.task_done()` сообщает, что взятая задача закончена.
- `queue.join()` ждёт, пока для каждого добавленного элемента вызовут `task_done()`.
- `maxsize=5` ограничивает очередь пятью элементами. Это создаёт обратное давление: производитель ждёт, если работники не успевают.
- `asyncio.create_task()` запускает работника в фоне относительно текущей корутины.
- После завершения очереди бесконечных работников нужно остановить. `cancel()` просит задачу завершиться, `gather(..., return_exceptions=True)` дожидается отмены.

В примере `finally` нужен, чтобы вызвать `task_done()` даже при отмене работника во время обработки. Для важных фоновых задач в production обычно нужны более надёжная очередь, хранение заданий и обработка повторных попыток.

## Как выбрать инструмент

| Нужно | Инструмент |
| --- | --- |
| Запустить несколько операций и получить все результаты | `asyncio.gather()` |
| Обрабатывать ответы по готовности | `asyncio.as_completed()` |
| Не превышать число одновременных запросов | `asyncio.Semaphore` |
| Ограничить время ожидания | `asyncio.wait_for()` |
| Безопасно менять общие данные между задачами | `asyncio.Lock` |
| Передавать работу нескольким обработчикам | `asyncio.Queue` |

## Коротко

`asyncio` помогает эффективно ждать несколько операций ввода-вывода. `Semaphore` ограничивает одновременную нагрузку, `wait_for` задаёт таймаут, `Lock` защищает общий участок, а `Queue` распределяет задания между работниками.

## Документация

- [Задачи и корутины asyncio](https://docs.python.org/3/library/asyncio-task.html)
- [Очереди asyncio](https://docs.python.org/3/library/asyncio-queue.html)
- [Блокировки asyncio](https://docs.python.org/3/library/asyncio-sync.html)
