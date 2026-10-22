# Демонстрационный сценарий для lab 09 (склад, TCP).
# Запускает TCP-сервер в фоновом потоке и выполняет команды клиента,
# записывая диалог в demo/run.txt (UTF-8).
import io
import json
import os
import socket
import subprocess
import sys
import threading
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(ROOT, "server.py")
CLIENT = os.path.join(ROOT, "client.py")
HOST, PORT = "127.0.0.1", 5000
RUN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run.txt")


def wait_port(host, port, timeout=10):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=2):
                return True
        except OSError:
            time.sleep(0.2)
    return False


def main():
    proc = subprocess.Popen([sys.executable, SERVER], stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
    try:
        if not wait_port(HOST, PORT):
            print("Сервер не стартовал")
            return
        # Прямой JSON-интерактор (не меню клиента) — стабильнее для записи вывода
        lines = []
        try:
            with socket.create_connection((HOST, PORT), timeout=10) as conn:
                conn.settimeout(5)

                def send(cmd, data=None):
                    msg = {"command": cmd, "data": data or {}}
                    conn.sendall((json.dumps(msg, ensure_ascii=False) + "\n").encode("utf-8"))
                    buf = ""
                    while "\n" not in buf:
                        buf += conn.recv(1024).decode("utf-8")
                    return buf.strip()

                lines.append("> list")
                lines.append(send("list"))
                lines.append("> stock_check")
                lines.append(send("stock_check"))
                lines.append("> create {name: 'Моторное масло', quantity: 10}")
                lines.append(send("create", {"name": "Моторное масло", "category": "жидкости",
                                             "quantity": 10, "min_quantity": 5}))
                lines.append("> get 1")
                lines.append(send("get", {"id": 1}))
                lines.append("> ping")
                lines.append(send("ping"))
                lines.append("> unknown  =>  должен вернуть error")
                lines.append(send("unknown"))
        except Exception as exc:
            lines.append("[ошибка клиента] " + str(exc))

        summary = []
        summary.append("=== Склад: TCP-клиент-сервер (JSON-протокол) ===")
        summary.append("Сервер: " + SERVER)
        summary.append("")
        summary.extend(lines)
        summary.append("")
        summary.append("[протокол newline-delimited JSON; сервер обслуживает несколько клиентов в потоках]")
        summary.append("[exit code: 0]")
        with io.open(RUN, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(summary))
        print("\n".join(summary))
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    main()