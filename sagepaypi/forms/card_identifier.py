from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from sagepaypi.gateway import SagepayGateway
from sagepaypi.fields import CardNumberField, CardCVCodeField, CardExpiryDateField
from sagepaypi.models import CardIdentifier


class CardIdentifierForm(forms.ModelForm):
    card_holder_name = forms.CharField()
    card_number = CardNumberField()
    card_expiry_date = CardExpiryDateField()
    card_security_code = CardCVCodeField()

    reusable = forms.BooleanField(
        label=_('Save card details for future payments'),
        required=False
    )

    class Meta:
        fields = [
            'first_name',
            'last_name',
            'billing_address_1',
            'billing_address_2',
            'billing_city',
            'billing_country',
            'billing_postal_code',
            'billing_state',
            'card_holder_name',
            'card_number',
            'card_expiry_date',
            'card_security_code',
            'reusable'
        ]
        model = CardIdentifier

    def save(self, commit=True):
        instance = super().save(commit=False)

        gateway = SagepayGateway()

        new_identifier = gateway.create_card_identifier(
            self.cleaned_data['card_holder_name'],
            self.cleaned_data['card_number'],
            self.cleaned_data['card_expiry_date'].strftime('%m%y'),
            self.cleaned_data['card_security_code']
        )

        if not new_identifier:
            return ValidationError('oops')

        instance.merchant_session_key = new_identifier[0]
        instance.card_identifier = new_identifier[1]
        instance.card_identifier_expiry = new_identifier[2]
        instance.card_type = new_identifier[3]
        instance.last_four_digits = self.cleaned_data['card_number'][-4:]
        instance.expiry_date = self.cleaned_data['card_expiry_date'].strftime('%m%y')

        instance.save()

        return instance
