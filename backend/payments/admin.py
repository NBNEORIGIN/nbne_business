from django.contrib import admin
from .models import Customer, PaymentSession, Transaction, Refund


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['email', 'name', 'provider', 'created_at']
    search_fields = ['email', 'name']


@admin.register(PaymentSession)
class PaymentSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'payable_type', 'payable_id', 'amount_pence', 'currency', 'status', 'created_at']
    list_filter = ['status', 'payable_type']
    search_fields = ['payable_id']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'payment_session', 'gross_amount_pence', 'currency', 'captured_at']


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ['id', 'transaction', 'amount_pence', 'status', 'created_at']
    list_filter = ['status']
