from django.contrib import admin

from service.models import Client, Employee, ServiceRequest, UserProfile


# Register your models here.
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone_number')
    search_fields = ('name', 'email')


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone_number', 'position')
    search_fields = ('name', 'email')


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ('title', 'client', 'employee', 'status', 'created_at')
    list_filter = ('status', 'created_at')

    search_fields = ('title', 'description', 'client__name', 'employee__name')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "role")
    list_filter = ("role",)
    search_fields = ("user__username",)
