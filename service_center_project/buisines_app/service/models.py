from django.contrib.auth.models import User
from django.db import models


class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="client_profile")
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20)

    @property
    def full_name(self):
        return self.name

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"


class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="employee_profile")
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20)
    position = models.CharField(max_length=50)

    @property
    def full_name(self):
        return self.name

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"


class ServiceRequest(models.Model):
    STATUS_CHOICES = [
        ("new", "Новая"),
        ("pending", "Ожидает"),
        ("in_progress", "В процессе"),
        ("completed", "Завершена"),
    ]

    title = models.CharField(max_length=200, verbose_name="Название заявки")
    description = models.TextField(verbose_name="Описание заявки")
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="requests",
        verbose_name="Клиент",
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="requests",
        verbose_name="Сотрудник",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="new",
        verbose_name="Статус заявки",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Service Request #{self.id} for {self.client.name}"

    class Meta:
        verbose_name = "Заявка на обслуживание"
        verbose_name_plural = "Заявки на обслуживание"
        ordering = ["-created_at"]


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ("client", "Клиент"),
        ("employee", "Сотрудник"),
        ("admin", "Администратор"),
    ]

    user = models.OneToOneField("auth.User", on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="client")

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"
