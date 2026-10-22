# Лабораторная работа N20. Вариант 7
# Фитнес-клуб. Контейнеризация (Docker), CI/CD, эксплуатация.
#
# Приложение: Flask-приложение фитнес-клуба из ЛР 15.
# Добавляем: Dockerfile, .dockerignore, docker-compose.yml, healthcheck,
# переменные окружения, CI workflow (GitHub Actions).
#
# Файлы проекта:
#   main.py          - Flask-приложение фитнес-клуба
#   Dockerfile       - контейнеризация
#   docker-compose.yml - приложение + БД
#   .github/workflows/ci.yml - автоматические тесты
#   tests/ - тесты
#   requirements.txt - зависимости

import os
from flask import Flask, jsonify

# Приложение из ЛР 15 (фитнес-клуб) с добавлением /health и конфигурации
app = Flask(__name__)

# Конфигурация из переменных окружения (НЕ в исходном коде)
# Например для PostgreSQL:
#   DATABASE_URL=postgresql+psycopg://user:password@db:5432/fitness
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///fitness.db")
SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SECRET_KEY"] = SECRET_KEY


@app.get("/health")
def health():
    """Health check для Docker и CI."""
    # Проверим, что БД доступна (упрощённо - просто отвечаем 200)
    return jsonify({"status": "healthy", "database": DATABASE_URL.split("//")[0]})


@app.get("/")
def index():
    return jsonify({"service": "fitness-club", "version": "1.0"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=DEBUG)


# ============================================================
# Dockerfile
# ============================================================
# FROM python:3.11-slim
#
# WORKDIR /app
#
# # Установка зависимостей отдельно (кэширование слоёв)
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt
#
# # Копирование исходного кода
# COPY . .
#
# # Команда запуска
# CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "main:app"]
# ============================================================


# ============================================================
# .dockerignore
# ============================================================
# .git
# .venv
# __pycache__
# *.pyc
# .pytest_cache
# .env
# *.db
# ============================================================


# ============================================================
# docker-compose.yml
# ============================================================
# services:
#   app:
#     build: .
#     environment:
#       DATABASE_URL: postgresql+psycopg://fitness:fitness@db:5432/fitness
#       SECRET_KEY: ${SECRET_KEY}
#     ports:
#       - "8000:8000"
#     depends_on:
#       db:
#         condition: service_healthy
#     healthcheck:
#       test: ["CMD", "python", "-c", "import urllib.request;urllib.request.urlopen('http://localhost:8000/health')"]
#       interval: 30s
#       timeout: 5s
#       retries: 3
#
#   db:
#     image: postgres:16
#     environment:
#       POSTGRES_USER: fitness
#       POSTGRES_PASSWORD: fitness
#       POSTGRES_DB: fitness
#     volumes:
#       - postgres_data:/var/lib/postgresql/data
#     healthcheck:
#       test: ["CMD-SHELL", "pg_isready -U fitness"]
#       interval: 10s
#       retries: 5
#
# volumes:
#   postgres_data:
# ============================================================


# ============================================================
# .github/workflows/ci.yml
# ============================================================
# name: CI
#
# on:
#   push:
#   pull_request:
#
# jobs:
#   test:
#     runs-on: ubuntu-latest
#     steps:
#       - uses: actions/checkout@v4
#       - name: Setup Python
#         uses: actions/setup-python@v5
#         with:
#           python-version: "3.11"
#       - name: Install dependencies
#         run: pip install -r requirements.txt
#       - name: Lint
#         run: ruff check .
#       - name: Run tests
#         run: pytest --cov=src --cov-fail-under=70
#       - name: Docker build
#         run: docker build -t fitness-club .
# ============================================================


# ============================================================
# requirements.txt
# ============================================================
# flask
# flask-sqlalchemy
# gunicorn
# pytest
# pytest-cov
# ruff
# psycopg2-binary
# ============================================================


def main():
    print("Контейнеризация фитнес-клуба (вариант 7) готова.")
    print("Запуск: docker compose up --build")
    print("Проверка: curl http://localhost:8000/health")


if __name__ == "__main__":
    main()