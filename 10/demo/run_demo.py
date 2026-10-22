# Демонстрация lab 10 (Flask REST API автосервиса) через тестовый клиент Flask:
# выполняем CRUD и специальные endpoint'ы, сохраняем вывод в demo/run.txt (UTF-8).
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

RUN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run.txt")


def main():
    # Импортируем app из lab10/app.py (переменная app и service)
    import app as server_app
    client = server_app.app.test_client()
    out = []
    out.append("=== Автосервис: Flask REST API ===")

    def log(title, resp):
        out.append("")
        out.append(title)
        out.append("HTTP " + str(resp.status_code))
        out.append(resp.get_data(as_text=True).strip())

    # GET все автомобили
    r = client.get("/cars")
    log("GET /cars (список)", r)

    # GET автомобиль в ремонте (спец. операция)
    r = client.get("/cars/in-repair")
    log("GET /cars/in-repair", r)

    # POST создать авто
    r = client.post("/cars", json={
        "brand": "Skoda", "model": "Octavia", "year": 2021,
        "owner": "Новиков", "mileage": 25000, "category": "sedan",
        "condition": "good",
    })
    new_id = r.get_json().get("id") if r.status_code == 201 else None
    log("POST /cars (создание)", r)

    # PATCH изменить пробег
    if new_id:
        r = client.patch(f"/cars/{new_id}", json={"mileage": 30000})
        log(f"PATCH /cars/{new_id} (пробег)", r)

    # DELETE первого авто
    r = client.delete("/cars/1")
    out.append("")
    out.append("DELETE /cars/1")
    out.append("HTTP " + str(r.status_code))

    # GET статистика
    r = client.get("/cars/statistics")
    log("GET /cars/statistics", r)

    # 404
    r = client.get("/cars/9999")
    log("GET /cars/9999 (404)", r)

    out.append("")
    out.append("[exit code: 0]")
    with io.open(RUN, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out))
    print("\n".join(out))


if __name__ == "__main__":
    main()