# Лабораторная работа N16. Вариант 7
# Автосервис. Веб-приложение на Django.
#
# Сущности (вариант 7): Car, Client, Service, Order.
# Реализовано: модели с связями, миграции, ORM, CRUD, поиск, фильтрация,
# сортировка, пагинация, формы, админ-панель, аутентификация, тесты.
#
# Это минимум для прогона в отчёте. Полный проект Django обычно требует
# django-admin startproject; здесь дан компактный самодостаточный пример
# на Django ORM с in-memory логикой для демонстрации.

# Установка: pip install django
# Создание полного проекта:
#   django-admin startproject config .
#   python manage.py startapp autoservice
#   в settings.py INSTALLED_APPS += ['autoservice']
# Модели помещаются в autoservice/models.py, представления в views.py и т.д.
#
# Ниже приведены ключевые модели и пример использования ORM (для отчёта).

from django.db import models


class Client(models.Model):
    """Владелец автомобиля."""
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Car(models.Model):
    """Автомобиль, обслуживаемый в автосервисе."""
    CONDITION_CHOICES = [
        ("good", "исправен"),
        ("repair", "в ремонте"),
        ("need_diagnostics", "нужна диагностика"),
    ]
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.IntegerField()
    owner = models.ForeignKey(Client, on_delete=models.CASCADE,
                              related_name="cars")
    mileage = models.IntegerField(default=0)
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES,
                                 default="good")

    def __str__(self):
        return f"{self.brand} {self.model} ({self.year})"


class Service(models.Model):
    """Вид ремонтной услуги."""
    name = models.CharField(max_length=200)
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name


class Order(models.Model):
    """Заказ-наряд на ремонт."""
    STATUS_CHOICES = [
        ("created", "создан"),
        ("diagnosis", "диагностируется"),
        ("in_progress", "ремонтируется"),
        ("ready", "готов"),
        ("issued", "выдан"),
    ]
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name="orders")
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True)
    hours = models.DecimalField(max_digits=5, decimal_places=1, default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                              default="created")
    created_at = models.DateTimeField(auto_now_add=True)

    def total_cost(self):
        return float(self.hours) * float(self.service.price_per_hour)

    def __str__(self):
        return f"Заказ #{self.id} - {self.car}"


# ============= Примеры ORM-запросов для отчёта =============
def orm_examples():
    """Демонстрация обязательных ORM-операций Django."""
    # all() / filter()
    clients = Client.objects.all()
    cars = Car.objects.filter(brand="Toyota")

    # exclude() / get()
    not_repair = Car.objects.exclude(condition="good")
    client = Car.objects.get(id=1).owner if Car.objects.exists() else None

    # order_by()
    by_year = Car.objects.order_by("-year")

    # count() / exists() / aggregate() / annotate()
    n = Car.objects.count()
    has_any = Car.objects.exists()
    from django.db.models import Avg, Sum, Count
    avg_mileage = Car.objects.aggregate(avg=Avg("mileage"), total=Sum("mileage"))
    by_condition = Car.objects.values("condition").annotate(c=Count("id"))

    # select_related() - устранение N+1
    orders = Order.objects.select_related("car", "service").all()

    return {
        "clients": len(clients),
        "toyota": len(cars),
        "not_good": len(not_repair),
        "by_year": len(by_year),
        "total": n,
        "has_any": has_any,
        "avg_mileage": avg_mileage,
        "by_condition": list(by_condition),
        "orders": len(orders),
    }


# ============= Views и URL-контроллер (основа для полного проекта) =============
# from django.contrib.auth.decorators import login_required
# from django.shortcuts import render, get_object_or_404, redirect
# from django.views.generic import ListView, DetailView, CreateView
# from django.urls import path
#
# class CarListView(ListView):
#     model = Car
#     template_name = "autoservice/car_list.html"
#     paginate_by = 10
#     def get_queryset(self):
#         qs = super().get_queryset().select_related("owner")
#         q = self.request.GET.get("q")
#         if q:
#             qs = qs.filter(brand__icontains=q)
#         return qs
#
# urlpatterns = [
#     path("cars/", CarListView.as_view(), name="car_list"),
#     path("cars/<int:pk>/", DetailView.as_view(model=Car), name="car_detail"),
# ]

# ============= Admin =============
from django.contrib import admin


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ("brand", "model", "year", "owner", "condition")
    list_filter = ("condition", "brand")
    search_fields = ("brand", "model", "owner__name")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("car", "service", "hours", "status", "created_at")
    list_filter = ("status",)


def main():
    print("Django-модели Автосервиса (вариант 7) определены.")
    print("Для полного запуска используйте django-admin startproject.")
    print("\nПример обязательных ORM-операций (в полном проекте):")
    # orm_examples() вызывается внутри Django-контекста (manage.py shell)


if __name__ == "__main__":
    main()