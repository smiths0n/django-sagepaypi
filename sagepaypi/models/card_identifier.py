import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _


class CardIdentifier(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True
    )
    created_at = models.DateTimeField(
        _('Created at'),
        auto_now_add=True
    )

    first_name = models.CharField(
        _('First name'),
        max_length=100
    )
    last_name = models.CharField(
        _('Last name'),
        max_length=100
    )
    billing_address_1 = models.CharField(
        _('Billing address 1'),
        max_length=255
    )
    billing_address_2 = models.CharField(
        _('Billing address 2'),
        max_length=255,
        null=True,
        blank=True
    )
    billing_city = models.CharField(
        _('Billing city'),
        max_length=255
    )
    billing_country = models.CharField(
        _('Billing country'),
        max_length=2
    )
    billing_postal_code = models.CharField(
        _('Billing Postal/Zip Code'),
        max_length=12,
        null=True,
        blank=True,
        help_text=_('Required for all countries except Ireland')
    )
    billing_state = models.CharField(
        _('Billing state'),
        max_length=2,
        null=True,
        blank=True,
        help_text=_('Required only if country is United States')
    )

    merchant_session_key = models.CharField(
        _('Merchant session key'),
        max_length=100,
        help_text=_('The merchant session key that was used to register the card identifier with Sage Pay.')
    )
    card_type = models.CharField(
        _('Card type'),
        max_length=255,
        help_text=_('The type of card reported by Sage Pay.')
    )
    last_four_digits = models.CharField(
        _('Last four digits'),
        max_length=4,
        help_text=_('The last four digits of the card.')
    )
    expiry_date = models.CharField(
        _('Expiry date'),
        max_length=4,
        help_text=_('The expiry date of the card, format "MMYY".')
    )
    card_identifier = models.CharField(
        _('Card identifier'),
        max_length=100,
        help_text=_('The card identifier key sent back from Sage Pay.')
    )
    card_identifier_expiry = models.DateTimeField(
        _('Card identifier expiry'),
        help_text=_(
            'The datetime in which a transaction must be submitted to Sage Pay by '
            'before the card identifier becomes invalid.'
        )
    )

    def __str__(self):
        return str(self.pk)

    def clean(self):
        """
        Includes additional validation to ensure:

        - billing_postal_code is present when billing_country is IE.
        - billing_state is present when billing_country is US.
        """

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

    @property
    def display_text(self):
        return '%s (%s)' % (
            self.card_type,
            self.last_four_digits
        )
