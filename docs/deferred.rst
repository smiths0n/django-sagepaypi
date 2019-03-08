Deferred payments
=================

Deferred payments give you a way of requesting authorisation for a specified amount,
prior to requesting settlement of these funds at a later date by submitting another request to Sage Pay.
This can be used when orders are made in advance of stock availability or manufacture to secure
confirmation of funds from your customer.

A deferred request is authenticated and built in the same way as a Payment with the ``type`` set to Deferred.

Performing a deferred payment
-----------------------------

When you require a transaction to be performed using deferred you will capture the card details from your customer
and create a card identifier in the same way as did in :ref:`creating-a-card-identifier`.

Then create your transaction in the same way as a payment ensuring its ``type`` is set to ``Deferred``:

.. code-block:: bash

    >>> from sagepaypi.models import Transaction

    >>> transaction = Transaction(\
            type='Deferred',\
            card_identifier=card_identifier,\
            amount=100,\
            currency='GBP',\
            description='Deferred payment of goods'\
        )

    >>> transaction.full_clean()

    >>> transaction.save()

    >>> transaction.submit_transaction()

    >>> print(transaction.status)
    Ok

Log into django admin and you will see all the details of the transaction.

.. note::

   The payment will be held in this deferred state on Sage Pay for 30 days,
   after which Sage Pay will **abort** the payment and release the funds back to the card it came from.

Releasing a deferred payment
----------------------------

A successful deferred payment is valid for up to 30 days. In this period you can choose
to release part or all of the authorised amount, however only a single release can
occur against a deferred transaction.

To perform a release you just need to call the release method on the transaction:

.. code-block:: bash

    >>> transaction.release()

To release a partial amount pass amount as a parameter in the release method:

.. code-block:: bash

    >>> transaction.release(amount=1)

In the event of a release failing always catch the error and always check the status:

.. code-block:: python

    from sagepaypi.exceptions import InvalidTransactionStatus

    try:
        transaction.release()
        if transaction.instruction == 'release':
            # Yay!!
    except InvalidTransactionStatus:
        # this will be thrown if the original transaction is
        # not in a state that a release can even be attempted.
        # ie it was not successful in the first place, it's a not a deferred payment,
        # its older than 30 days or has a instruction already created.

Aborting a deferred payment
---------------------------

Should you have any deferred transactions that no longer require authorisation
you can use the abort request to remove any shadow in place against your customer's account.

After 30 days a deferred transaction will expire so you do not have to use the abort
request on all deferred transactions that will not be authorised.

To perform an abort you just need to call the abort method on the transaction:

.. code-block:: bash

    >>> transaction.abort()

In the event of an abort failing always catch the error and always check the status:

.. code-block:: python

    from sagepaypi.exceptions import InvalidTransactionStatus

    try:
        transaction.abort()
        if transaction.instruction == 'abort':
            # Yay!!
    except InvalidTransactionStatus:
        # this will be thrown if the original transaction is
        # not in a state that an abort can even be attempted.
        # ie it was not successful in the first place, it's a not a deferred payment,
        # its older than 30 days or has a instruction already created.