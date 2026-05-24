from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Client, Employee, ServiceRequest, UserProfile


class UserBoundModelForm(forms.ModelForm):
    user = forms.ModelChoiceField(
        queryset=User.objects.none(),
        widget=forms.Select(attrs={"class": "form-control"}),
        label="Пользователь",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = getattr(self, "instance", None)
        queryset = User.objects.all().order_by("username")
        queryset = queryset.exclude(client_profile__isnull=False).exclude(employee_profile__isnull=False)

        if instance and instance.pk and instance.user_id:
            queryset = User.objects.filter(pk=instance.user_id) | queryset

        self.fields["user"].queryset = queryset.distinct()


class ClientForm(UserBoundModelForm):
    class Meta:
        model = Client
        fields = ["user", "name", "email", "phone_number"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
        }

    def save(self, commit=True):
        client = super().save(commit=False)
        client.user.email = self.cleaned_data["email"]
        if commit:
            client.user.save(update_fields=["email"])
            client.save()
            user_profile, _ = UserProfile.objects.get_or_create(user=client.user)
            user_profile.role = "client"
            user_profile.save(update_fields=["role"])
        return client


class EmployeeForm(UserBoundModelForm):
    class Meta:
        model = Employee
        fields = ["user", "name", "email", "phone_number", "position"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
            "position": forms.TextInput(attrs={"class": "form-control"}),
        }

    def save(self, commit=True):
        employee = super().save(commit=False)
        employee.user.email = self.cleaned_data["email"]
        if commit:
            employee.user.save(update_fields=["email"])
            employee.save()
            user_profile, _ = UserProfile.objects.get_or_create(user=employee.user)
            user_profile.role = "employee"
            user_profile.save(update_fields=["role"])
        return employee


class ServiceRequestForm(forms.ModelForm):
    class Meta:
        model = ServiceRequest
        fields = ["title", "description", "client", "employee", "status"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "client": forms.Select(attrs={"class": "form-control"}),
            "employee": forms.Select(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-control"}),
        }


class RegisterForm(UserCreationForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": "form-control"}))

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["username", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"class": "form-control"})
        self.fields["email"].widget.attrs.update({"class": "form-control"})
        self.fields["password1"].widget.attrs.update({"class": "form-control"})
        self.fields["password2"].widget.attrs.update({"class": "form-control"})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user
