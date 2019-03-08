.. _payments-using-tokens:

Payment using tokens
====================

The Sage Pay Token functionality allows you to save the card details of your customer
in the form of a token (a reusable card identifier) and use it for future purchases.

.. _creating-a-card-identifier:

Creating a card identifier
--------------------------

Before you can submit a payment to Sage Pay you need to create a reusable card identifier.
This consists of capturing details of the payee such as name, card details and address of the card holder.

To help you capture this we have created a form ``sagepaypi.forms.CardIdentifierForm``. This will capture
and validate everything you need to process a new payment.

.. admonition:: As of writing the the below details is a test card number which can be found in Sage Pay's documentation.

   http://integrations.sagepay.co.uk/content/sandbox-testing

.. code-block:: bash

    >>> from sagepaypi.forms import CardIdentifierForm

    >>> data = {\
           'first_name': 'Sam',\
           'last_name': 'Jones',\
           'billing_address_1': '88',\
           'billing_city': 'City',\
           'billing_country': 'GB',\
           'billing_postal_code': '412',\
           'card_holder_name': 'SAM JONES',\
           'card_number': '4929000005559',\
           'card_expiry_date_0': '12',\
           'card_expiry_date_1': '2025',\
           'card_security_code': '123'\
        }
    >>> form = CardIdentifierForm(data)

    >>> form.is_valid()
    True

    >>> card_identifier = form.save()

    >>> card_identifier
    <CardIdentifier: 22bd220a-cbf7-4510-b4c3-4a97d1e37235>

Log into django admin and you will see all the details of the card identifier.

.. warning::

   When creating a card identifier you have 400 seconds in which you can use it to make a new payment.
   If you have not created a payment using that card identifier you will be required to request another one
   as Sage Pay will remove it.


Creating your payment
---------------------

Now that you have created a card identifier you can create your payment.

.. code-block:: bash

    >>> from sagepaypi.models import Transaction

    >>> transaction = Transaction(\
            type='Payment',\
            card_identifier=card_identifier,\
            amount=100,\
            currency='GBP',\
            description='Payment of goods'\
        )

    >>> transaction.full_clean()

    >>> transaction.save()

    >>> transaction.submit_transaction()

    >>> print(transaction.status)
    Ok

Log into django admin and you will see all the details of the transaction.