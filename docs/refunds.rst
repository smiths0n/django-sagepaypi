Refunds
=======

A refund allows you to credit the funds that have already been taken for a transaction,
back to your customer. You are able to complete a refund on Sage Pay for up to 2 years after the
original transaction has been processed, or until the card has expired.

With a refund, you are only able to credit your shoppers the total of the original transaction, and no more.

Performing a refund
-------------------

You are able to refund all successfully authorised transactions that have been processed
through Sage Pay. If the amount of the refund is less that the original transaction amount,
the transaction will be partially refunded. A transaction might be refunded multiple times,
providing that the sum of the amount refunded does not exceed the original transaction amount.

Get the transaction you wish to refund:

.. code-block:: bash

    >>> from sagepaypi.models import Transaction

    >>> transaction = Transaction.objects.get(pk='ecdadf86-7899-4c6b-9f76-71ca3077174c')

To perform a refund of the full amount just call the refund method:

.. code-block:: bash

    >>> transaction.refund()
    <Transaction: f3f0e2d3-18d1-48c6-800c-9e3e3cfdb288>

The new transaction returned is the refund. Once again look in Django admin and you will see the details

Partial refunds
---------------

To perform a partial refund you just need to pass to the refund method of the original transaction an amount.
You can call refund as many times as you need as long as you do not exceed the value of the original transaction

.. code-block:: bash

    >>> transaction.refund(amount=1)

Changing additional properties
------------------------------

Additionally you can change things like the ``description`` and ``vendor_tx_code``:

.. code-block:: bash

    >>> transaction.refund(description='Refund of goods', vendor_tx_code='refunded-some-unique-suffix')

Errors
------

In the event of a refund failing always catch the error and always check the status:

.. code-block:: python

    from sagepaypi.exceptions import InvalidTransactionStatus

    try:
        refund = transaction.refund()
        if refund.status == 'Ok':
            # Yay!!
    except InvalidTransactionStatus:
        # this will be thrown if the original transaction is
        # not in a state that a refund can even be attempted.
        # ie it was not successful in the first place.
