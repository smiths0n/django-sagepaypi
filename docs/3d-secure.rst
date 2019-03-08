Using 3-D Secure
================

Transactions that require 3-D Secure authentication are a little more complicated because
your customer has to be forwarded to their card issuer to authenticate themselves before
a card authorisation can occur.

Firstly go through the steps of creating a new card identifier and a payment in :ref:`payments-using-tokens`.
But instead of the card number in the example use one that requires the card holder to enter their password.

.. note::

   You can find details of the test cards here. You need a card that has its ``3-D Secure object status`` set
   to ``Authenticated``.

   http://integrations.sagepay.co.uk/content/sandbox-testing

Once you've done that take a look at the transaction, its status should be the following:

.. code-block:: bash

    >>> transaction.status
    '3DAuth'

    >>> transaction.status_detail
    'Please redirect your customer to the ACSURL to complete the 3DS Transaction'

    >>> transaction.requires_3d_secure
    True

The payment will not be authorised until the following steps have been taken.

Redirecting to authenticate
---------------------------

In a view that is creating the payment you need to render a template that includes details of the transaction
and submit it to the url defined in ``transaction.acs_url``. More can be seen regarding the form in their
docs at http://integrations.sagepay.co.uk/content/getting-started-integrate-using-your-own-form.

We have created a simple template that you can render yourself:

.. code-block:: python

    def post(self, request, *args, **kwargs):

        # other bits

        transaction.submit_transaction()

        if transaction.requires_3d_secure:
            return render(
                request,
                'sagepaypi/3d_secure_redirect_form.html',
                {'transaction': transaction}
            )

        # other bits where it does't require 3d auth

Below it the content of the template:

.. code-block:: html

    {% load sagepaypi_tags %}
    <!DOCTYPE html>
    <html>
        <head>
            <title>Django SageSayPI Redirect Form</title>
        </head>
        <body>
            {% sagepay_secure_redirect_form transaction %}
        </body>
    </html>

This will render the form and submit it via javascript.
How and where you render it is up to you. As you can see there is also a template tag you can use
to include it somewhere yourself.

Handling the response
---------------------

Once the user enters their password they are redirected back to the site using a one time use url
provided by this package to complete the rest of the transaction. This includes:

- Getting the status of the authentication (Authenticated, Not Authenticated).
- Getting the outcome of the transaction.
- Redirecting to a url defined in your application.

Setting up the view
-------------------

Once the 3-D secure has complete and we know the outcome of the transaction, we need to redirect to a view
which you need to define. This could be to do things like:

- Show the status.
- Maybe send a confirmation email to the customer.
- Start the process again if it failed.

An example can be seen below:

.. code-block:: python

    # views.py

    from django.views.generic import DetailView

    from sagepaypi.models import Transaction


    class TransactionStatusView(DetailView):
        template_name = 'example/transaction_status.html'
        model = Transaction

        def get_object(self):
            tidb64 = self.kwargs['tidb64']
            token = self.kwargs['token']
            return Transaction.objects.get_for_token(tidb64, token)

.. code-block:: python

    # urls.py

    from django.urls import path, include

    from example.views import TransactionStatusView

    appname = 'example'
    urlpatterns = [
        path('sagepay/', include('sagepaypi.urls')),
        path('transactions/<tidb64>/<token>/status/',
             TransactionStatusView.as_view(),
             name='transaction_status'
        ),
    ]

.. code-block:: html

    <!DOCTYPE html>
    <html>
        <head>
            <title>Transaction Status</title>
        </head>
        <body>
            <h2>Transaction Status</h2>
            <p>Status: {{ transaction.status }}</p>
            <p>Status Code: {{ transaction.status_code }}</p>
            <p>Detail: {{ transaction.status_detail }}</p>
            <p>Amount: {{ transaction.amount }}</p>
            <p>Description: {{ transaction.description }}</p>
            {% if transaction.bank_authorisation_code %}
                <p>Bank authorisation code: {{ transaction.bank_authorisation_code }}</p>
            {% endif %}
        </body>
    </html>

.. important::

   For this application to know what the url is called you need to set the
   ``SAGEPAYPI_POST_3D_SECURE_REDIRECT_URL`` in your settings file.

   It takes the format of ``appname:urlname`` ie ``example:transaction_status`` for the above.

   The parameters ``tidb64`` and ``token`` are passed to that url so they must be present in your url and
   the transaction must be fetched using the ``Transaction.objects.get_for_token(tidb64, token)`` manager method.
