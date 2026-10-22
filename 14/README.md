# Лабораторная работа №14 — вариант 7

**Тема:** разработка REST API на Python с использованием FastAPI.
**Задание:** автосервис — автомобили.

## Что делает программа

REST API на FastAPI с Pydantic-схемами (`CarCreate`, `CarUpdate`,
`CarResponse`, `CarListResponse`). Реализованы полный CRUD, фильтрация,
сортировка, пагинация, поиск, статистика, специализированный endpoint,
асинхронный endpoint и отдача HTTP-кодов. Хранение данных — в памяти;
структура Router/Service/Repository соблюдена.

## Эндпоинты

| Метод | Endpoint | Назначение |
|---|---|---|
| GET | `/cars` | список с фильтрацией, сортировкой, пагинацией, поиском |
| GET | `/cars/{id}` | один автомобиль |
| POST | `/cars` | создание (201) |
| PUT | `/cars/{id}` | полное изменение |
| PATCH | `/cars/{id}` | частичное изменение |
| DELETE | `/cars/{id}` | удаление (204) |
| GET | `/cars/in-repair` | автомобили в ремонте |
| GET | `/cars/statistics` | статистика |
| GET | `/cars/search/{term}` | асинхронный поиск |
| GET | `/health` | проверка состояния |

## Запуск

```bash
pip install fastapi uvicorn pydantic
uvicorn main:app --reload
```

Swagger-документация: `http://127.0.0.1:8000/docs`.

## Структура

- `main.py` — схемы, репозиторий, сервис, endpoints, инициализация.

## Проверки

- валидация через Pydantic (`Field`, диапазоны);
- корректные HTTP-коды (201, 204, 404, 422);
- бизнес-логика отделена от HTTP-обработчиков (Service/Repository).