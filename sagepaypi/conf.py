from django.conf import settings


SETTINGS_PREFIX = 'SAGEPAYPI'
SETTINGS_DEFAULTS = {
    'VENDOR_NAME': None,
    'INTEGRATION_KEY': None,
    'INTEGRATION_PASSWORD': None
}


def get_setting(name):
    setting_key = '{}_{}'.format(SETTINGS_PREFIX, name)
    return getattr(settings, setting_key, SETTINGS_DEFAULTS[name])
