# Лабораторная работа N9. Вариант 7
# Склад. Клиент-серверное приложение (TCP, JSON-протокол, несколько клиентов)
#
# Файлы проекта:
#   models.py     - сущность Item (складская позиция)
#   repository.py - хранение в памяти
#   service.py    - бизнес-логика (проверка остатков)
#   protocol.py   - сериализация сообщений (newline-delimited JSON)
#   server.py     - TCP-сервер (многопоточный)
#   client.py     - TCP-клиент (меню)
#   exceptions.py - ProtocolError и др.
#
# Запуск: python server.py  и  python client.py

import json
import socket
import threading
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("warehouse")


# ============ exceptions.py ============
class ProtocolError(Exception):
    pass


class ItemNotFoundError(Exception):
    pass


# ============ models.py ============
class Item:
    """Складская позиция: id, наименование, категория, количество, min остаток."""
    def __init__(self, item_id, name, category, quantity, min_quantity):
        self.id = item_id
        self.name = name
        self.category = category
        self.quantity = quantity
        self.min_quantity = min_quantity

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "quantity": self.quantity,
            "min_quantity": self.min_quantity,
            "low_stock": self.quantity < self.min_quantity,
        }


# ============ repository.py ============
class Repository:
    def __init__(self):
        self._items = {}
        self._next_id = 1

    def add(self, name, category, quantity, min_quantity):
        item = Item(self._next_id, name, category, quantity, min_quantity)
        self._items[item.id] = item
        self._next_id += 1
        return item

    def get(self, item_id):
        return self._items.get(item_id)

    def get_all(self):
        return list(self._items.values())

    def update(self, item_id, data):
        item = self._items.get(item_id)
        if not item:
            raise ItemNotFoundError(f"Позиция {item_id} не найдена")
        for key, value in data.items():
            if hasattr(item, key) and key != "id":
                setattr(item, key, value)
        return item

    def delete(self, item_id):
        if item_id not in self._items:
            raise ItemNotFoundError(f"Позиция {item_id} не найдена")
        del self._items[item_id]


# ============ service.py ============
class Service:
    def __init__(self, repository):
        self.repository = repository

    def list_items(self):
        return [i.to_dict() for i in self.repository.get_all()]

    def get_item(self, item_id):
        item = self.repository.get(item_id)
        if not item:
            raise ItemNotFoundError(f"Позиция {item_id} не найдена")
        return item.to_dict()

    def create_item(self, data):
        name = data.get("name", "").strip()
        category = data.get("category", "").strip()
        quantity = int(data.get("quantity", 0))
        min_quantity = int(data.get("min_quantity", 0))
        if not name:
            raise ValueError("Наименование не может быть пустым")
        if quantity < 0 or min_quantity < 0:
            raise ValueError("Остатки не могут быть отрицательными")
        item = self.repository.add(name, category, quantity, min_quantity)
        return item.to_dict()

    def update_item(self, item_id, data):
        clean = {k: v for k, v in data.items()
                 if k in ("name", "category", "quantity", "min_quantity")}
        item = self.repository.update(item_id, clean)
        return item.to_dict()

    def delete_item(self, item_id):
        self.repository.delete(item_id)
        return {"deleted": item_id}

    def stock_check(self):  # специализированная команда
        """Проверка остатков: позиции с низким остатком."""
        low = [i.to_dict() for i in self.repository.get_all()
               if i.quantity < i.min_quantity]
        total = sum(i.quantity for i in self.repository.get_all())
        return {"low_stock_items": low, "total_quantity": total}


# ============ protocol.py ============
def encode(message) -> bytes:
    return (json.dumps(message, ensure_ascii=False) + "\n").encode("utf-8")


def decode(data: bytes):
    try:
        return json.loads(data.decode("utf-8").strip())
    except json.JSONDecodeError:
        raise ProtocolError("Некорректный JSON")


# ============ server.py ============
HOST = "127.0.0.1"
PORT = 5000


def handle_command(service, message):
    command = message.get("command")
    data = message.get("data", {})
    try:
        if command == "list":
            result = service.list_items()
            return {"status": "ok", "data": result}
        elif command == "get":
            result = service.get_item(int(data["id"]))
            return {"status": "ok", "data": result}
        elif command == "create":
            result = service.create_item(data)
            return {"status": "ok", "data": result}
        elif command == "update":
            result = service.update_item(int(data["id"]), data)
            return {"status": "ok", "data": result}
        elif command == "delete":
            result = service.delete_item(int(data["id"]))
            return {"status": "ok", "data": result}
        elif command == "stock_check":
            result = service.stock_check()
            return {"status": "ok", "data": result}
        elif command == "ping":
            return {"status": "ok", "data": {"message": "pong"}}
        else:
            return {"status": "error", "error": f"Неизвестная команда: {command}"}
    except ItemNotFoundError as e:
        return {"status": "error", "error": str(e)}
    except (ValueError, KeyError, ProtocolError) as e:
        return {"status": "error", "error": str(e)}
    except Exception as e:
        return {"status": "error", "error": f"Внутренняя ошибка: {e}"}


def handle_client(conn, addr, service):
    logger.info("Client connected: %s:%s", addr[0], addr[1])
    conn.settimeout(5)
    try:
        buffer = ""
        while True:
            data = conn.recv(1024)
            if not data:
                break
            buffer += data.decode("utf-8")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if not line.strip():
                    continue
                try:
                    message = decode(line.encode())
                except ProtocolError as e:
                    response = {"status": "error", "error": str(e)}
                else:
                    logger.info("Command: %s", message.get("command"))
                    response = handle_command(service, message)
                conn.sendall(encode(response))
    except socket.timeout:
        logger.info("Client %s timeout", addr)
    except ConnectionResetError:
        logger.info("Client %s reset connection", addr)
    finally:
        conn.close()
        logger.info("Client disconnected: %s:%s", addr[0], addr[1])


def run_server():
    service = Service(Repository())
    # демо-данные
    for name, cat, q, m in [
        ("Масло моторное", "смазка", 120, 50),
        ("Фильтр воздушный", "фильтры", 5, 20),
        ("Тормозные колодки", "тормоза", 40, 15),
        ("Свечи зажигания", "электроника", 8, 25),
        ("Антифриз", "жидкости", 60, 30),
    ]:
        service.create_item({"name": name, "category": cat,
                             "quantity": q, "min_quantity": m})

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    logger.info("Server started at %s:%s", HOST, PORT)

    executor = threading.Thread
    while True:
        conn, addr = server.accept()
        t = threading.Thread(target=handle_client, args=(conn, addr, service),
                             daemon=True)
        t.start()


if __name__ == "__main__":
    run_server()