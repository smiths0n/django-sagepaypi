Settings
========

Any settings with their defaults are listed below for quick reference.

.. code-block:: python

    # when true all urls to Sage Pay are prefixed https://pi-test.sagepay.com/api/v1
    SAGEPAYPI_TEST_MODE = settings.DEBUG

    # Your vendor name, key and password on Sage Pay
    # For testing purposes the are two sandbox accounts within sagepay. SAGEPAYPI_TEST_MODE must be True
    # see http://integrations.sagepay.co.uk/content/sandbox-testing
    SAGEPAYPI_VENDOR_NAME = None
    SAGEPAYPI_INTEGRATION_KEY = None
    SAGEPAYPI_INTEGRATION_PASSWORD = None

    # This is the length of days the transaction tokens are valid for when
    # redirecting back after a 3d login to Sage Pay secure auth
    SAGEPAYPI_TOKEN_URL_DAYS_VALID = 1

    # the url name to redirect to after completing a Sage Pay secure auth login
    # ie 'mysite:transaction_status'
    SAGEPAYPI_POST_3D_SECURE_REDIRECT_URL = None
