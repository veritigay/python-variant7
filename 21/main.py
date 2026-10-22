# Лабораторная работа N21. Вариант 7
# Итоговый проект. Фитнес-клуб.
#
# Законченная система: FastAPI + SQLAlchemy + PostgreSQL + Pydantic +
# pytest + Docker + Docker Compose + CI/CD.
#
# Сущности (вариант 7): Client, Trainer, Training (+ Subscription).
# Реализовано: REST API, CRUD, валидация, бизнес-правила, обработка ошибок,
# авторизация (JWT), статистика, health check.
#
# Для компактного отчёта функциональное ядро представлено ниже; полный
# проект разбивается на app/{api,models,schemas,services,repositories}.

from typing import Optional, List
from pydantic import BaseModel, Field, validator
from fastapi import FastAPI, HTTPException, Depends

app = FastAPI(title="Фитнес-клуб - итоговый проект", version="1.0")


# ================= Schemas (Pydantic) =================
class ClientCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    age: int = Field(ge=14, le=100)
    phone: str = Field(min_length=6)
    subscription_expire: str

    @validator("subscription_expire")
    def date_format(cls, value):
        # простая проверка формата ГГГГ-ММ-ДД
        parts = value.split("-")
        if len(parts) != 3 or not all(len(p) in (4, 2, 2) for p in parts):
            raise ValueError("Дата должна быть в формате ГГГГ-ММ-ДД")
        return value


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = Field(default=None, ge=14, le=100)
    phone: Optional[str] = None
    subscription_expire: Optional[str] = None


class ClientResponse(BaseModel):
    id: int
    name: str
    age: int
    phone: str
    subscription_expire: str


class TrainCreate(BaseModel):
    client_id: int
    trainer_id: int
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    duration: int = Field(ge=15, le=240)


class TrainResponse(BaseModel):
    id: int
    client_id: int
    trainer_id: int
    date: str
    duration: int


# ================= Entity =================
class Client:
    def __init__(self, client_id, name, age, phone, subscription_expire):
        self.id = client_id
        self.name = name
        self.age = age
        self.phone = phone
        self.subscription_expire = subscription_expire


class Training:
    def __init__(self, training_id, client_id, trainer_id, date, duration):
        self.id = training_id
        self.client_id = client_id
        self.trainer_id = trainer_id
        self.date = date
        self.duration = duration


# ================= Repository =================
class GymRepository:
    """Хранение в памяти (в полном проекте - SQLAlchemy/PostgreSQL)."""
    def __init__(self):
        self._clients: dict[int, Client] = {}
        self._trainings: dict[int, Training] = {}
        self._next_client = 1
        self._next_training = 1

    # --- Clients ---
    def add_client(self, client):
        client.id = self._next_client
        self._next_client += 1
        self._clients[client.id] = client
        return client

    def get_client(self, client_id):
        return self._clients.get(client_id)

    def all_clients(self):
        return list(self._clients.values())

    def update_client(self, client):
        self._clients[client.id] = client
        return client

    def delete_client(self, client_id):
        # удаляем связанные тренировки
        self._trainings = {k: v for k, v in self._trainings.items()
                           if v.client_id != client_id}
        return self._clients.pop(client_id, None)

    # --- Trainings ---
    def add_training(self, training):
        training.id = self._next_training
        self._next_training += 1
        self._trainings[training.id] = training
        return training

    def get_training(self, training_id):
        return self._trainings.get(training_id)

    def all_trainings(self):
        return list(self._trainings.values())


