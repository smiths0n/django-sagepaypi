from django.utils.translation import ugettext_lazy as _

import pycountry


COUNTRY_CHOICES = sorted(
    [(o.alpha_2, o.name) for o in pycountry.countries],
    key=lambda o: o[1]
)

TRANSACTION_TYPE_CHOICES = [
    ('Payment', _('Payment')),
    ('Deferred', _('Deferred')),
    ('Repeat', _('Repeat')),
    ('Refund', _('Refund')),
]

US_STATE_CHOICES = sorted(
    [(o.code[-2:], o.name) for o in pycountry.subdivisions.get(country_code='US')],
    key=lambda o: o[1]
)
