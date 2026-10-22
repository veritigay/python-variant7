# Демонстрация lab 14 (FastAPI REST API автосервиса) через TestClient:
# CRUD, фильтрация, статистика, асинхронный поиск. Вывод в demo/run.txt (UTF-8).
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

RUN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run.txt")


def main():
    from fastapi.testclient import TestClient
    import main as server_app
    client = TestClient(server_app.app)
    out = []
    out.append("=== Автосервис: FastAPI REST API ===")

    def log(title, r):
        out.append("")
        out.append(title)
        out.append("HTTP " + str(r.status_code))
        out.append(r.text)

    r = client.get("/cars")
    log("GET /cars?limit=10 (список, пагинация)", r)

    r = client.get("/cars?category=sedan&sort=mileage")
    log("GET /cars?category=sedan&sort=mileage (фильтр+сортировка)", r)

    r = client.post("/cars", json={
        "brand": "Skoda", "model": "Octavia", "year": 2021, "owner": "Новиков",
        "mileage": 25000, "category": "sedan", "condition": "good",
    })
    new_id = r.json().get("id") if r.status_code == 201 else None
    log("POST /cars (создание, 201)", r)

    if new_id:
        r = client.patch(f"/cars/{new_id}", json={"mileage": 30000})
        log(f"PATCH /cars/{new_id} (частичное изменение)", r)
        r = client.delete(f"/cars/{new_id}")
        out.append("")
        out.append(f"DELETE /cars/{new_id}")
        out.append("HTTP " + str(r.status_code))

    r = client.get("/cars/in-repair")
    log("GET /cars/in-repair (автомобили в ремонте)", r)

    r = client.get("/cars/statistics")
    log("GET /cars/statistics", r)

    r = client.get("/cars/search/toyota")
    log("GET /cars/search/toyota (асинхронный поиск)", r)

    r = client.get("/cars/9999")
    log("GET /cars/9999 (404)", r)

    r = client.get("/health")
    log("GET /health", r)

    out.append("")
    out.append("[exit code: 0]")
    with io.open(RUN, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out))
    print("\n".join(out))


if __name__ == "__main__":
    main()