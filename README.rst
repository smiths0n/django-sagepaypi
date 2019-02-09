Django SagePayPI
================

|CircleCI| |Codecov|

Django SagePayPI Payment Gateway

Documentation
-------------

Can be found on `readthedocs <http://django-sagepaypi.readthedocs.io/>`_.

Example site with docker
------------------------

Clone the repo

.. code:: bash

    $ git clone https://github.com/AccentDesign/django-sagepaypi.git

Run the docker container

.. code:: bash

    $ cd django-sagepaypi
    $ docker-compose up

Create yourself a superuser

.. code:: bash

    $ docker-compose exec app bash
    $ python manage.py createsuperuser

Go to http://127.0.0.1:8000

.. |CircleCI| image:: https://circleci.com/gh/AccentDesign/django-sagepaypi/tree/master.svg?style=svg
   :target: https://circleci.com/gh/AccentDesign/django-sagepaypi/tree/master
.. |Codecov| image:: https://codecov.io/gh/AccentDesign/django-sagepaypi/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/AccentDesign/django-sagepaypi
