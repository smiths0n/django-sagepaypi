from datetime import datetime, timezone
import dateutil
import uuid

from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import models
from django.db.models.manager import BaseManager
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.translation import ugettext_lazy as _

import pycountry

from sagepaypi.exceptions import InvalidTransactionStatus
from sagepaypi.gateway import SagepayHttpResponse
from sagepaypi.constants import TRANSACTION_TYPE_CHOICES
from sagepaypi.tokens import default_token_generator


class TransactionQuerySet(models.QuerySet):
    """ Custom queryset """

    pass


class TransactionManager(BaseManager.from_queryset(TransactionQuerySet)):
    """ Custom manager """

    def get_for_token(self, tidb64, token):
        transaction = None
        try:
            tid = urlsafe_base64_decode(tidb64).decode()
            transaction = Transaction.objects.get(pk=tid)
            if not default_token_generator.check_token(transaction, token):
                transaction = None
        except (TypeError, ValueError, OverflowError, ObjectDoesNotExist, ValidationError):
            pass

        return transaction


class Transaction(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True
    )
    created_at = models.DateTimeField(
        _('Created at'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('Updated at'),
        auto_now=True
    )
    type = models.CharField(
        _('Type'),
        max_length=8,
        choices=TRANSACTION_TYPE_CHOICES,
        help_text=_('Type of transaction, e.g "Payment".')
    )
    card_identifier = models.ForeignKey(
        'sagepaypi.CardIdentifier',
        verbose_name=_('Card identifier'),
        on_delete=models.PROTECT,
        related_name='transactions',
        help_text=_('The card identifier used for the transaction.')
    )
    vendor_tx_code = models.CharField(
        _('Vendor tx code'),
        max_length=40,
        unique=True,
        default=uuid.uuid4,
        help_text=_('The unique vendor tx code used for the transaction.')
    )
    amount = models.IntegerField(
        _('Amount'),
        help_text=_('The amount charged in the smallest currency unit. e.g 100 pence to charge £1.00.')
    )
    currency = models.CharField(
        _('Currency'),
        max_length=3,
        help_text=_('Currency code of the transaction, e.g "GBP = Pounds Sterling".')
    )
    description = models.TextField(
        _('Description'),
        help_text=_('Description used against the transaction on Sage Pay.')
    )
    status_code = models.CharField(
        _('Status code'),
        max_length=4,
        null=True,
        blank=True,
        help_text=_('The current status code of the transaction on Sage Pay.')
    )
    status = models.CharField(
        _('Status'),
        max_length=50,
        null=True,
        blank=True,
        help_text=_('The current status of the transaction on Sage Pay.')
    )
    status_detail = models.CharField(
        _('Status detail'),
        max_length=255,
        null=True,
        blank=True,
        help_text=_('The current status detail of the transaction on Sage Pay.')
    )
    transaction_id = models.CharField(
        _('Transaction id'),
        max_length=36,
        null=True,
        blank=True,
        help_text=_('The transaction id on Sage Pay.')
    )
    retrieval_reference = models.CharField(
        _('Retrieval reference'),
        max_length=20,
        null=True,
        blank=True,
        help_text=_(
            'Sage Pay unique Authorisation Code for a successfully authorised transaction. '
            'Only present if status is Ok.'
        )
    )
    bank_authorisation_code = models.CharField(
        _('Bank authorisation code'),
        max_length=20,
        null=True,
        blank=True,
        help_text=_('The authorisation code returned from the merchant bank.')
    )
    acs_url = models.URLField(
        _('Acs url'),
        null=True,
        blank=True,
        help_text=_('The url to redirect to for a transaction that requires 3-D authentication.')
    )
    pareq = models.TextField(
        _('Pareq'),
        null=True,
        blank=True,
        help_text=_(
            'A Base64 encoded, encrypted message that contains the transaction details. '
            'This needs to be passed to the issuing bank as part of the 3-D Secure authentication.'
        )
    )
    pares = models.TextField(
        _('Pares'),
        null=True,
        blank=True,
        help_text=_(
            'A Base64 encoded, encrypted message sent back by the issuing bank to your TermUrl '
            'at the end of the 3-D Secure authentication process.'
        )
    )
    secure_status = models.CharField(
        _('Secure status'),
        max_length=50,
        null=True,
        blank=True,
        help_text=_('The 3-D Secure status of the transaction, if applied.')
    )
    instruction = models.CharField(
        _('Instruction'),
        max_length=10,
        null=True,
        blank=True,
        db_index=True,
        help_text=_('The instruction to either release, abort or void a transaction.')
    )
    instruction_created_at = models.DateTimeField(
        _('Instruction created at'),
        null=True,
        blank=True,
        help_text=_('The date in which the instruction was requested.')
    )
    reference_transaction = models.ForeignKey(
        'self',
        verbose_name=_('Reference transaction'),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text=_('The referring transaction used for a "Repeat" or "Refund" transaction.')
    )

    objects = TransactionManager()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return str(self.pk)

    def clean(self):
        """
        Includes additional validation to ensure:

        - currency is a valid currency code
        - reference_transaction is present when the type is either a "Repeat" or "Refund".
        """

        errors = {}

        if not pycountry.currencies.get(alpha_3=self.currency):
            errors['currency'] = _('Requires a valid currency.')

        if self.type == 'Repeat' and not self.reference_transaction:
            errors['reference_transaction'] = _('Required for a "Repeat" transaction.')

        if self.type == 'Refund' and not self.reference_transaction:
            errors['reference_transaction'] = _('Required for a "Refund" transaction.')

        if errors:
            raise ValidationError(errors)

    def get_tokens(self):
        """
        Get transaction tokens.

        Can be used in urls to get the transaction. It will be valid for the
        number of days defined in SAGEPAYPI_TOKEN_URL_DAYS_VALID and is only valid until
        the transaction has been updated.

        Primarily used to generate a TermURL that Sage Pay will redirect to after 3d secure login.

        :returns: Returns a tuple of base64 encoded string of the transaction id and a token that
            will be valid for limited period for this transaction, similar to django's password reset token.
        """

        tidb64 = urlsafe_base64_encode(force_bytes(self.pk))
        token = default_token_generator.make_token(self)
        return tidb64, token

    def submit_transaction(self):
        """
        Submit's the transaction to Sage Pay and saves the response.
        """

        new_transaction = {
            'transactionType': self.type,
            'vendorTxCode': str(self.vendor_tx_code),
            'amount': self.amount,
            'currency': self.currency,
            'description': self.description
        }

        if self.type in ['Payment', 'Deferred']:
            new_transaction.update({
                'paymentMethod': {
                    'card': {
                        'merchantSessionKey': self.card_identifier.merchant_session_key,
                        'cardIdentifier': self.card_identifier.card_identifier
                    }
                },
                'customerFirstName': self.card_identifier.first_name,
                'customerLastName': self.card_identifier.last_name,
                'billingAddress': self.card_identifier.billing_address
            })

        else:
            new_transaction.update({
                'referenceTransactionId': self.reference_transaction.transaction_id
            })

        from sagepaypi.gateway import default_gateway

        response = default_gateway.submit_transaction(new_transaction)

        data = response.json()

        self.responses.create(step='submit_transaction', status_code=response.status_code, data=data)

        if response.status_code in [
            SagepayHttpResponse.HTTP_200,
            SagepayHttpResponse.HTTP_201,
            SagepayHttpResponse.HTTP_202,
            SagepayHttpResponse.HTTP_204
        ]:
            self.status_code = data.get('statusCode')
            self.status = data.get('status')
            self.status_detail = data.get('statusDetail')
            self.transaction_id = data.get('transactionId')
            self.retrieval_reference = data.get('retrievalReference')
            self.bank_authorisation_code = data.get('bankAuthorisationCode')
            self.pareq = data.get('paReq')
            self.acs_url = data.get('acsUrl')

        else:
            self.status = data.get('status')
            self.status_code = data.get('statusCode')

        self.save()

    submit_transaction.alters_data = True

    def get_3d_secure_status(self, pares):
        """
        Get's the result of the 3d secure login to Sage Pay.

        User must have already been redirected to Sage Pay to login and redirected back to the site.
        If the cardholder was able to successfully authenticate, the status will be 'Authenticated'.

        :param pares: A Base64 encoded, encrypted message sent back by the issuing bank to your TermUrl
            at the end of the 3-D Secure authentication process. See Sage Pay docs.

        :raises InvalidTransactionStatus: if the transaction is not in a valid state to process.
        """

        if not self.transaction_id:
            err = _('transaction is missing a transaction_id')
            raise InvalidTransactionStatus(err)

        self.pares = pares

        from sagepaypi.gateway import default_gateway

        post_data = {'paRes': self.pares}
        response = default_gateway.get_3d_secure_status(self.transaction_id, post_data)

        data = response.json()

        self.responses.create(step='get_3d_secure_status', status_code=response.status_code, data=data)

        if response.status_code == SagepayHttpResponse.HTTP_201:
            self.secure_status = data.get('status')

        self.save()
        self.get_transaction_outcome()

    get_3d_secure_status.alters_data = True

    def get_transaction_outcome(self):
        """
        Get's the outcome of a transaction from Sage Pay.

        Must have a valid transaction_id to process.

        :raises InvalidTransactionStatus: if the transaction is not in a valid state to process.
        """

        if not self.transaction_id:
            err = _('transaction is missing a transaction_id')
            raise InvalidTransactionStatus(err)

        from sagepaypi.gateway import default_gateway

        response = default_gateway.get_transaction_outcome(self.transaction_id)

        data = response.json()

        self.responses.create(step='get_transaction_outcome', status_code=response.status_code, data=data)

        if response.status_code == SagepayHttpResponse.HTTP_200:
            self.status_code = data.get('statusCode')
            self.status = data.get('status')
            self.status_detail = data.get('statusDetail')
            self.transaction_id = data.get('transactionId')
            self.retrieval_reference = data.get('retrievalReference')
            self.bank_authorisation_code = data.get('bankAuthorisationCode')

        self.save()

    get_transaction_outcome.alters_data = True

    def release(self, amount=None):
        """
        Release a deferred transaction.

        This has to be completed within 30 days of the creation date.
        You can only either request a release or abort of a deferred payment once.
        After 30 days Sage Pay will auto abort the transaction and you will be required
        to make another transaction with the card holder if you still require the funds.

        :param amount: Specify the amount if you do not want to release the full amount.

        :raises InvalidTransactionStatus: if the transaction is not in a valid state to process.
        """

        if not self.transaction_id:
            err = _('transaction is missing a transaction_id')
            raise InvalidTransactionStatus(err)

        if not (self.successful and self.type == 'Deferred'):
            err = _('can only release a deferred transaction')
            raise InvalidTransactionStatus(err)

        if self.instruction:
            err = _('cannot release a transaction with an existing instruction')
            raise InvalidTransactionStatus(err)

        if self.days_since_created > 30:
            err = _('can only release a transaction that was created within 30 days')
            raise InvalidTransactionStatus(err)

        if amount and amount > self.amount:
            err = _('can only release up to the original amount and no more')
            raise InvalidTransactionStatus(err)

        from sagepaypi.gateway import default_gateway

        post_data = {
            'instructionType': 'release',
            'amount': amount or self.amount
        }
        response = default_gateway.submit_transaction_instruction(self.transaction_id, post_data)

        data = response.json()

        self.responses.create(step='release', status_code=response.status_code, data=data)

        if response.status_code == SagepayHttpResponse.HTTP_201:
            self.instruction = data['instructionType']
            self.instruction_created_at = dateutil.parser.parse(data['date'])

        self.save()

    release.alters_data = True

    def abort(self):
        """
        Abort a deferred transaction.

        This has to be completed within 30 days of the creation date.
        You can only either request a release or abort of a deferred payment once.
        After 30 days Sage Pay will auto abort the transaction if no instruction has been made.

        :raises InvalidTransactionStatus: if the transaction is not in a valid state to process.
        """

        if not self.transaction_id:
            err = _('transaction is missing a transaction_id')
            raise InvalidTransactionStatus(err)

        if not self.successful:
            err = _('cannot abort an unsuccessful transaction')
            raise InvalidTransactionStatus(err)

        if not self.type == 'Deferred':
            err = _('can only abort a deferred transaction')
            raise InvalidTransactionStatus(err)

        if self.days_since_created > 30:
            err = _('can only abort a transaction that was created within 30 days')
            raise InvalidTransactionStatus(err)

        from sagepaypi.gateway import default_gateway

        post_data = {
            'instructionType': 'abort',
            'amount': self.amount
        }
        response = default_gateway.submit_transaction_instruction(self.transaction_id, post_data)

        data = response.json()

        self.responses.create(step='abort', status_code=response.status_code, data=data)

        if response.status_code == SagepayHttpResponse.HTTP_201:
            self.instruction = data['instructionType']
            self.instruction_created_at = dateutil.parser.parse(data['date'])

            self.save()
            self.get_transaction_outcome()

    abort.alters_data = True

    def void(self):
        """
        Void a transaction.

        This has to be completed on the same calendar day as the original transaction.
        You can only void a "Payment" or "Refund" transaction that has an Ok status.

        :raises InvalidTransactionStatus: if the transaction is not in a valid state to process.
        """

        if not self.transaction_id:
            err = _('transaction is missing a transaction_id')
            raise InvalidTransactionStatus(err)

        if not self.successful:
            err = _('cannot void an unsuccessful transaction')
            raise InvalidTransactionStatus(err)

        if self.type not in ['Payment', 'Refund']:
            err = _('can only void a payment or refund')
            raise InvalidTransactionStatus(err)

        if self.days_since_created > 0:
            err = _('can only void transaction that was created today')
            raise InvalidTransactionStatus(err)

        from sagepaypi.gateway import default_gateway

        post_data = {'instructionType': 'void'}
        response = default_gateway.submit_transaction_instruction(self.transaction_id, post_data)

        data = response.json()

        self.responses.create(step='void', status_code=response.status_code, data=data)

        if response.status_code == SagepayHttpResponse.HTTP_201:
            self.instruction = data['instructionType']
            self.instruction_created_at = dateutil.parser.parse(data['date'])

            self.save()
            self.get_transaction_outcome()

    void.alters_data = True

    def repeat(self, **kwargs):
        """
        Repeat a transaction

        To repeat a transaction it must have been a successful
        Payment, Repeat or a released Deferred transaction and not void.

        :param kwargs: Pass any defaults for the repeat transaction,
            ie {'amount': 1, 'description': 'Repeat of payment'}

        :raises InvalidTransactionStatus: if the transaction is not in a valid state to process.

        :returns: the new transaction instance.
        """

        if not self.transaction_id:
            err = _('transaction is missing a transaction_id')
            raise InvalidTransactionStatus(err)

        if not self.successful:
            err = _('cannot repeat an unsuccessful transaction')
            raise InvalidTransactionStatus(err)

        if self.type not in ['Payment', 'Repeat', 'Deferred']:
            err = _('can only repeat a successful Payment, Repeat or a released Deferred transaction')
            raise InvalidTransactionStatus(err)

        if self.type == 'Deferred' and self.instruction != 'release':
            err = _('can only repeat a successful Payment, Repeat or a released Deferred transaction')
            raise InvalidTransactionStatus(err)

        if self.instruction == 'void':
            err = _('cannot repeat a void transaction')
            raise InvalidTransactionStatus(err)

        repeat = Transaction(**kwargs)

        # must be set to original transaction details
        repeat.type = 'Repeat'
        repeat.card_identifier = self.card_identifier
        repeat.reference_transaction = self

        # can be changeable
        repeat.currency = repeat.currency or self.currency
        repeat.amount = repeat.amount or self.amount
        repeat.description = repeat.description or self.description

        # clean, save and submit the transaction
        repeat.full_clean()
        repeat.save()
        repeat.submit_transaction()

        return repeat

    repeat.alters_data = True

    def refund(self, **kwargs):
        """
        Refund a transaction

        You can perform multiple refunds on a single transaction as long
        as the sum of the amounts does not exceed the original transaction.

        :param kwargs: Pass any defaults for the refund transaction,
            ie {'amount': 1, 'description': 'Refund of payment'}

        :raises InvalidTransactionStatus: if the transaction is not in a valid state to process.

        :returns: the new transaction instance.
        """

        if not self.transaction_id:
            err = _('transaction is missing a transaction_id')
            raise InvalidTransactionStatus(err)

        if not self.successful:
            err = _('cannot refund an unsuccessful transaction')
            raise InvalidTransactionStatus(err)

        if self.instruction == 'void':
            err = _('cannot refund a void transaction')
            raise InvalidTransactionStatus(err)

        if self.type == 'Deferred' and not self.instruction == 'release':
            err = _('cannot refund a deferred transaction that is not released')
            raise InvalidTransactionStatus(err)

        refund = Transaction(**kwargs)

        # must be set to original transaction details
        refund.type = 'Refund'
        refund.card_identifier = self.card_identifier
        refund.reference_transaction = self
        refund.currency = self.currency

        # can be changeable
        refund.amount = refund.amount or self.amount
        refund.description = refund.description or self.description

        # clean, save and submit the transaction
        refund.full_clean()
        refund.save()
        refund.submit_transaction()

        return refund

    refund.alters_data = True

    @property
    def days_since_created(self):
        return (self.utc_now() - self.created_at).days

    @property
    def requires_3d_secure(self):
        return self.status_code == '2007'

    @property
    def successful(self):
        return self.status_code == '0000'

    @staticmethod
    def utc_now():
        return datetime.now(timezone.utc)


class TransactionResponse(models.Model):
    transaction = models.ForeignKey(
        'sagepaypi.Transaction',
        verbose_name=_('Transaction'),
        on_delete=models.CASCADE,
        related_name='responses',
    )
    created_at = models.DateTimeField(
        _('Created at'),
        auto_now_add=True
    )
    step = models.CharField(
        _('Step'),
        max_length=100
    )
    status_code = models.IntegerField(
        _('Status code'),
        null=True
    )
    data = JSONField(
        _('Data'),
        default=dict
    )

    class Meta:
        ordering = ['-created_at']
