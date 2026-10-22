# Лабораторная работа №20 — вариант 7

**Тема:** контейнеризация, CI/CD и эксплуатация Python-приложения.
**Задание:** фитнес-клуб.

## Что делает программа

Приложение фитнес-клуба (Flask) подготовлено к развёртыванию: описаны
`Dockerfile`, `.dockerignore`, `docker-compose.yml` (приложение + PostgreSQL с
volume и healthcheck), конфигурация через переменные окружения, endpoint
`/health`, а также GitHub Actions CI workflow (установка зависимостей, lint,
pytest с порогом покрытия, сборка Docker-образа).

## Запуск

```bash
docker compose up --build
curl http://localhost:8000/health
```

## Структура

- `main.py` — Flask-приложение с `/health` и чтением конфигурации из окружения;
- встроенные примеры `Dockerfile`, `.dockerignore`, `docker-compose.yml`,
  `requirements.txt` и `.github/workflows/ci.yml`.

## Что реализовано

- Dockerfile на официальном Python-образе;
- переменные окружения (DATABASE_URL, SECRET_KEY) без секретов в коде;
- docker-compose с приложением и БД, volume и healthcheck;
- CI: checkout → python setup → install → lint → pytest → docker build;
- `.env.example` для локальной разработки.

## Проверки

- `/health` возвращает `{"status":"healthy"}`;
- данные БД переживают перезапуск контейнера (volume);
- CI завершается ошибкой при неуспешных тестах или сборке.