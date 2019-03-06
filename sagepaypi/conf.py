from django.conf import settings


SETTINGS_PREFIX = 'SAGEPAYPI'
SETTINGS_DEFAULTS = {
    'TEST_MODE': settings.DEBUG,
    'VENDOR_NAME': None,
    'INTEGRATION_KEY': None,
    'INTEGRATION_PASSWORD': None,
    'TOKEN_URL_DAYS_VALID': 1,
    'POST_3D_SECURE_REDIRECT_URL': None
}


def get_setting(name):
    setting_key = '{}_{}'.format(SETTINGS_PREFIX, name)
    return getattr(settings, setting_key, SETTINGS_DEFAULTS[name])
