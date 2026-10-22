# Генератор demo/run.txt для консольных работ: запускает main.py с входом
# из input.txt и записывает вывод в UTF-8 (вместе с входом).
import io
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))


def run_lab(num, input_lines, args=None):
    num_dir = os.path.join(ROOT, "{:02d}".format(num))
    py = os.path.join(num_dir, "main.py")
    demo = os.path.join(num_dir, "demo")
    os.makedirs(demo, exist_ok=True)

    input_path = os.path.join(demo, "input.txt")
    with io.open(input_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(input_lines) + "\n")

    p = subprocess.run(
        [sys.executable, py] + (args or []),
        input=("\n".join(input_lines) + "\n").encode("utf-8"),
        capture_output=True,
        cwd=num_dir,
    )
    out = p.stdout.decode("utf-8", errors="replace")
    if p.stderr:
        out += "\n[stderr]\n" + p.stderr.decode("utf-8", errors="replace")
    out += "\n[exit code: {}]".format(p.returncode)

    run_path = os.path.join(demo, "run.txt")
    with io.open(run_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(out)
    print("lab {:02d}: exit {}".format(num, p.returncode))


if __name__ == "__main__":
    # lab 01: анализ результатов соревнований
    run_lab(1, ["3", "12.5", "11.0", "13.2"])

    # lab 02: заказы (меню). Номер, клиент, стоимость, статус; затем 0 выход
    run_lab(2, [
        "1", "A-100", "Иванов", "5000", "оплачен",
        "1", "A-101", "Петрова", "2000", "создан",
        "1", "A-102", "Иванов", "7000", "оплачен",
        "6", "7", "0",
    ])

    # lab 05: банковские счета — выводится сразу, вход не нужен
    run_lab(5, [])

    # lab 06: автосервис (декораторы) — без ввода
    run_lab(6, [])

    # lab 07: автосервис SOLID — без ввода
    run_lab(7, [])

    # lab 08: автосервис паттерны — без ввода
    run_lab(8, [])

    # lab 11: SQL+Redis+CDN — меню, сразу выход (0)
    run_lab(11, ["0"])

    # lab 12: SQLAlchemy фитнес — меню, сразу выход (0)
    run_lab(12, ["0"])

    # lab 19: микросервисы — без ввода
    run_lab(19, [])