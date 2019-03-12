import dateutil

from django import forms
from django.utils.translation import ugettext_lazy as _

from sagepaypi.gateway import SagepayHttpResponse
from sagepaypi.fields import CardNumberField, CardCVCodeField, CardExpiryDateField
from sagepaypi.models import CardIdentifier


class CardIdentifierForm(forms.ModelForm):
    card_holder_name = forms.CharField()
    card_number = CardNumberField()
    card_expiry_date = CardExpiryDateField()
    card_security_code = CardCVCodeField()

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
            'card_security_code'
        ]
        model = CardIdentifier

    def clean(self):
        """
        Here we are overriding the clean method in the form to get a new
        card identifier with Sage Pay. If it fails then it will get stopped
        via form.is_valid().

        This may not be the best approach but if feels better than handling
        a validation error after form.is_valid() has already been relorted as
        successful.
        """

        super().clean()

        card_holder_name = self.cleaned_data.get('card_holder_name')
        card_number = self.cleaned_data.get('card_number')
        card_expiry_date = self.cleaned_data.get('card_expiry_date')
        card_security_code = self.cleaned_data.get('card_security_code')

        if all([card_holder_name, card_number, card_expiry_date, card_security_code]):
            # submit new card to Sage Pay only if all fields are clean

            from sagepaypi.gateway import default_gateway

            data = {
                'cardDetails': {
                    'cardholderName': card_holder_name,
                    'cardNumber': card_number,
                    'expiryDate': card_expiry_date.strftime('%m%y'),
                    'securityCode': card_security_code,
                }
            }

            response, merchant_session_key = default_gateway.create_card_identifier(data)

            data = response.json()

            if response.status_code == SagepayHttpResponse.HTTP_201:
                self.instance.merchant_session_key = merchant_session_key
                self.instance.card_identifier = data['cardIdentifier']
                self.instance.card_identifier_expiry = dateutil.parser.parse(data['expiry'])
                self.instance.card_type = data['cardType']

            elif response.status_code == SagepayHttpResponse.HTTP_422:
                # add any errors relating to the fields filled in
                # and map them to form field properties
                error_field_mappings = {
                    'cardDetails.cardholderName': 'card_holder_name',
                    'cardDetails.cardNumber': 'card_number',
                    'cardDetails.expiryDate': 'card_expiry_date',
                    'cardDetails.securityCode': 'card_security_code',
                }
                errors = data.get('errors')
                if errors and isinstance(errors, list):
                    for error in errors:
                        prop = error.get('property')
                        msg = error.get('clientMessage')
                        if prop and msg and prop in error_field_mappings:
                            # the prop is in the mapping so add the error to the field
                            self.add_error(error_field_mappings[prop], msg)
                        elif msg:
                            # if not add the error to the NON_FIELD_ERRORS
                            self.add_error(None, msg)

            else:
                # something unexpected has happened
                err = _('Something went wrong at sagepay, Please check the card details and try again.')
                self.add_error(None, err)

        return self.cleaned_data

    def save(self, commit=True):
        """
        Set additional required instance attributes before save.
        """

        self.instance.last_four_digits = self.cleaned_data['card_number'][-4:]
        self.instance.expiry_date = self.cleaned_data['card_expiry_date'].strftime('%m%y')

        return super().save(commit)
