from django import forms

from sagepaypi.models import Transaction


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = (
            'amount',
            'currency'
        )
