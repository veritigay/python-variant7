# Лабораторная работа N9. Вариант 7
# Склад. Клиент для работы с TCP-сервером (JSON-протокол)
import socket
import json
import sys

HOST = "127.0.0.1"
PORT = 5000


def send_command(conn, command, data=None):
    message = {"command": command, "data": data or {}}
    raw = (json.dumps(message, ensure_ascii=False) + "\n").encode("utf-8")
    conn.sendall(raw)
    # читаем одну строку-ответ (newline-delimited JSON)
    buffer = ""
    while "\n" not in buffer:
        chunk = conn.recv(1024).decode("utf-8")
        if not chunk:
            break
        buffer += chunk
    return json.loads(buffer.strip())


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((HOST, PORT))
    except ConnectionRefusedError:
        print("Ошибка: сервер недоступен. Запустите server.py")
        sys.exit(1)
    sock.settimeout(5)

    while True:
        print("\n=== SKLAD CLIENT ===")
        print("1. Список позиций")
        print("2. Получить позицию")
        print("3. Добавить позицию")
        print("4. Изменить позицию")
        print("5. Удалить позицию")
        print("6. Проверка остатков")
        print("0. Выход")
        choice = input("Выберите действие: ")

        try:
            if choice == "1":
                response = send_command(sock, "list")
                print(json.dumps(response, ensure_ascii=False, indent=2))
            elif choice == "2":
                item_id = int(input("ID позиции: "))
                response = send_command(sock, "get", {"id": item_id})
                print(json.dumps(response, ensure_ascii=False, indent=2))
            elif choice == "3":
                data = {
                    "name": input("Наименование: "),
                    "category": input("Категория: "),
                    "quantity": int(input("Количество: ")),
                    "min_quantity": int(input("Мин. остаток: ")),
                }
                response = send_command(sock, "create", data)
                print(json.dumps(response, ensure_ascii=False, indent=2))
            elif choice == "4":
                item_id = int(input("ID позиции: "))
                data = {"id": item_id, "quantity": int(input("Новое количество: "))}
                response = send_command(sock, "update", data)
                print(json.dumps(response, ensure_ascii=False, indent=2))
            elif choice == "5":
                item_id = int(input("ID позиции: "))
                response = send_command(sock, "delete", {"id": item_id})
                print(json.dumps(response, ensure_ascii=False, indent=2))
            elif choice == "6":
                response = send_command(sock, "stock_check")
                print(json.dumps(response, ensure_ascii=False, indent=2))
            elif choice == "0":
                break
            else:
                print("Неверный пункт меню")
        except socket.timeout:
            print("Ошибка: тайм-аут ожидания ответа")
        except json.JSONDecodeError:
            print("Ошибка: некорректный ответ сервера")

    sock.close()


if __name__ == "__main__":
    main()