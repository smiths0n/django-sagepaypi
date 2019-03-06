import dateutil
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from sagepaypi.gateway import SagepayGateway, SagepayHttpResponse
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

        post_data = {
            'cardDetails': {
                'cardholderName': self.cleaned_data['card_holder_name'],
                'cardNumber': self.cleaned_data['card_number'],
                'expiryDate': self.cleaned_data['card_expiry_date'].strftime('%m%y'),
                'securityCode': self.cleaned_data['card_security_code'],
            }
        }

        response, merchant_session_key = gateway.create_card_identifier(post_data)

        data = response.json()

        if response.status_code == SagepayHttpResponse.HTTP_201:
            instance.merchant_session_key = merchant_session_key
            instance.card_identifier = data['cardIdentifier']
            instance.card_identifier_expiry = dateutil.parser.parse(data['expiry'])
            instance.card_type = data['cardType']
            instance.last_four_digits = self.cleaned_data['card_number'][-4:]
            instance.expiry_date = self.cleaned_data['card_expiry_date'].strftime('%m%y')

            instance.save(commit)

        else:
            raise ValidationError(data)

        return instance
