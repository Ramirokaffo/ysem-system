from django.contrib import admin
from .models import Staff


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'gender', 'phone_number', 'is_active', 'is_staff']
    list_filter = ['role', 'gender', 'is_active', 'is_staff']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'email']
    date_hierarchy = 'born_date'
