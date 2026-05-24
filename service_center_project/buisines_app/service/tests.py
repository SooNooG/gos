from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Client, Employee, ServiceRequest, UserProfile


class ServiceAppTests(TestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(
            username="client_user",
            password="StrongPass123!",
            email="client@example.com",
        )
        self.client_profile = UserProfile.objects.create(user=self.client_user, role="client")
        self.client_entity = Client.objects.create(
            user=self.client_user,
            name="Client One",
            email="client@example.com",
            phone_number="111",
        )

        self.admin_user = User.objects.create_user(
            username="admin_user",
            password="StrongPass123!",
            email="admin@example.com",
        )
        UserProfile.objects.create(user=self.admin_user, role="admin")

    def test_registration_creates_user_profile_and_client(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "new_user",
                "email": "new_user@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertRedirects(response, reverse("home"))
        user = User.objects.get(username="new_user")
        self.assertEqual(user.userprofile.role, "client")
        self.assertTrue(Client.objects.filter(user=user, email="new_user@example.com").exists())

    def test_login_redirects_to_home(self):
        response = self.client.post(
            reverse("login"),
            {"username": "client_user", "password": "StrongPass123!"},
        )

        self.assertRedirects(response, reverse("home"))

    def test_profile_page_is_available_for_logged_in_user(self):
        ServiceRequest.objects.create(
            title="Чайник",
            description="Не включается",
            client=self.client_entity,
            status="new",
        )
        self.client.force_login(self.client_user)

        response = self.client.get(reverse("profile"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Профиль пользователя")
        self.assertEqual(response.context["role"], "client")
        self.assertEqual(response.context["request_stats"]["total"], 1)

    def test_request_list_supports_search_and_pagination(self):
        for index in range(12):
            ServiceRequest.objects.create(
                title=f"Ноутбук {index}",
                description="Диагностика",
                client=self.client_entity,
                status="new",
            )
        ServiceRequest.objects.create(
            title="Стиральная машина",
            description="Ремонт",
            client=self.client_entity,
            status="completed",
        )

        self.client.force_login(self.client_user)

        response = self.client.get(reverse("request_list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["requests"]), 10)
        self.assertTrue(response.context["page_obj"].has_next())

        response = self.client.get(reverse("request_list"), {"page": 2})
        self.assertEqual(len(response.context["requests"]), 3)

        response = self.client.get(reverse("request_list"), {"q": "машина"})
        self.assertEqual(len(response.context["requests"]), 1)
        self.assertEqual(response.context["requests"][0].title, "Стиральная машина")

    def test_cannot_complete_request_without_employee(self):
        service_request = ServiceRequest.objects.create(
            title="Пылесос",
            description="Не включается",
            client=self.client_entity,
            status="new",
        )
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse("request_update", args=[service_request.pk]),
            {
                "title": service_request.title,
                "description": service_request.description,
                "client": self.client_entity.pk,
                "employee": "",
                "status": "completed",
            },
        )

        self.assertEqual(response.status_code, 200)
        service_request.refresh_from_db()
        self.assertEqual(service_request.status, "new")
        self.assertIsNone(service_request.closed_at)

    def test_admin_can_create_employee_and_role_is_synced(self):
        employee_user = User.objects.create_user(
            username="employee_user",
            password="StrongPass123!",
            email="employee@example.com",
        )
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse("employee_create"),
            {
                "user": employee_user.pk,
                "name": "Employee One",
                "email": "employee@example.com",
                "phone_number": "222",
                "position": "Инженер",
            },
        )

        self.assertRedirects(response, reverse("employee_list"))
        employee = Employee.objects.get(user=employee_user)
        self.assertEqual(employee.position, "Инженер")
        self.assertEqual(employee_user.userprofile.role, "employee")
