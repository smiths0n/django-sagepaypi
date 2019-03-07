Installation
============

Django SagePayPI is available on PyPI - to install it, just run:

.. code-block:: python
  
    pip install django-sagepaypi

Once thats done you need to add the following to your ``INSTALLED_APPS`` settings:

.. code-block:: python

    INSTALLED_APPS = [
        ...
        'sagepaypi'
        ...
    ]

Add your Sage Pay account details in your settings:

.. note::

   Take care to use the sandbox accounts while developing your application.
   As of writing this documentation the below is an account for general testing provided by Sage Pay.

   http://integrations.sagepay.co.uk/content/sandbox-testing

.. code-block:: python

    SAGEPAYPI_VENDOR_NAME = 'sandbox'
    SAGEPAYPI_INTEGRATION_KEY = 'hJYxsw7HLbj40cB8udES8CDRFLhuJ8G54O6rDpUXvE6hYDrria'
    SAGEPAYPI_INTEGRATION_PASSWORD = 'o2iHSrFybYMZpmWOQMuhsXP52V4fBtpuSDshrKDSWsBY1OiN6hwd9Kb12z4j5Us5u'

Add the urls to your ``urls.py``:

.. code-block:: python

    from django.contrib import admin
    from django.urls import path, include

    urlpatterns = [
        path('admin/', admin.site.urls),
        path('sagepay/', include('sagepaypi.urls')),
        ...
    ]
