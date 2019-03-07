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

Add the urls to your ``urls.py``:

.. code-block:: python

    from django.contrib import admin
    from django.urls import path, include

    urlpatterns = [
        path('admin/', admin.site.urls),
        path('sagepay/', include('sagepaypi.urls')),
        ...
    ]
