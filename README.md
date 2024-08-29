# Content Aggregator API

Content Aggregator API — это микросервис для управления балансом пользователей, позволяющий зачислять, 
списывать и отображать средства в различных валютах. 
Сервис поддерживает конвертацию баланса по актуальным курсам Центробанка и предоставляет историю транзакций.

## Оглавление

- [Установка и использование](#установка-и-использование)
- [Структура проекта](#структура-проекта)
- [API Эндпоинты](#api-эндпоинты)
- [Docker](#docker)
- [Тестирование](#тестирование)

### Предварительные требования

- Убедитесь, что у вас установлены Docker и Docker Compose
- Версия Python: 3.11

### Установка и использование

1. Клонируйте репозиторий:
    ```sh
    git clone https://github.com/RedHotChilliHead/avito_tech_balance.git
    cd avito_tech_balance
    ```

2. Установите зависимости:
    ```sh
    pip install -r requirements.txt
    ```

3. Запуск всех контейнеров:
    ```sh
    docker compose up -d
    ```
Примечание: Миграции применять не нужно, так как база данных инициализируется из дампа schema.sql, который находится в директории initdb.

После запуска сервер будет доступен по адресу: http://127.0.0.1:8000.

## Структура проекта

- urls.py (корневой): Конфигурация маршрутизации URL проекта, включая маршруты для административного интерфейса.
- urls.py (приложение): Конфигурация маршрутизации URL для приложения, включая маршруты для пользователей, переводов транзакций.
- models.py: Модели для пользователей и транзакций.
- serializers.py: Сериализаторы для преобразования данных между моделями и форматами JSON.
- views.py: Определения представлений для обработки запросов к API, включая создание, обновление, удаление и получение данных.
- tests.py: Тесты для проверки API.

## API Эндпоинты

### Создание пользователя

Создает пользователя с начальным балансом 0.00 рублей.

#### URL

```
POST /balance/customers
```

#### Пример запроса

```sh
curl -X POST -H 'Content-Type: application/json' -d '{"name":"Antonio Banderas"}' http://127.0.0.1:8000//balance/customers/
```

#### Пример ответа

```json
{"id":2,"name":"Antonio Banderas","balance":"0.00","valute":"RUB"}
```

### Список пользователей

Отображает список всех пользователей с балансом по умолчанию в рублях.

#### URL

```
GET /balance/customers
```

#### Пример запроса

```sh
curl -X GET http://127.0.0.1:8000/balance/customers/
```

#### Пример ответа

```json
{"count":2,"next":null,"previous":null,"results":[{"id":1,"name":"Irina","balance":"0.00","valute":"RUB"},{"id":2,"name":"Antonio Banderas","balance":"0.00","valute":"RUB"}]}
```

### Детальная информация о пользователе

Отображает детали пользователя.

Для вывода баланса в других валютах необходимо использовать параметр запроса currency и кодовое обозначение валюты.
Курс валюты будет актуальным на текущую дату относительно рубля, 
данные о курсе валют берутся с официального сайта Центрального Банка России http://www.cbr.ru/.

#### URL

```
GET /balance/customers/<int:id>
```

#### Пример запроса

```sh
curl -X GET 'http://127.0.0.1:8000/balance/customers/1/?currency=USD'
```

#### Пример ответа

```json
{"id":1,"name":"Irina","balance":"0.00","valute":"USD"}
```

### Редактирование пользователя

Позволяет редактировать имя пользователя.

#### URL

```
PUT /balance/customers/<int:id>
```

#### Пример запроса

```sh
curl -X PUT -H 'Content-Type: application/json' -d '{"name":"Natalia Oreiro"}' http://127.0.0.1:8000//balance/customers/1/
```

#### Пример ответа

```json
{"id":1,"name":"Natalia Oreiro","balance":"0.00","valute":"RUB"}
```

### Удаление пользователя

Удаляет пользователя из базы данных.

#### URL

```
DELETE /balance/customers/<int:id>
```

#### Пример запроса

```sh
curl -X DELETE http://127.0.0.1:8000//balance/customers/1/
```

#### Успешным выполнением метода удаления пользователя является пустой ответ

### Операции с балансом

#### Описание

Позволяет зачислить или списать средства.
Для данного метода не обязательно указывать источник зачисления средств и получателя в случае списания,
так как в первом случае источником будет банк, а во втором получателем является платформа Avito.

Обязательны параметры:
- **amount**: сумма зачисления/списания
- **operation**: тип операции, 'withdraw' (зачисление средств на счет) или 'deposit' (списание средств)

Не обязательные параметры:
- **description**: описание

#### URL

```
POST /balance/customers/<int:customer_id>/operations/
```

#### Пример запроса

```sh
curl -X POST -H 'Content-Type: application/json' -d '{"amount": 1000000, "operation": "withdraw", "description": "for a new car"}' http://127.0.0.1:8000//balance/customers/2/operations/
```

#### Пример ответа

```json
{"OK":"The operation was successful"}
```

### Перевод средств

Перевод средств с одного пользователя на другого.

Обязательны параметры:
- **sender**: индентификатор отправителя средств
- **recipient**: индентификатор получателя средств
- **amount**: сумма

Не обязательные параметры:
- **description**: описание

#### URL

```http
`POST /balance/transfer/`
```

#### Пример запроса

```sh
curl -X POST -H 'Content-Type: application/json' -d '{"amount": 500, "sender": "2", "recipient": "3", "description": "present"}' http://127.0.0.1:8000//balance/transfer/
```

#### Пример ответа

```json
{"OK":"The operation was successful"}
```

### Список транзакций

Отображает список всех транзакций пользователя с возможностью сортировки по дате и сумме.

Не обязательные параметры запроса:
- **?order=timestamp**: сортировка по дате
- **?order=amount**: сортировка по сумме

Для сортировки по убыванию параметр запроса должен начинаться с "-", например **?order=-amount**
Сортировка по умолчанию - по уникальному идентификатору (id) в порядке возрастания.

#### URL

```
GET /balance/customers/<int:customer_id>/transactions/
```

#### Пример запроса

```sh
curl -X GET "http://127.0.0.1:8000//balance/customers/2/transactions/?order=-amount"
```

#### Пример ответа

```json
{
  "count":2,
  "next":null,
  "previous":null,
  "results":
  [
    {
      "id":1,
      "amount":"1000000.00",
      "timestamp":"2024-07-26T08:46:04.236372Z",
      "description":"for a new car",
      "sender":null,
      "recipient":2
    },
    {
      "id":2,
      "amount":"500.00",
      "timestamp":"2024-07-26T08:56:15.465247Z",
      "description":"present",
      "sender":2,
      "recipient":3
    }
  ]
}
```

Во всех методах реализована валидация, в случае передачи некорректных параметров будет выведено соответствующее сообщение об ошибке.

## Docker

Проект использует Docker для контейнеризации. Основные команды:

- Запуск всех контейнеров:
    ```sh
    docker compose up
    ```
  
- Запуск всех контейнеров в фоновом режиме:
    ```sh
    docker compose up -d
    ```

- Остановка всех контейнеров:
    ```sh
    docker compose down
    ```

- Создание и удаление тома для базы данных PostgreSQL:
    ```sh
    docker volume create balance_postgres_data
    docker volume rm balance_postgres_data
    ```

## Тестирование

Запуск тестов для проверки функциональности API:

```sh
docker compose run balanceapp python magae.py test
```