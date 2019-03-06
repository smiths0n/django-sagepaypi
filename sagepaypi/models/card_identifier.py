import uuid

from django.db import models
from django.utils.translation import ugettext_lazy as _


class CardIdentifier(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    customer = models.ForeignKey(
        'sagepaypi.Customer',
        on_delete=models.CASCADE,
        related_name='card_identifiers',
    )
    reusable = models.BooleanField(
        default=False,
        help_text=_('Indicates the card identifier can be used in future transactions.')
    )
    merchant_session_key = models.CharField(
        max_length=100,
        help_text=_('The merchant session key that was used to register the card identifier with Sage Pay.')
    )
    card_type = models.CharField(
        max_length=255,
        help_text=_('The type of card reported by Sage Pay.')
    )
    last_four_digits = models.CharField(
        max_length=4,
        help_text=_('The last four digits of the card.')
    )
    expiry_date = models.CharField(
        max_length=4,
        help_text=_('The expiry date of the card, format "MMYY".')
    )
    card_identifier = models.CharField(
        max_length=100,
        help_text=_('The card identifier key sent back from Sage Pay.')
    )
    card_identifier_expiry = models.DateTimeField(
        help_text=_(
            'The datetime in which a transaction must be submitted to Sage Pay by '
            'before the card identifier becomes invalid.'
        )
    )

    def __str__(self):
        return str(self.pk)

    @property
    def display_text(self):
        return '%s (%s)' % (
            self.card_type,
            self.last_four_digits
        )
