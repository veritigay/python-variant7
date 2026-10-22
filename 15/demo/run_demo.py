# Демонстрация lab 15 (Flask + Jinja2 фитнес-клуб) через тестовый клиент Flask.
# Проверяем web-страницы и REST API, вывод сохраняем в demo/run.txt (UTF-8).
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

RUN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run.txt")


def main():
    import main as app_module
    app = app_module.app
    client = app.test_client()
    out = []
    out.append("=== Фитнес-клуб: Flask веб-приложение ===")

    def log(title, r, show_html=False):
        out.append("")
        out.append(title)
        out.append("HTTP " + str(r.status_code))
        text = r.get_data(as_text=True).strip()
        if show_html and text:
            # обрезаем HTML до видимой строки заголовка
            import re
            m = re.search(r"<h1[^>]*>(.*?)</h1>", text)
            out.append("HTML: " + (m.group(1) if m else text[:120]))
        elif text:
            out.append(text[:400])

    # web-страницы
    log("GET / (главная)", client.get("/"), show_html=True)
    log("GET /clients (список)", client.get("/clients"), show_html=True)
    log("GET /clients?search=Иван (поиск)", client.get("/clients?search=Иван"), show_html=True)
    log("GET /statistics (статистика)", client.get("/statistics"), show_html=True)
    log("GET /clients/1 (детальная)", client.get("/clients/1"), show_html=True)
    log("GET /clients/999 (404)", client.get("/clients/999"), show_html=True)

    # REST API
    log("GET /api/clients", client.get("/api/clients"))
    r = client.post("/api/clients", json={"name": "Новиков", "age": 28,
                                          "phone": "990007",
                                          "subscription_expire": "2026-12-31"})
    log("POST /api/clients (создание)", r)
    log("GET /api/clients/7", client.get("/api/clients/7"))
    r = client.put("/api/clients/7", json={"name": "Новиков", "age": 29,
                                           "phone": "990007",
                                           "subscription_expire": "2026-12-31"})
    log("PUT /api/clients/7 (изменение)", r)
    r = client.delete("/api/clients/7")
    out.append("")
    out.append("DELETE /api/clients/7")
    out.append("HTTP " + str(r.status_code))

    # запись на тренировку (бизнес-правило: абонемент)
    log("GET /trainings/book (форма)", client.get("/trainings/book"), show_html=True)

    out.append("")
    out.append("[exit code: 0]")
    with io.open(RUN, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out))
    print("\n".join(out))


if __name__ == "__main__":
    main()