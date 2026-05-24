from django.contrib.auth import views as auth_views
from django.urls import path

from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("profile/", views.profile, name="profile"),
    path("requests/", views.request_list, name="request_list"),
    path("requests/create/", views.request_create, name="request_create"),
    path("requests/<int:pk>/", views.request_detail, name="request_detail"),
    path("requests/<int:pk>/update/", views.request_update, name="request_update"),
    path("requests/<int:pk>/delete/", views.request_delete, name="request_delete"),
    path("clients/", views.client_list, name="client_list"),
    path("clients/create/", views.client_create, name="client_create"),
    path("clients/<int:pk>/update/", views.client_update, name="client_update"),
    path("clients/<int:pk>/delete/", views.client_delete, name="client_delete"),
    path("employees/", views.employee_list, name="employee_list"),
    path("employees/create/", views.employee_create, name="employee_create"),
    path("employees/<int:pk>/update/", views.employee_update, name="employee_update"),
    path("employees/<int:pk>/delete/", views.employee_delete, name="employee_delete"),
    path("register/", views.register, name="register"),
    path("login/", auth_views.LoginView.as_view(template_name="login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
