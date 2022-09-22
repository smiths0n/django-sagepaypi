from django.contrib import admin

from sagepaypi.models import CardIdentifier, Transaction, TransactionResponse


class ReadOnlyAdmin:

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class CardIdentifierAdmin(ReadOnlyAdmin, admin.ModelAdmin):
    list_display = [
        'pk',
        'display_text',
        'first_name',
        'last_name',
        'created_at'
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
admin.site.register(Transaction, TransactionAdmin)
