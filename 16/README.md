# Лабораторная работа №16 — вариант 7

**Тема:** разработка веб-приложения на Python с использованием Django.
**Задание:** автосервис.

## Что делает программа

Модели Django: `Client`, `Car`, `Service`, `Order` со связями `ForeignKey`
(автомобиль принадлежит клиенту, заказ-наряд ссылается на автомобиль и услугу).
Реализованы админ-панель для `Car` и `Order`, Class-Based Views (основа для CRUD)
и примеры обязательных ORM-операций: `all`, `filter`, `exclude`, `get`,
`order_by`, `count`, `exists`, `aggregate`, `annotate`, `select_related`
(устранение N+1).

## Запуск

Полный проект Django создаётся командами:

```bash
pip install django
django-admin startproject config .
python manage.py startapp autoservice
```

Модели из этого файла помещаются в `autoservice/models.py`, после чего:

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Структура

- `models.py` — модели Client, Car, Service, Order + примеры ORM-запросов;
- `admin.py`-блоки регистрации моделей в Admin;
- Class-Based Views и отчёт показаны в закомментированной части для переноса в полный проект.

## Админ-панель

- `CarAdmin` — list_display, list_filter по марке и состоянию, search по марке/модели/владельцу;
- `OrderAdmin` — list_display и list_filter по статусу.

## ORM

В коде приведена функция `orm_examples()` с примерами всех обязательных ORM-операций
и демонстрацией `select_related` для предотвращения N+1-запросов.