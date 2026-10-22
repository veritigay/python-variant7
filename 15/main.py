# Лабораторная работа N15. Вариант 7
# Фитнес-клуб. Веб-приложение на Flask + SQLAlchemy + шаблоны Jinja2 + REST API.
#
# Сущности (вариант 7): Client, Trainer, Training
# Реализовано: HTML-интерфейс, REST API, CRUD, поиск, фильтрация, сортировка.
#
# Запуск: pip install flask flask-sqlalchemy; python main.py
# Откройте http://127.0.0.1:5000

import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy

BASE = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE, "fitness.db")
app.config["SECRET_KEY"] = "change-me"
db = SQLAlchemy(app)


# ---------- Models ----------
class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    phone = db.Column(db.String(50), nullable=False, unique=True)
    subscription_expire = db.Column(db.String(10), nullable=False)
    trainings = db.relationship("Training", backref="client", lazy=True)


class Trainer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    specialty = db.Column(db.String(100), nullable=False)
    trainings = db.relationship("Training", backref="trainer", lazy=True)


class Training(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=False)
    trainer_id = db.Column(db.Integer, db.ForeignKey("trainer.id"), nullable=False)
    date = db.Column(db.String(10), nullable=False)
    duration = db.Column(db.Integer, nullable=False)


# ---------- Repository ----------
class GymRepository:
    def __init__(self, db_session):
        self.db = db_session

    def get_clients(self, search=None, min_age=None, specialty=None, sort=None):
        query = Client.query
        if search:
            query = query.filter(Client.name.contains(search))
        if min_age:
            query = query.filter(Client.age >= int(min_age))
        if sort == "age":
            query = query.order_by(Client.age)
        elif sort == "name":
            query = query.order_by(Client.name)
        return query.all()

    def get_client(self, client_id):
        return self.db.get(Client, client_id)

    def create_client(self, name, age, phone, expire):
        client = Client(name=name, age=age, phone=phone, subscription_expire=expire)
        self.db.add(client)
        self.db.commit()
        return client

    def update_client(self, client, **fields):
        for key, value in fields.items():
            if hasattr(client, key):
                setattr(client, key, value)
        self.db.commit()
        return client

    def delete_client(self, client):
        for t in client.trainings:
            self.db.delete(t)
        self.db.delete(client)
        self.db.commit()

    def get_trainers(self):
        return Trainer.query.all()

    def create_training(self, client, trainer, date, duration):
        training = Training(client_id=client.id, trainer_id=trainer.id,
                            date=date, duration=duration)
        self.db.add(training)
        self.db.commit()
        return training


# ---------- Service ----------
class GymService:
    def __init__(self, repository):
        self.repository = repository

    def list_clients(self, **filters):
        return self.repository.get_clients(**filters)

    def get_client(self, client_id):
        client = self.repository.get_client(client_id)
        if not client:
            return None
        return client

    def create_client(self, data):
        expire = data.get("expire") or data.get("subscription_expire")
        return self.repository.create_client(
            data["name"], int(data["age"]), data["phone"], expire
        )

    def update_client(self, client, data):
        expire = data.get("expire") or data.get("subscription_expire")
        return self.repository.update_client(
            client,
            name=data.get("name", client.name),
            age=int(data.get("age", client.age)),
            phone=data.get("phone", client.phone),
            subscription_expire=expire or client.subscription_expire,
        )

    def delete_client(self, client):
        self.repository.delete_client(client)

    def book_training(self, client_id, trainer_id, date, duration):
        client = self.repository.get_client(client_id)
        if not client:
            return None, "Клиент не найден"
        if client.subscription_expire < date:
            return None, f"Абонемент истёк: {client.subscription_expire}"
        trainer = next((t for t in self.repository.get_trainers()
                        if t.id == trainer_id), None)
        if not trainer:
            return None, "Тренер не найден"
        training = self.repository.create_training(
            client, trainer, date, int(duration)
        )
        return training, None

    def statistics(self):
        clients = self.repository.get_clients()
        trainings_count = Training.query.count()
        avg_age = sum(c.age for c in clients) / len(clients) if clients else 0
        return {
            "clients_count": len(clients),
            "trainings_count": trainings_count,
            "average_age": round(avg_age, 1) if clients else 0,
            "trainers_count": len(self.repository.get_trainers()),
        }


