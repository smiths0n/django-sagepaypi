Repeat payments
===============

A repeat payment allows you to process another transaction by using the details of a customer that were captured
for the original payment and process them again.

When processing a repeat transaction there are no restrictions on the amount you are able to charge.
In order to be able to use the repeat transaction type you first require a Continuous Authority merchant account.

Performing a repeat payment
---------------------------

Any authorised transaction can be used as a basis for initiating another transaction using the same card details.
A Repeat transaction simply uses the card details from the original transaction,
and charges it again with an amount specified in your post.
The amount does not have to match the value of the original transaction.

Get the transaction you wish to repeat:

.. code-block:: bash

    >>> from sagepaypi.models import Transaction

    >>> transaction = Transaction.objects.get(pk='ecdadf86-7899-4c6b-9f76-71ca3077174c')

To perform a repeat of the transaction just call the repeat method:

.. code-block:: bash

    >>> transaction.repeat()
    <Transaction: f3f0e2d3-18d1-48c6-800c-9e3e3cfdb288>

The new transaction returned is the repeat. Once again look in Django admin and you will see the details

Changing additional properties
------------------------------

Additionally you can change things like the ``amount``, ``description`` and ``vendor_tx_code``:

.. code-block:: bash

    >>> transaction.repeat(amount=1, description='Repeat of goods', vendor_tx_code='repeat-some-unique-suffix')

Errors
------

In the event of a repeat failing always catch the error and always check the status:

.. code-block:: python

    from sagepaypi.exceptions import InvalidTransactionStatus

    try:
        repeat = transaction.repeat()
        if repeat.status == 'Ok':
            # Yay!!
    except InvalidTransactionStatus:
        # this will be thrown if the original transaction is
        # not in a state that a repeat can even be attempted.
        # ie it was not successful in the first place.