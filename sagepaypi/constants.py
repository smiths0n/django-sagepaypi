from django.utils.translation import ugettext_lazy as _


# http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2
COUNTRIES = {
    "IE": _("Ireland"),
    "GB": _("United Kingdom"),
    "US": _("United States"),
}

# https://en.wikipedia.org/wiki/ISO_4217
CURRENCIES = {
    "GBP": _("Pound Sterling"),
}

TRANSACTION_TYPES = {
    "Payment": _("Payment"),
    "Deferred": _("Deferred"),
    "Repeat": _("Repeat"),
    "Refund": _("Refund"),
}

# http://en.wikipedia.org/wiki/ISO_3166-2:US
US_STATES = {
    "AL": _("Alabama"),
}


def get_country_choices():
    return [(c, v) for c, v in COUNTRIES.items()]


def get_currency_choices():
    return [(c, v) for c, v in CURRENCIES.items()]


def get_transaction_type_choices():
    return [(c, v) for c, v in TRANSACTION_TYPES.items()]


def get_us_state_choices():
    return [(c, v) for c, v in US_STATES.items()]
