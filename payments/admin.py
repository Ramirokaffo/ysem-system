from django.contrib import admin
from .models import *

@admin.register(PaymentInstallment)
class PaymentInstallmentAdmin(admin.ModelAdmin):
    list_display = ['program', 'name', 'academic_year', 'level', 'order_number', 'amount', 'due_date', 'created_at']
    list_filter = ['program', 'due_date', "academic_year", "level"]
    search_fields = ['name', 'program__name']
    searche_help_text = "Recherchez par nom de tranche ou par programme"
    ordering = ['program__name', 'level__name', 'order_number']
    date_hierarchy = 'due_date'
    readonly_fields = ['created_at', 'updated_at', 'deleted_at']
    save_on_top = True


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['student', 'installment', 'academic_year', 'category', 'amount_paid', 'payment_date', 'receipt_number', 'created_at']
    list_filter = ['payment_date', 'academic_year', 'category', 'created_at']
    search_fields = ['student__metadata__first_name', 'student__metadata__last_name', 'installment__name', 'receipt_number']
    ordering = ['-payment_date', '-created_at']
    date_hierarchy = 'payment_date'
    readonly_fields = ['payment_date', 'created_at', 'updated_at']
    save_on_top = True

