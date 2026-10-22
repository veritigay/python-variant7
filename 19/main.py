# Лабораторная работа N19. Вариант 7
# Фитнес-клуб. Микросервисная архитектура.
#
# Вариант 7 (Фитнес-клуб): сервисы "клиенты", "абонементы", "занятия".
# Реализовано: API Gateway, 3 микросервиса с собственными БД, Database per
# Service, Retry, Circuit Breaker, асинхронное событие через брокер (имитация).
#
# Структура (см. docker-compose.yml):
#   gateway/       - единая точка входа, маршрутизация
#   client-service/ - клиенты фитнес-клуба
#   subscription-service/ - абонементы
#   training-service/     - занятия, проверка действительности абонемента
#
# Для компактности каждый сервис - отдельный Python-файл с FastAPI.
# Здесь представлена центральная логика: Retry, Circuit Breaker, Gateway.

import json
import time
import random
from dataclasses import dataclass
from typing import Optional, Callable


# ================= Circuit Breaker =================
class CircuitBreaker:
    """Защита от каскадных отказов: closed -> open -> half-open."""
    def __init__(self, threshold=3, cooldown=5.0):
        self.threshold = threshold
        self.cooldown = cooldown
        self.failures = 0
        self.state = "CLOSED"
        self.opened_at = 0.0

    def allow(self) -> bool:
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            if time.time() - self.opened_at >= self.cooldown:
                self.state = "HALF-OPEN"
                return True
            return False
        # HALF-OPEN: разрешаем пробный запрос
        return True

    def record_success(self):
        self.failures = 0
        self.state = "CLOSED"

    def record_failure(self):
        self.failures += 1
        if self.failures >= self.threshold:
            self.state = "OPEN"
            self.opened_at = time.time()

    def __str__(self):
        return f"CircuitBreaker(state={self.state}, failures={self.failures})"


# ================= Retry =================
def retry(max_attempts=3, delay=0.2):
    """Декоратор повторной попытки при исключении."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            attempt = 0
            last_error = None
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as error:
                    last_error = error
                    attempt += 1
                    if attempt < max_attempts:
                        time.sleep(delay * attempt)
            raise last_error
        return wrapper
    return decorator


# ================= Имитация удалённых сервисов =================
class SubscriptionService:
    """Сервис абонементов (имитация удалённого HTTP-сервиса)."""
    def __init__(self):
        self.subscriptions = {
            1: {"client_id": 1, "expire": "2026-12-31", "active": True},
            2: {"client_id": 2, "expire": "2025-01-15", "active": False},
            3: {"client_id": 3, "expire": "2026-06-01", "active": True},
        }
        self.failing = False

    def check_valid(self, client_id):
        """Проверка действительности абонемента (может дать сбой)."""
        if self.failing:
            raise ConnectionError("Subscription service unavailable")
        sub = self.subscriptions.get(client_id)
        return bool(sub and sub["active"])


class ClientService:
    """Сервис клиентов (имитация)."""
    def __init__(self):
        self.clients = {
            1: {"name": "Иван Петров"},
            2: {"name": "Анна Сидорова"},
            3: {"name": "Пётр Кузнецов"},
        }

    def get_client(self, client_id):
        return self.clients.get(client_id)


class TrainingService:
    """Сервис занятий: проверяет абонемент через SubscriptionService."""
    def __init__(self, subscription_service):
        self.subscription = subscription_service
        self.trainings = []
        self.breaker = CircuitBreaker()
        self._next_id = 1

    @retry(max_attempts=3)
    def _check_subscription_safe(self, client_id):
        return self.subscription.check_valid(client_id)

    def book(self, client_id, trainer, date):
        """Запись на занятие с проверкой абонемента и Circuit Breaker."""
        if not self.breaker.allow():
            raise RuntimeError("Submission service temporarily unavailable "
                               "(circuit open)")
        try:
            valid = self._check_subscription_safe(client_id)
        except ConnectionError:
            self.breaker.record_failure()
            raise ConnectionError(f"Не удалось проверить абонемент клиента {client_id}; "
                                  f"{self.breaker}")
        self.breaker.record_success()
        if not valid:
            raise ValueError(f"Абонемент клиента {client_id} не действителен")
        entry = {"id": self._next_id, "client_id": client_id,
                 "trainer": trainer, "date": date}
        self._next_id += 1
        self.trainings.append(entry)
        event_publish("TrainingBooked", entry)
        return entry


# ================= Асинхронное событие (имитация брокера) =================
OBSERVERS = []


def event_publish(event_name, data):
    """Публикация события всем наблюдателям (Event-Driven)."""
    for observer in OBSERVERS:
        observer.on_event(event_name, data)


class NotificationObserver:
    def on_event(self, event_name, data):
        print(f"  [Notification] {event_name}: {data}")


class AnalyticsObserver:
    def on_event(self, event_name, data):
        print(f"  [Analytics] {event_name}: {data}")


class LogObserver:
    def on_event(self, event_name, data):
        print(f"  [Log] {event_name} -> {json.dumps(data, ensure_ascii=False)}")


OBSERVERS = [NotificationObserver(), AnalyticsObserver(), LogObserver()]


# ================= API Gateway =================
class Gateway:
    """Единая точка входа: маршрутизация между сервисами."""
    def __init__(self, clients, subscription, trainings):
        self.clients = clients
        self.subscription = subscription
        self.trainings = trainings

    def get_client(self, client_id):
        return self.clients.get_client(client_id)

    def check_subscription(self, client_id):
        return self.subscription.check_valid(client_id)

    def book_training(self, client_id, trainer, date):
        return self.trainings.book(client_id, trainer, date)


# ================= Демонстрация =================
def main():
    clients = ClientService()
    subscription = SubscriptionService()
    trainings = TrainingService(subscription)
    gateway = Gateway(clients, subscription, trainings)

    print("=== Фитнес-клуб: микросервисы (вариант 7) ===")
    print("Сервисы: client-service, subscription-service, training-service, gateway\n")

    print("1. Запись клиента с действительным абонементом:")
    training = gateway.book_training(1, "Тренер А", "2026-10-25")
    print(f"   Создана тренировка #{training['id']}\n")

    print("2. Клиент с просроченным абонементом:")
    try:
        gateway.book_training(2, "Тренер Б", "2026-10-25")
    except ValueError as error:
        print(f"   Ошибка: {error}\n")

    print("3. Сервис абонементов временно недоступен (Retry + Circuit Breaker):")
    subscription.failing = True
    for i in range(5):
        try:
            gateway.book_training(3, "Тренер В", "2026-10-26")
            break
        except (ConnectionError, RuntimeError) as error:
            print(f"   Попытка {i+1}: {str(error)[:60]}")
    print(f"   Состояние: {trainings.breaker}\n")

    print("Сервис восстановлен:")
    subscription.failing = False
    time.sleep(trainings.breaker.cooldown + 0.1)  # даём Circuit Breaker перейти в HALF-OPEN
    training = gateway.book_training(3, "Тренер В", "2026-10-26")
    print(f"   Тренировка #{training['id']} создана, {trainings.breaker}")


if __name__ == "__main__":
    main()