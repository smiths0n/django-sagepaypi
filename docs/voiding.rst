Voiding
=======

Once a transaction has been submitted to Sage Pay and processed through their system
and has been successfully authorised, the transaction will be sent to the bank for settlement.

If you wish to cancel that payment before it is settled with the bank the following day,
you can void a transaction to prevent it from ever being settled,
thus saving you your transaction charges and the customer from ever being charged.

Once a transaction has been settled you can no longer void it.
If you wish to return funds to the customer you need to perform a refund.

You are able to request a void on a Payment or Refund.

A successful void request will cancel the transaction and stop any funds moving before settlement
has taken place.

Voiding a transaction
---------------------

Get the transaction you wish to void:

.. code-block:: bash

    >>> from sagepaypi.models import Transaction

    >>> transaction = Transaction.objects.get(pk='ecdadf86-7899-4c6b-9f76-71ca3077174c')

To perform a void:

.. code-block:: bash

    >>> transaction.void()
    <Transaction: ecdadf86-7899-4c6b-9f76-71ca3077174c>

Errors
------

In the event of a void failing always catch the error and always check the status:

.. code-block:: python

    from sagepaypi.exceptions import InvalidTransactionStatus

    try:
        transaction.void()
        if transaction.instruction == 'void':
            # Yay!!
    except InvalidTransactionStatus:
        # this will be thrown if the original transaction is
        # not in a state that a void can even be attempted.
        # ie it was not successful in the first place or it's a deferred or repeat
        # or it was not created today.
