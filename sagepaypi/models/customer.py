import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _

from sagepaypi.constants import get_country_choices, get_us_state_choices


class Customer(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    first_name = models.CharField(
        max_length=100
    )
    last_name = models.CharField(
        max_length=100
    )
    billing_address_1 = models.CharField(
        max_length=255
    )
    billing_address_2 = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )
    billing_city = models.CharField(
        max_length=255
    )
    billing_country = models.CharField(
        max_length=2,
        choices=get_country_choices()
    )
    billing_postal_code = models.CharField(
        _('Postal/Zip Code'),
        max_length=12,
        null=True,
        blank=True,
        help_text=_('Required for all countries except Ireland')
    )
    billing_state = models.CharField(
        max_length=2,
        null=True,
        blank=True,
        choices=get_us_state_choices(),
        help_text=_('Required only if country is United States')
    )

    def __str__(self):
        return str(self.pk)

    def clean(self):
        errors = {}

        # post code is required when country is not IE
        if self.billing_country != 'IE' and not self.billing_postal_code:
            errors['billing_postal_code'] = _('This field is required.')

        # billing_state is required when country is US
        if self.billing_country == 'US' and not self.billing_state:
            errors['billing_state'] = _('This field is required.')

        if errors:
            raise ValidationError(errors)

    @property
    def billing_address(self):
        address = {
            'address1': self.billing_address_1,
            'city': self.billing_city,
            'country': self.billing_country
        }

        if self.billing_address_2:
            address['address2'] = self.billing_address_2
        if self.billing_postal_code:
            address['postalCode'] = self.billing_postal_code
        if self.billing_state:
            address['state'] = self.billing_state

        return address
