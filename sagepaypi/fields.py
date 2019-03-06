import re
from calendar import monthrange, IllegalMonthError
from datetime import date

from django import forms
from django.utils.translation import ugettext_lazy as _

from sagepaypi.widgets import ExpiryDateWidget


CREDIT_CARD_RE = [
    r'4[0-9]{12}(?:[0-9]{3})?',  # Visa Card
    r'(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14})',  # Visa Master Card
    r'5[1-5][0-9]{14}',  # Mastercard
    r'(5018|5020|5038|6304|6759|6761|6763)[0-9]{8,15}',  # Maestro Card UK
    r'3[47][0-9]{13}',  # American Express
    r'3(?:0[0-5]|[68][0-9])[0-9]{11}',  # Diners Club
    r'(?:2131|1800|35\d{3})\d{11}',  # JCB
]
CV_VALUE_RE = r'^([0-9]{3,4})$'


class CardNumberField(forms.CharField):
    default_error_messages = {
        'required': _('Please enter a credit card number.'),
        'invalid': _('The credit card number you entered is invalid.'),
    }

    def clean(self, value):
        value = value.replace(' ', '').replace('-', '')
        if not value and self.required:
            raise forms.ValidationError(self.error_messages['required'])
        if value and not re.match('(?:%s)' % '|'.join(CREDIT_CARD_RE), value):
            raise forms.ValidationError(self.error_messages['invalid'])
        return value


class CardCVCodeField(forms.CharField):
    widget = forms.widgets.TextInput(attrs={'maxlength': 4})
    default_error_messages = {
        'required': _('Please enter the three or four digit security code.'),
        'invalid': _('The security code you entered is invalid.'),
    }

    def clean(self, value):
        value = value.replace(' ', '')
        if not value and self.required:
            raise forms.ValidationError(self.error_messages['required'])
        if value and not re.match(CV_VALUE_RE, value):
            raise forms.ValidationError(self.error_messages['invalid'])
        return value


class CardExpiryDateField(forms.MultiValueField):
    default_error_messages = {
        'invalid_month': _('Please enter a valid month.'),
        'invalid_year': _('Please enter a valid year.'),
        'date_passed': _('This expiry date has passed.'),
    }

    def __init__(self, *args, **kwargs):
        today = date.today()
        error_messages = self.default_error_messages.copy()

        if 'error_messages' in kwargs:
            error_messages.update(kwargs['error_messages'])

        if 'initial' not in kwargs:
            kwargs['initial'] = today

        months = [
            (x, '%02d (%s)' % (x, date(today.year, x, 1).strftime('%b')))
            for x in range(1, 13)
        ]
        years = [
            (x, x)
            for x in range(today.year, today.year + 15)
        ]

        fields = (
            forms.ChoiceField(choices=months, error_messages={'invalid': error_messages['invalid_month']}),
            forms.ChoiceField(choices=years, error_messages={'invalid': error_messages['invalid_year']}),
        )

        super().__init__(fields, *args, **kwargs)

        self.widget = ExpiryDateWidget(widgets=[fields[0].widget, fields[1].widget])

    def clean(self, value):
        expiry_date = super().clean(value)
        if expiry_date and date.today() > expiry_date:
            raise forms.ValidationError(self.error_messages['date_passed'])
        return expiry_date

    def compress(self, data_list):
        if data_list:
            try:
                month = int(data_list[0])
            except (ValueError, TypeError):
                raise forms.ValidationError(self.error_messages['invalid_month'])
            try:
                year = int(data_list[1])
            except (ValueError, TypeError):
                raise forms.ValidationError(self.error_messages['invalid_year'])
            try:
                day = monthrange(year, month)[1]
            except IllegalMonthError:
                raise forms.ValidationError(self.error_messages['invalid_month'])
            except ValueError:
                raise forms.ValidationError(self.error_messages['invalid_year'])

            return date(year, month, day)

        return None