# ================= Service (бизнес-логика) =================
class GymService:
    def __init__(self, repository):
        self.repository = repository

    def create_client(self, data: ClientCreate):
        client = Client(0, data.name, data.age, data.phone,
                        data.subscription_expire)
        return self.repository.add_client(client)

    def get_client(self, client_id):
        client = self.repository.get_client(client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        return client

    def list_clients(self, min_age=None, name=None):
        clients = self.repository.all_clients()
        if min_age:
            clients = [c for c in clients if c.age >= min_age]
        if name:
            clients = [c for c in clients if name.lower() in c.name.lower()]
        return clients

    def update_client(self, client_id, data: ClientUpdate):
        existing = self.get_client(client_id)
        if data.name is not None:
            existing.name = data.name
        if data.age is not None:
            existing.age = data.age
        if data.phone is not None:
            existing.phone = data.phone
        if data.subscription_expire is not None:
            existing.subscription_expire = data.subscription_expire
        return self.repository.update_client(existing)

    def delete_client(self, client_id):
        self.get_client(client_id)
        self.repository.delete_client(client_id)

    def book_training(self, data: TrainCreate):
        """Бизнес-правило: абонемент должен быть действителен на дату занятия."""
        client = self.get_client(data.client_id)
        # Бизнес-правило 1: проверка действительности абонемента
        if client.subscription_expire < data.date:
            raise HTTPException(status_code=409,
                                detail="Абонемент истёк до даты занятия")
        # Бизнес-правило 2: тренер должен существовать (в полной версии)
        # Здесь тренеры заданы наборами 1..3
        if data.trainer_id not in (1, 2, 3):
            raise HTTPException(status_code=404, detail="Trainer not found")
        # Бизнес-правило 3: нет двух занятий клиента в один день
        for t in self.repository.all_trainings():
            if t.client_id == data.client_id and t.date == data.date:
                raise HTTPException(status_code=409,
                                    detail="У клиента уже есть занятие в этот день")
        training = Training(0, data.client_id, data.trainer_id,
                            data.date, data.duration)
        return self.repository.add_training(training)

    def client_trainings(self, client_id):
        return [t for t in self.repository.all_trainings()
                if t.client_id == client_id]

    def statistics(self):
        clients = self.repository.all_clients()
        trainings = self.repository.all_trainings()
        return {
            "clients_count": len(clients),
            "trainings_count": len(trainings),
            "average_age": round(sum(c.age for c in clients) / len(clients), 1)
                          if clients else 0,
            "active_subscriptions": sum(
                1 for c in clients if c.subscription_expire >= "2026-01-01"),
        }


# ================= Инициализация + DI =================
repository = GymRepository()
service = GymService(repository)


def get_service() -> GymService:
    return service


# Демо-данные
service.create_client(ClientCreate(name="Иван Петров", age=25,
                                   phone="990001",
                                   subscription_expire="2026-12-31"))
service.create_client(ClientCreate(name="Анна Сидорова", age=31,
                                   phone="990002",
                                   subscription_expire="2025-01-15"))
service.create_client(ClientCreate(name="Пётр Кузнецов", age=19,
                                   phone="990003",
                                   subscription_expire="2026-06-01"))
service.book_training(TrainCreate(client_id=1, trainer_id=1,
                                  date="2026-10-25", duration=60))


# ================= REST endpoints =================
@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/clients", response_model=ClientResponse, status_code=201)
def api_create_client(data: ClientCreate, svc: GymService = Depends(get_service)):
    return svc.create_client(data)


@app.get("/clients", response_model=List[ClientResponse])
def api_list_clients(min_age: Optional[int] = None, name: Optional[str] = None,
                     svc: GymService = Depends(get_service)):
    return svc.list_clients(min_age, name)


@app.get("/clients/{client_id}", response_model=ClientResponse)
def api_get_client(client_id: int, svc: GymService = Depends(get_service)):
    return svc.get_client(client_id)


@app.put("/clients/{client_id}", response_model=ClientResponse)
def api_update_client(client_id: int, data: ClientUpdate,
                      svc: GymService = Depends(get_service)):
    return svc.update_client(client_id, data)


@app.delete("/clients/{client_id}", status_code=204)
def api_delete_client(client_id: int, svc: GymService = Depends(get_service)):
    svc.delete_client(client_id)


@app.post("/trainings", response_model=TrainResponse, status_code=201)
def api_book_training(data: TrainCreate, svc: GymService = Depends(get_service)):
    return svc.book_training(data)


@app.get("/clients/{client_id}/trainings", response_model=List[TrainResponse])
def api_client_trainings(client_id: int, svc: GymService = Depends(get_service)):
    return svc.client_trainings(client_id)


@app.get("/statistics")
def api_statistics(svc: GymService = Depends(get_service)):
    return svc.statistics()


# ================= Тесты (pytest, из ЛР 18) =================
def test_business_rule_expired_subscription():
    """Бизнес-правило: просроченный абонемент блокирует запись."""
    repo = GymRepository()
    svc = GymService(repo)
    svc.create_client(ClientCreate(name="Анна", age=31, phone="990002",
                                   subscription_expire="2025-01-15"))
    try:
        svc.book_training(TrainCreate(client_id=1, trainer_id=1,
                                      date="2026-10-25", duration=60))
        assert False, "Должно было выбросить исключение"
    except HTTPException as error:
        assert error.status_code == 409


def test_business_rule_duplicate_day():
    """Бизнес-правило: нельзя записать клиента на занятие в тот же день."""
    repo = GymRepository()
    svc = GymService(repo)
    svc.create_client(ClientCreate(name="Иван", age=25, phone="990001",
                                   subscription_expire="2026-12-31"))
    svc.book_training(TrainCreate(client_id=1, trainer_id=1,
                                  date="2026-10-25", duration=60))
    try:
        svc.book_training(TrainCreate(client_id=1, trainer_id=2,
                                      date="2026-10-25", duration=45))
        assert False
    except HTTPException as error:
        assert error.status_code == 409


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)