# ---------- Инициализация ----------
with app.app_context():
    db.create_all()
    if not Trainer.query.first():
        db.session.add_all([
            Trainer(name="Тренер А", specialty="силовые"),
            Trainer(name="Тренер Б", specialty="кардио"),
            Trainer(name="Тренер В", specialty="йога"),
        ])
        db.session.commit()

repository = GymRepository(db.session)
service = GymService(repository)


# ---------- Web routes (HTML + Jinja2) ----------
@app.get("/")
def index():
    stats = service.statistics()
    return render_template("index.html", stats=stats)


@app.get("/clients")
def list_clients():
    search = request.args.get("search")
    min_age = request.args.get("min_age")
    sort = request.args.get("sort")
    clients = service.list_clients(search=search, min_age=min_age, sort=sort)
    return render_template("clients.html", clients=clients)


@app.get("/clients/<int:client_id>")
def detail_client(client_id):
    client = service.get_client(client_id)
    if not client:
        return render_template("404.html"), 404
    return render_template("client_detail.html", client=client)


@app.route("/clients/create", methods=["GET", "POST"])
def create_client():
    if request.method == "POST":
        service.create_client(request.form)
        return redirect(url_for("list_clients"))
    return render_template("client_form.html", client=None)


@app.route("/clients/<int:client_id>/edit", methods=["GET", "POST"])
def edit_client(client_id):
    client = service.get_client(client_id)
    if not client:
        return render_template("404.html"), 404
    if request.method == "POST":
        service.update_client(client, request.form)
        return redirect(url_for("detail_client", client_id=client.id))
    return render_template("client_form.html", client=client)


@app.post("/clients/<int:client_id>/delete")
def delete_client(client_id):
    client = service.get_client(client_id)
    if client:
        service.delete_client(client)
    return redirect(url_for("list_clients"))


@app.route("/trainings/book", methods=["GET", "POST"])
def book_training():
    if request.method == "POST":
        training, error = service.book_training(
            int(request.form["client_id"]),
            int(request.form["trainer_id"]),
            request.form["date"],
            request.form["duration"],
        )
        if error:
            return render_template("training_form.html",
                                   trainers=repository.get_trainers(),
                                   clients=repository.get_clients(), error=error), 400
        return redirect(url_for("detail_client", client_id=training.client_id))
    return render_template("training_form.html",
                           trainers=repository.get_trainers(),
                           clients=repository.get_clients(), error=None)


@app.get("/statistics")
def statistics():
    return render_template("statistics.html", stats=service.statistics())


@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404


# ---------- REST API ----------
@app.get("/api/clients")
def api_list_clients():
    clients = service.list_clients()
    return jsonify([
        {"id": c.id, "name": c.name, "age": c.age, "phone": c.phone,
         "subscription_expire": c.subscription_expire}
        for c in clients
    ])


@app.get("/api/clients/<int:client_id>")
def api_get_client(client_id):
    client = service.get_client(client_id)
    if not client:
        return jsonify({"error": "Client not found"}), 404
    return jsonify({"id": client.id, "name": client.name, "age": client.age,
                    "phone": client.phone, "subscription_expire": client.subscription_expire})


@app.post("/api/clients")
def api_create_client():
    data = request.get_json(silent=True) or {}
    if not data.get("name"):
        return jsonify({"error": "Name required"}), 400
    client = service.create_client(data)
    return jsonify({"id": client.id}), 201


@app.put("/api/clients/<int:client_id>")
def api_update_client(client_id):
    client = service.get_client(client_id)
    if not client:
        return jsonify({"error": "Client not found"}), 404
    data = request.get_json(silent=True) or {}
    client = service.update_client(client, data)
    return jsonify({"id": client.id, "name": client.name})


@app.delete("/api/clients/<int:client_id>")
def api_delete_client(client_id):
    client = service.get_client(client_id)
    if not client:
        return jsonify({"error": "Client not found"}), 404
    service.delete_client(client)
    return "", 204


if __name__ == "__main__":
    app.run(port=5000, debug=True)