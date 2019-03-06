from django import forms
from django.utils.translation import ugettext_lazy as _

from sagepaypi.fields import CardNumberField, CardCVCodeField, CardExpiryDateField


class RegisterCardForm(forms.Form):
    card_holder_name = forms.CharField()
    card_number = CardNumberField()
    expiry_date = CardExpiryDateField()
    security_code = CardCVCodeField()
    reusable = forms.BooleanField(
        label=_('Save card details for future payments'),
        required=False
    )

    class Meta:
        fields = [
            'card_holder_name',
            'card_number',
            'expiry_date',
            'security_code',
            'reusable'
        ]
