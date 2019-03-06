from django.contrib import admin

from sagepaypi.models import CardIdentifier, Customer, Transaction, TransactionResponse


class ReadOnlyAdmin:

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class CardIdentifierAdmin(ReadOnlyAdmin, admin.ModelAdmin):
    list_display = [
        'pk',
        'display_text',
        'customer',
        'reusable',
        'created_at'
    ]


class CustomerAdmin(admin.ModelAdmin):
    list_display = [
        'pk',
        'first_name',
        'last_name',
        'billing_address_1',
        'billing_city',
        'billing_country',
        'billing_postal_code'
    ]


class TransactionResponseAdmin(ReadOnlyAdmin, admin.StackedInline):
    model = TransactionResponse

    def has_delete_permission(self, request, obj=None):
        return False


class TransactionAdmin(ReadOnlyAdmin, admin.ModelAdmin):
    inlines = [
        TransactionResponseAdmin
    ]
    list_display = [
        'pk',
        'type',
        'amount',
        'currency',
        'status',
        'transaction_id',
        'instruction',
        'created_at'
    ]


admin.site.register(CardIdentifier, CardIdentifierAdmin)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(Transaction, TransactionAdmin)
