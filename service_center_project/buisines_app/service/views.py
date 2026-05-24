from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import ClientForm, EmployeeForm, RegisterForm, ServiceRequestForm
from .models import Client, Employee, ServiceRequest, UserProfile


def get_user_role(user):
    if getattr(user, "is_superuser", False):
        return "admin"
    try:
        return user.userprofile.role
    except UserProfile.DoesNotExist:
        return None


def require_admin(request):
    if get_user_role(request.user) != "admin":
        return HttpResponseForbidden("Недостаточно прав.")
    return None


def get_request_for_user_or_403(request, pk):
    service_request = get_object_or_404(
        ServiceRequest.objects.select_related("client__user", "employee__user"),
        pk=pk,
    )
    role = get_user_role(request.user)

    if role == "client" and service_request.client.user_id != request.user.id:
        return None, HttpResponseForbidden("У вас нет доступа к этой заявке.")

    return service_request, None


def apply_request_business_rules(service_request):
    if service_request.status == "completed":
        if service_request.employee is None:
            return False
        if service_request.closed_at is None:
            service_request.closed_at = timezone.now()
    else:
        service_request.closed_at = None
    return True


@login_required
def home(request):
    total_requests = ServiceRequest.objects.count()
    new_requests = ServiceRequest.objects.filter(status="new").count()
    in_progress_requests = ServiceRequest.objects.filter(status="in_progress").count()
    done_requests = ServiceRequest.objects.filter(status="completed").count()

    context = {
        "total_requests": total_requests,
        "new_requests": new_requests,
        "in_progress_requests": in_progress_requests,
        "done_requests": done_requests,
    }
    return render(request, "home.html", context)


@login_required
def profile(request):
    role = get_user_role(request.user)
    client_profile = None
    employee_profile = None
    request_stats = {"total": 0, "new": 0, "in_progress": 0, "completed": 0}

    if role == "client":
        client_profile = getattr(request.user, "client_profile", None)
        if client_profile:
            queryset = ServiceRequest.objects.filter(client=client_profile)
            request_stats = {
                "total": queryset.count(),
                "new": queryset.filter(status="new").count(),
                "in_progress": queryset.filter(status="in_progress").count(),
                "completed": queryset.filter(status="completed").count(),
            }
    elif role == "employee":
        employee_profile = getattr(request.user, "employee_profile", None)
        if employee_profile:
            queryset = ServiceRequest.objects.filter(employee=employee_profile)
            request_stats = {
                "total": queryset.count(),
                "new": queryset.filter(status="new").count(),
                "in_progress": queryset.filter(status="in_progress").count(),
                "completed": queryset.filter(status="completed").count(),
            }
    elif role == "admin":
        queryset = ServiceRequest.objects.all()
        request_stats = {
            "total": queryset.count(),
            "new": queryset.filter(status="new").count(),
            "in_progress": queryset.filter(status="in_progress").count(),
            "completed": queryset.filter(status="completed").count(),
        }

    return render(
        request,
        "profile.html",
        {
            "role": role,
            "client_profile": client_profile,
            "employee_profile": employee_profile,
            "request_stats": request_stats,
        },
    )


@login_required
def request_list(request):
    status = request.GET.get("status", "").strip()
    query = request.GET.get("q", "").strip()
    role = get_user_role(request.user)

    requests = ServiceRequest.objects.select_related("client", "employee")

    if role == "client":
        requests = requests.filter(client__user=request.user)
    elif role not in {"employee", "admin"}:
        requests = requests.none()

    if status:
        requests = requests.filter(status=status)

    if query:
        requests = requests.filter(title__icontains=query)

    page_number = request.GET.get("page", 1)
    paginator = Paginator(requests, 10)
    page_obj = paginator.get_page(page_number)

    query_string = urlencode({k: v for k, v in {"status": status, "q": query}.items() if v})

    context = {
        "requests": page_obj,
        "page_obj": page_obj,
        "selected_status": status,
        "search_query": query,
        "statuses": ServiceRequest.STATUS_CHOICES,
        "role": role,
        "query_string": query_string,
    }
    return render(request, "request_list.html", context)


@login_required
def request_detail(request, pk):
    service_request, error = get_request_for_user_or_403(request, pk)
    if error:
        return error

    role = get_user_role(request.user)
    can_edit = role in {"admin", "employee"} or (
        role == "client" and service_request.client.user_id == request.user.id
    )
    can_delete = role == "admin" or (
        role == "client" and service_request.client.user_id == request.user.id
    )

    return render(
        request,
        "request_detail.html",
        {
            "service_request": service_request,
            "role": role,
            "can_edit": can_edit,
            "can_delete": can_delete,
        },
    )


@login_required
def request_create(request):
    role = get_user_role(request.user)

    if role == "employee":
        return HttpResponseForbidden("Сотрудник не может создавать заявки.")

    if request.method == "POST":
        form_data = request.POST.copy()
        if role == "client":
            form_data["status"] = "new"
        form = ServiceRequestForm(form_data)
        if role == "client":
            form.fields["client"].required = False
            form.fields["employee"].required = False

        if form.is_valid():
            service_request = form.save(commit=False)

            if role == "client":
                service_request.client = request.user.client_profile
                service_request.employee = None
                service_request.status = "new"

            if not apply_request_business_rules(service_request):
                messages.error(request, "Нельзя завершить заявку без назначенного сотрудника.")
            else:
                service_request.save()
                messages.success(request, "Заявка успешно создана.")
                return redirect("request_list")
    else:
        form = ServiceRequestForm()
        if role == "client":
            form.fields["client"].widget = form.fields["client"].hidden_widget()
            form.fields["employee"].widget = form.fields["employee"].hidden_widget()
            form.fields["status"].widget = form.fields["status"].hidden_widget()

    return render(
        request,
        "request_form.html",
        {
            "form": form,
            "title": "Создание заявки",
            "role": role,
        },
    )


@login_required
def request_update(request, pk):
    service_request, error = get_request_for_user_or_403(request, pk)
    if error:
        return error

    role = get_user_role(request.user)

    if request.method == "POST":
        form_data = request.POST.copy()
        if role == "client":
            form_data["client"] = service_request.client_id
            form_data["status"] = service_request.status
            form_data["employee"] = service_request.employee_id or ""
        form = ServiceRequestForm(form_data, instance=service_request)

        if role == "client":
            form.fields["client"].required = False
            form.fields["employee"].required = False
            form.fields["status"].required = False

        if form.is_valid():
            updated_request = form.save(commit=False)

            if role == "client":
                updated_request.client = service_request.client
                updated_request.employee = service_request.employee
                updated_request.status = service_request.status

            if not apply_request_business_rules(updated_request):
                messages.error(request, "Нельзя завершить заявку без назначенного сотрудника.")
            else:
                updated_request.save()
                messages.success(request, "Заявка успешно обновлена.")
                return redirect("request_detail", pk=service_request.pk)
    else:
        form = ServiceRequestForm(instance=service_request)
        if role == "client":
            form.fields["client"].widget = form.fields["client"].hidden_widget()
            form.fields["employee"].widget = form.fields["employee"].hidden_widget()
            form.fields["status"].widget = form.fields["status"].hidden_widget()

    return render(
        request,
        "request_form.html",
        {
            "form": form,
            "service_request": service_request,
            "title": "Редактирование заявки",
            "role": role,
        },
    )


@login_required
def request_delete(request, pk):
    service_request, error = get_request_for_user_or_403(request, pk)
    if error:
        return error

    role = get_user_role(request.user)
    if role not in {"admin", "client"}:
        return HttpResponseForbidden("Недостаточно прав.")
    if role == "client" and service_request.client.user_id != request.user.id:
        return HttpResponseForbidden("Недостаточно прав.")

    if request.method == "POST":
        service_request.delete()
        messages.success(request, "Заявка успешно удалена.")
        return redirect("request_list")

    return render(request, "request_confirm_delete.html", {"service_request": service_request})


@login_required
def client_list(request):
    forbidden = require_admin(request)
    if forbidden:
        return forbidden

    clients = Client.objects.select_related("user").all()
    return render(request, "client_list.html", {"clients": clients})


@login_required
def client_create(request):
    forbidden = require_admin(request)
    if forbidden:
        return forbidden

    if request.method == "POST":
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Клиент успешно создан.")
            return redirect("client_list")
    else:
        form = ClientForm()

    return render(request, "client_form.html", {"form": form, "title": "Добавление клиента"})


@login_required
def client_update(request, pk):
    forbidden = require_admin(request)
    if forbidden:
        return forbidden

    client = get_object_or_404(Client, pk=pk)
    if request.method == "POST":
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, "Клиент успешно обновлен.")
            return redirect("client_list")
    else:
        form = ClientForm(instance=client)

    return render(request, "client_form.html", {"form": form, "title": "Редактирование клиента"})


@login_required
def client_delete(request, pk):
    forbidden = require_admin(request)
    if forbidden:
        return forbidden

    client = get_object_or_404(Client, pk=pk)
    if request.method == "POST":
        client.delete()
        messages.success(request, "Клиент успешно удален.")
        return redirect("client_list")

    return render(request, "client_confirm_delete.html", {"client": client})


@login_required
def employee_list(request):
    forbidden = require_admin(request)
    if forbidden:
        return forbidden

    employees = Employee.objects.select_related("user").all()
    return render(request, "employee_list.html", {"employees": employees})


@login_required
def employee_create(request):
    forbidden = require_admin(request)
    if forbidden:
        return forbidden

    if request.method == "POST":
        form = EmployeeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Сотрудник успешно создан.")
            return redirect("employee_list")
    else:
        form = EmployeeForm()

    return render(request, "employee_form.html", {"form": form, "title": "Добавление сотрудника"})


@login_required
def employee_update(request, pk):
    forbidden = require_admin(request)
    if forbidden:
        return forbidden

    employee = get_object_or_404(Employee, pk=pk)
    if request.method == "POST":
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, "Сотрудник успешно обновлен.")
            return redirect("employee_list")
    else:
        form = EmployeeForm(instance=employee)

    return render(request, "employee_form.html", {"form": form, "title": "Редактирование сотрудника"})


@login_required
def employee_delete(request, pk):
    forbidden = require_admin(request)
    if forbidden:
        return forbidden

    employee = get_object_or_404(Employee, pk=pk)
    if request.method == "POST":
        employee.delete()
        messages.success(request, "Сотрудник успешно удален.")
        return redirect("employee_list")

    return render(request, "employee_confirm_delete.html", {"employee": employee})


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user, role="client")
            Client.objects.create(
                user=user,
                name=user.username,
                email=user.email,
                phone_number="",
            )
            login(request, user)
            messages.success(request, "Регистрация прошла успешно.")
            return redirect("home")
    else:
        form = RegisterForm()

    return render(request, "register.html", {"form": form})


def login_view(request):
    return render(request, "login.html")
