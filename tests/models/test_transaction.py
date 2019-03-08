from datetime import timedelta
import dateutil
import mock
import uuid

from django.core.exceptions import ValidationError
from django.db import models
from sagepaypi.constants import get_transaction_type_choices, get_currency_choices
from sagepaypi.exceptions import InvalidTransactionStatus

from sagepaypi.models import CardIdentifier, Transaction
from tests.mocks import (
    abort_instruction_transaction,
    gone_response,
    malformed_response,
    payment_created_response,
    refund_created_response,
    release_instruction_transaction,
    transaction_3d_auth_response,
    transaction_outcome_response,
    void_instruction_transaction
)
from tests.test_case import AppTestCase


class TestManager(AppTestCase):
    fixtures = ['tests/fixtures/test']

    def test_get_for_token__gets_transaction(self):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        tidb64, token = transaction.get_tokens()
        transaction_from_manager = Transaction.objects.get_for_token(tidb64, token)
        self.assertEqual(transaction, transaction_from_manager)

    def test_get_for_token__invalid_args(self):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        tidb64, token = transaction.get_tokens()
        self.assertIsNone(Transaction.objects.get_for_token('invalid', token))
        self.assertIsNone(Transaction.objects.get_for_token(tidb64, 'invalid'))
        self.assertIsNone(Transaction.objects.get_for_token('invalid', 'invalid'))


class TestModel(AppTestCase):

    # fields

    def test_id(self):
        field = self.get_field(Transaction, 'id')
        self.assertModelField(field, models.UUIDField)
        self.assertFalse(field.editable)
        self.assertTrue(field.primary_key)

    def test_created_at(self):
        field = self.get_field(Transaction, 'created_at')
        self.assertModelField(field, models.DateTimeField, blank=True)
        self.assertTrue(field.auto_now_add)

    def test_updated_at(self):
        field = self.get_field(Transaction, 'updated_at')
        self.assertModelField(field, models.DateTimeField, blank=True)
        self.assertTrue(field.auto_now)

    def test_type(self):
        field = self.get_field(Transaction, 'type')
        self.assertModelField(field, models.CharField)
        self.assertEqual(field.max_length, 8)
        self.assertEqual(field.choices, get_transaction_type_choices())

    def test_card_identifier(self):
        field = self.get_field(Transaction, 'card_identifier')
        self.assertModelPKField(field, CardIdentifier, on_delete=models.PROTECT, related_name='transactions')

    def test_vendor_tx_code(self):
        field = self.get_field(Transaction, 'vendor_tx_code')
        self.assertModelField(field, models.CharField, default=uuid.uuid4)
        self.assertEqual(field.max_length, 40)
        self.assertTrue(field.unique)

    def test_amount(self):
        field = self.get_field(Transaction, 'amount')
        self.assertModelField(field, models.IntegerField)

    def test_currency(self):
        field = self.get_field(Transaction, 'currency')
        self.assertModelField(field, models.CharField)
        self.assertEqual(field.max_length, 3)
        self.assertEqual(field.choices, get_currency_choices())

    def test_description(self):
        field = self.get_field(Transaction, 'description')
        self.assertModelField(field, models.TextField)

    def test_status_code(self):
        field = self.get_field(Transaction, 'status_code')
        self.assertModelField(field, models.CharField, True, True)
        self.assertEqual(field.max_length, 4)

    def test_status(self):
        field = self.get_field(Transaction, 'status')
        self.assertModelField(field, models.CharField, True, True)
        self.assertEqual(field.max_length, 50)

    def test_status_detail(self):
        field = self.get_field(Transaction, 'status_detail')
        self.assertModelField(field, models.CharField, True, True)
        self.assertEqual(field.max_length, 255)

    def test_transaction_id(self):
        field = self.get_field(Transaction, 'transaction_id')
        self.assertModelField(field, models.CharField, True, True)
        self.assertEqual(field.max_length, 36)

    def test_retrieval_reference(self):
        field = self.get_field(Transaction, 'retrieval_reference')
        self.assertModelField(field, models.CharField, True, True)
        self.assertEqual(field.max_length, 20)

    def test_bank_authorisation_code(self):
        field = self.get_field(Transaction, 'bank_authorisation_code')
        self.assertModelField(field, models.CharField, True, True)
        self.assertEqual(field.max_length, 20)

    def test_acs_url(self):
        field = self.get_field(Transaction, 'acs_url')
        self.assertModelField(field, models.URLField, True, True)

    def test_pareq(self):
        field = self.get_field(Transaction, 'pareq')
        self.assertModelField(field, models.TextField, True, True)

    def test_pares(self):
        field = self.get_field(Transaction, 'pares')
        self.assertModelField(field, models.TextField, True, True)

    def test_secure_status(self):
        field = self.get_field(Transaction, 'secure_status')
        self.assertModelField(field, models.CharField, True, True)
        self.assertEqual(field.max_length, 50)

    def test_instruction(self):
        field = self.get_field(Transaction, 'instruction')
        self.assertModelField(field, models.CharField, True, True)
        self.assertEqual(field.max_length, 10)

    def test_instruction_created_at(self):
        field = self.get_field(Transaction, 'instruction_created_at')
        self.assertModelField(field, models.DateTimeField, True, True)

    def test_reference_transaction(self):
        field = self.get_field(Transaction, 'reference_transaction')
        self.assertModelPKField(field, Transaction, models.CASCADE, True, True)

    # meta

    def test_ordering(self):
        self.assertEqual(Transaction._meta.ordering, ['-created_at'])

    # properties

    def test_str(self):
        pk = uuid.uuid4()
        self.assertEqual(Transaction(pk=pk).__str__(), str(pk))

    def test_deferred(self):
        self.assertTrue(
            Transaction(status_code='0000', type='Deferred').deferred
        )
        self.assertFalse(
            Transaction(status_code='1234', type='Deferred').deferred
        )
        self.assertFalse(
            Transaction(status_code='0000', type='Payment').deferred
        )

    def test_requires_3d_secure(self):
        self.assertTrue(
            Transaction(status_code='2007').requires_3d_secure
        )
        self.assertFalse(
            Transaction(status_code='1234').requires_3d_secure
        )

    def test_successful(self):
        self.assertTrue(
            Transaction(status_code='0000').successful
        )
        self.assertFalse(
            Transaction(status_code='1234').successful
        )

    # validation

    def test_clean(self):
        with self.assertRaises(ValidationError) as e:
            Transaction(type='Repeat').clean()

        self.assertEqual(
            e.exception.args[0],
            {'reference_transaction': 'Required for a "Repeat" transaction.'}
        )

        with self.assertRaises(ValidationError) as e:
            Transaction(type='Refund').clean()

        self.assertEqual(
            e.exception.args[0],
            {'reference_transaction': 'Required for a "Refund" transaction.'}
        )


class TestSubmitTransaction(AppTestCase):
    fixtures = ['tests/fixtures/test']

    @mock.patch('sagepaypi.gateway.requests.post', side_effect=payment_created_response)
    def test_submit_transaction__success(self, mock_post):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.submit_transaction()

        json = mock_post().json()

        # expected
        self.assertEqual(transaction.status_code, json['statusCode'])
        self.assertEqual(transaction.status, json['status'])
        self.assertEqual(transaction.status_detail, json['statusDetail'])
        self.assertEqual(transaction.transaction_id, json['transactionId'])
        self.assertEqual(transaction.retrieval_reference, json['retrievalReference'])
        self.assertEqual(transaction.bank_authorisation_code, json['bankAuthorisationCode'])

        # not expected
        self.assertIsNone(transaction.pareq)
        self.assertIsNone(transaction.acs_url)

    @mock.patch('sagepaypi.gateway.requests.post', side_effect=transaction_3d_auth_response)
    def test_submit_transaction__requires_3d_auth(self, mock_post):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.submit_transaction()

        json = mock_post().json()

        # expected
        self.assertEqual(transaction.status_code, json['statusCode'])
        self.assertEqual(transaction.status, json['status'])
        self.assertEqual(transaction.status_detail, json['statusDetail'])
        self.assertEqual(transaction.transaction_id, json['transactionId'])
        self.assertEqual(transaction.pareq, json['paReq'])
        self.assertEqual(transaction.acs_url, json['acsUrl'])

        # not expected
        self.assertIsNone(transaction.retrieval_reference)
        self.assertIsNone(transaction.bank_authorisation_code)

    @mock.patch('sagepaypi.gateway.requests.post', side_effect=malformed_response)
    def test_submit_transaction__bad_response(self, mock_post):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.submit_transaction()

        json = mock_post().json()

        # expected
        self.assertEqual(transaction.status_code, json['statusCode'])
        self.assertEqual(transaction.status, json['status'])

        # not expected
        self.assertIsNone(transaction.status_detail)
        self.assertIsNone(transaction.transaction_id)
        self.assertIsNone(transaction.retrieval_reference)
        self.assertIsNone(transaction.bank_authorisation_code)
        self.assertIsNone(transaction.pareq)
        self.assertIsNone(transaction.acs_url)

    @mock.patch('sagepaypi.gateway.requests.post', side_effect=gone_response)
    def test_submit_transaction__500_response(self, mock_post):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.submit_transaction()

        # not expected
        self.assertIsNone(transaction.status_code)
        self.assertIsNone(transaction.status)
        self.assertIsNone(transaction.status_detail)
        self.assertIsNone(transaction.transaction_id)
        self.assertIsNone(transaction.retrieval_reference)
        self.assertIsNone(transaction.bank_authorisation_code)
        self.assertIsNone(transaction.pareq)
        self.assertIsNone(transaction.acs_url)


class TestTransactionOutcome(AppTestCase):
    fixtures = ['tests/fixtures/test']

    def test_error__no_transaction_id(self):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')

        with self.assertRaises(InvalidTransactionStatus) as e:
            transaction.get_transaction_outcome()

        self.assertEqual(
            e.exception.args[0],
            'transaction is missing a transaction_id'
        )

    @mock.patch('sagepaypi.gateway.requests.get', side_effect=gone_response)
    def test_error__500_response(self, mock_get):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.transaction_id = 'dummy-transaction-id'
        transaction.get_transaction_outcome()

        # not expected
        self.assertIsNone(transaction.status_code)
        self.assertIsNone(transaction.status)
        self.assertIsNone(transaction.status_detail)
        self.assertIsNone(transaction.retrieval_reference)
        self.assertIsNone(transaction.bank_authorisation_code)
        self.assertIsNone(transaction.pareq)
        self.assertIsNone(transaction.acs_url)

    @mock.patch('sagepaypi.gateway.requests.get', side_effect=transaction_outcome_response)
    def test_outcome__success(self, mock_get):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.transaction_id = 'dummy-transaction-id'
        transaction.get_transaction_outcome()

        json = mock_get().json()

        # expected
        self.assertEqual(transaction.status_code, json['statusCode'])
        self.assertEqual(transaction.status, json['status'])
        self.assertEqual(transaction.status_detail, json['statusDetail'])
        self.assertEqual(transaction.transaction_id, json['transactionId'])
        self.assertEqual(transaction.retrieval_reference, json['retrievalReference'])
        self.assertEqual(transaction.bank_authorisation_code, json['bankAuthorisationCode'])


class TestReleaseTransaction(AppTestCase):
    fixtures = ['tests/fixtures/test']

    def test_error__no_transaction_id(self):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')

        with self.assertRaises(InvalidTransactionStatus) as e:
            transaction.release()

        self.assertEqual(
            e.exception.args[0],
            'transaction is missing a transaction_id'
        )

    def test_error__not_deferred(self):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.transaction_id = 'dummy-transaction-id'
        transaction.type = 'Payment'
        transaction.status_code = '0000'

        with self.assertRaises(InvalidTransactionStatus) as e:
            transaction.release()

        self.assertEqual(
            e.exception.args[0],
            'can only release a deferred transaction'
        )

    def test_error__instruction_already_present(self):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.transaction_id = 'dummy-transaction-id'
        transaction.type = 'Deferred'
        transaction.status_code = '0000'

        for instruction in ['release', 'abort']:
            transaction.instruction = instruction

            with self.assertRaises(InvalidTransactionStatus) as e:
                transaction.release()

            self.assertEqual(
                e.exception.args[0],
                'cannot release a transaction with an existing instruction'
            )

    def test_error__instruction_too_late(self):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.transaction_id = 'dummy-transaction-id'
        transaction.type = 'Deferred'
        transaction.status_code = '0000'
        transaction.created_at = transaction.utc_now() - timedelta(days=31)

        with self.assertRaises(InvalidTransactionStatus) as e:
            transaction.release()

        self.assertEqual(
            e.exception.args[0],
            'can only release a transaction that was created within 30 days'
        )

    @mock.patch('sagepaypi.gateway.requests.post', side_effect=release_instruction_transaction)
    def test_successful_instruction(self, mock_post):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.transaction_id = 'dummy-transaction-id'
        transaction.type = 'Deferred'
        transaction.status_code = '0000'
        transaction.created_at = transaction.utc_now() - timedelta(days=15)

        transaction.release()

        json = mock_post().json()

        # expected
        self.assertEqual(transaction.instruction, json['instructionType'])
        self.assertEqual(transaction.instruction_created_at, dateutil.parser.parse(json['date']))


class TestAbortTransaction(AppTestCase):
    fixtures = ['tests/fixtures/test']

    def test_error__no_transaction_id(self):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')

        with self.assertRaises(InvalidTransactionStatus) as e:
            transaction.abort()

        self.assertEqual(
            e.exception.args[0],
            'transaction is missing a transaction_id'
        )

    def test_error__not_deferred(self):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.transaction_id = 'dummy-transaction-id'
        transaction.type = 'Payment'
        transaction.status_code = '0000'

        with self.assertRaises(InvalidTransactionStatus) as e:
            transaction.abort()

        self.assertEqual(
            e.exception.args[0],
            'can only abort a deferred transaction'
        )

    def test_error__instruction_already_present(self):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.transaction_id = 'dummy-transaction-id'
        transaction.type = 'Deferred'
        transaction.status_code = '0000'

        for instruction in ['release', 'abort']:
            transaction.instruction = instruction

            with self.assertRaises(InvalidTransactionStatus) as e:
                transaction.abort()

            self.assertEqual(
                e.exception.args[0],
                'cannot abort a transaction with an existing instruction'
            )

    def test_error__instruction_too_late(self):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.transaction_id = 'dummy-transaction-id'
        transaction.type = 'Deferred'
        transaction.status_code = '0000'
        transaction.created_at = transaction.utc_now() - timedelta(days=31)

        with self.assertRaises(InvalidTransactionStatus) as e:
            transaction.abort()

        self.assertEqual(
            e.exception.args[0],
            'can only abort a transaction that was created within 30 days'
        )

    @mock.patch('sagepaypi.gateway.requests.post', side_effect=abort_instruction_transaction)
    def test_successful_instruction(self, mock_post):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.transaction_id = 'dummy-transaction-id'
        transaction.type = 'Deferred'
        transaction.status_code = '0000'
        transaction.created_at = transaction.utc_now() - timedelta(days=15)

        transaction.abort()

        json = mock_post().json()

        # expected
        self.assertEqual(transaction.instruction, json['instructionType'])
        self.assertEqual(transaction.instruction_created_at, dateutil.parser.parse(json['date']))


class TestVoidTransaction(AppTestCase):
    fixtures = ['tests/fixtures/test']

    def test_error__no_transaction_id(self):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')

        with self.assertRaises(InvalidTransactionStatus) as e:
            transaction.void()

        self.assertEqual(
            e.exception.args[0],
            'transaction is missing a transaction_id'
        )

    def test_error__not_successful(self):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.transaction_id = 'dummy-transaction-id'
        transaction.type = 'Payment'
        transaction.status_code = '9999'

        with self.assertRaises(InvalidTransactionStatus) as e:
            transaction.void()

        self.assertEqual(
            e.exception.args[0],
            'cannot void an unsuccessful transaction'
        )

    def test_error__invalid_type(self):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.transaction_id = 'dummy-transaction-id'
        transaction.status_code = '0000'

        for tr_type in ['Deferred', 'Repeat']:
            transaction.type = tr_type

            with self.assertRaises(InvalidTransactionStatus) as e:
                transaction.void()

            self.assertEqual(
                e.exception.args[0],
                'can only void a payment or refund'
            )

    def test_error__instruction_too_late(self):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.transaction_id = 'dummy-transaction-id'
        transaction.type = 'Payment'
        transaction.status_code = '0000'
        transaction.created_at = transaction.utc_now() - timedelta(days=1)

        with self.assertRaises(InvalidTransactionStatus) as e:
            transaction.void()

        self.assertEqual(
            e.exception.args[0],
            'can only void transaction that was created today'
        )

    @mock.patch('sagepaypi.gateway.requests.post', side_effect=void_instruction_transaction)
    def test_successful_instruction(self, mock_post):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.transaction_id = 'dummy-transaction-id'
        transaction.type = 'Payment'
        transaction.status_code = '0000'
        transaction.created_at = transaction.utc_now()

        transaction.void()

        json = mock_post().json()

        # expected
        self.assertEqual(transaction.instruction, json['instructionType'])
        self.assertEqual(transaction.instruction_created_at, dateutil.parser.parse(json['date']))


class TestRepeatTransaction(AppTestCase):
    fixtures = ['tests/fixtures/test']

    def test_error__no_transaction_id(self):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')

        with self.assertRaises(InvalidTransactionStatus) as e:
            transaction.repeat()

        self.assertEqual(
            e.exception.args[0],
            'transaction is missing a transaction_id'
        )

    def test_error__not_successful(self):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.transaction_id = 'dummy-transaction-id'
        transaction.type = 'Payment'
        transaction.status_code = '9999'

        with self.assertRaises(InvalidTransactionStatus) as e:
            transaction.repeat()

        self.assertEqual(
            e.exception.args[0],
            'cannot repeat an unsuccessful transaction'
        )

    def test_error__card_identifier_not_reusable(self):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.card_identifier.reusable = False
        transaction.card_identifier.save()
        transaction.transaction_id = 'dummy-transaction-id'
        transaction.type = 'Payment'
        transaction.status_code = '0000'

        with self.assertRaises(InvalidTransactionStatus) as e:
            transaction.repeat()

        self.assertEqual(
            e.exception.args[0],
            'cannot repeat a transaction without a reusable card identifier'
        )

    def test_error__void(self):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.transaction_id = 'dummy-transaction-id'
        transaction.type = 'Payment'
        transaction.status_code = '0000'
        transaction.instruction = 'void'

        with self.assertRaises(InvalidTransactionStatus) as e:
            transaction.repeat()

        self.assertEqual(
            e.exception.args[0],
            'cannot repeat a void transaction'
        )

    def test_error__deferred_not_released(self):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.transaction_id = 'dummy-transaction-id'
        transaction.type = 'Deferred'
        transaction.status_code = '0000'

        for instruction in ['', 'abort']:
            transaction.instruction = instruction

            with self.assertRaises(InvalidTransactionStatus) as e:
                transaction.repeat()

            self.assertEqual(
                e.exception.args[0],
                'cannot repeat a deferred transaction that is not released'
            )

    def test_error__refund(self):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.transaction_id = 'dummy-transaction-id'
        transaction.type = 'Refund'
        transaction.status_code = '0000'

        with self.assertRaises(InvalidTransactionStatus) as e:
            transaction.repeat()

        self.assertEqual(
            e.exception.args[0],
            'cannot repeat a refund transaction'
        )

    @mock.patch('sagepaypi.gateway.requests.post', side_effect=payment_created_response)
    def test_successful_repeat__payment(self, mock_post):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.transaction_id = 'dummy-transaction-id'
        transaction.type = 'Payment'
        transaction.status_code = '0000'

        repeat = transaction.repeat()

        json = mock_post().json()

        # expected
        self.assertEqual(repeat.type, 'Repeat')
        self.assertEqual(repeat.reference_transaction, transaction)
        self.assertEqual(repeat.amount, transaction.amount)
        self.assertEqual(repeat.description, transaction.description)

        self.assertEqual(repeat.status_code, json['statusCode'])
        self.assertEqual(repeat.status, json['status'])
        self.assertEqual(repeat.status_detail, json['statusDetail'])
        self.assertEqual(repeat.transaction_id, json['transactionId'])
        self.assertEqual(repeat.retrieval_reference, json['retrievalReference'])
        self.assertEqual(repeat.bank_authorisation_code, json['bankAuthorisationCode'])

    @mock.patch('sagepaypi.gateway.requests.post', side_effect=payment_created_response)
    def test_successful_repeat__with_kwargs(self, mock_post):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.transaction_id = 'dummy-transaction-id'
        transaction.type = 'Payment'
        transaction.status_code = '0000'

        repeat = transaction.repeat(amount=50, description='repeat payment', vendor_tx_code='repeat-123')

        json = mock_post().json()

        # expected
        self.assertEqual(repeat.type, 'Repeat')
        self.assertEqual(repeat.reference_transaction, transaction)
        self.assertEqual(repeat.amount, 50)
        self.assertEqual(repeat.description, 'repeat payment')
        self.assertEqual(repeat.vendor_tx_code, 'repeat-123')

        self.assertEqual(repeat.status_code, json['statusCode'])
        self.assertEqual(repeat.status, json['status'])
        self.assertEqual(repeat.status_detail, json['statusDetail'])
        self.assertEqual(repeat.transaction_id, json['transactionId'])
        self.assertEqual(repeat.retrieval_reference, json['retrievalReference'])
        self.assertEqual(repeat.bank_authorisation_code, json['bankAuthorisationCode'])

    @mock.patch('sagepaypi.gateway.requests.post', side_effect=payment_created_response)
    def test_successful_repeat__repeat(self, mock_post):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.transaction_id = 'dummy-transaction-id'
        transaction.type = 'Repeat'
        transaction.status_code = '0000'

        repeat = transaction.repeat()

        json = mock_post().json()

        # expected
        self.assertEqual(repeat.type, 'Repeat')
        self.assertEqual(repeat.reference_transaction, transaction)
        self.assertEqual(repeat.amount, transaction.amount)
        self.assertEqual(repeat.description, transaction.description)

        self.assertEqual(repeat.status_code, json['statusCode'])
        self.assertEqual(repeat.status, json['status'])
        self.assertEqual(repeat.status_detail, json['statusDetail'])
        self.assertEqual(repeat.transaction_id, json['transactionId'])
        self.assertEqual(repeat.retrieval_reference, json['retrievalReference'])
        self.assertEqual(repeat.bank_authorisation_code, json['bankAuthorisationCode'])

    @mock.patch('sagepaypi.gateway.requests.post', side_effect=payment_created_response)
    def test_successful_repeat__deferred(self, mock_post):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.transaction_id = 'dummy-transaction-id'
        transaction.type = 'Deferred'
        transaction.status_code = '0000'
        transaction.instruction = 'release'

        repeat = transaction.repeat()

        json = mock_post().json()

        # expected
        self.assertEqual(repeat.type, 'Repeat')
        self.assertEqual(repeat.reference_transaction, transaction)
        self.assertEqual(repeat.amount, transaction.amount)
        self.assertEqual(repeat.description, transaction.description)

        self.assertEqual(repeat.status_code, json['statusCode'])
        self.assertEqual(repeat.status, json['status'])
        self.assertEqual(repeat.status_detail, json['statusDetail'])
        self.assertEqual(repeat.transaction_id, json['transactionId'])
        self.assertEqual(repeat.retrieval_reference, json['retrievalReference'])
        self.assertEqual(repeat.bank_authorisation_code, json['bankAuthorisationCode'])


class TestRefundTransaction(AppTestCase):
    fixtures = ['tests/fixtures/test']

    def test_error__no_transaction_id(self):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')

        with self.assertRaises(InvalidTransactionStatus) as e:
            transaction.refund()

        self.assertEqual(
            e.exception.args[0],
            'transaction is missing a transaction_id'
        )

    def test_error__not_successful(self):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.transaction_id = 'dummy-transaction-id'
        transaction.type = 'Payment'
        transaction.status_code = '9999'

        with self.assertRaises(InvalidTransactionStatus) as e:
            transaction.refund()

        self.assertEqual(
            e.exception.args[0],
            'cannot refund an unsuccessful transaction'
        )

    def test_error__void(self):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.transaction_id = 'dummy-transaction-id'
        transaction.type = 'Payment'
        transaction.status_code = '0000'
        transaction.instruction = 'void'

        with self.assertRaises(InvalidTransactionStatus) as e:
            transaction.refund()

        self.assertEqual(
            e.exception.args[0],
            'cannot refund a void transaction'
        )

    def test_error__deferred_not_released(self):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.transaction_id = 'dummy-transaction-id'
        transaction.type = 'Deferred'
        transaction.status_code = '0000'

        for instruction in ['', 'abort']:
            transaction.instruction = instruction

            with self.assertRaises(InvalidTransactionStatus) as e:
                transaction.refund()

            self.assertEqual(
                e.exception.args[0],
                'cannot refund a deferred transaction that is not released'
            )

    @mock.patch('sagepaypi.gateway.requests.post', side_effect=refund_created_response)
    def test_successful_refund__payment(self, mock_post):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.transaction_id = 'dummy-transaction-id'
        transaction.type = 'Payment'
        transaction.status_code = '0000'

        refund = transaction.refund()

        json = mock_post().json()

        # expected
        self.assertEqual(refund.type, 'Refund')
        self.assertEqual(refund.reference_transaction, transaction)
        self.assertEqual(refund.amount, transaction.amount)
        self.assertEqual(refund.description, transaction.description)

        self.assertEqual(refund.status_code, json['statusCode'])
        self.assertEqual(refund.status, json['status'])
        self.assertEqual(refund.status_detail, json['statusDetail'])
        self.assertEqual(refund.transaction_id, json['transactionId'])
        self.assertEqual(refund.retrieval_reference, json['retrievalReference'])
        self.assertEqual(refund.bank_authorisation_code, json['bankAuthorisationCode'])

    @mock.patch('sagepaypi.gateway.requests.post', side_effect=refund_created_response)
    def test_successful_refund__with_kwargs(self, mock_post):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.transaction_id = 'dummy-transaction-id'
        transaction.type = 'Payment'
        transaction.status_code = '0000'

        refund = transaction.refund(amount=50, description='refund payment', vendor_tx_code='refund-123')

        json = mock_post().json()

        # expected
        self.assertEqual(refund.type, 'Refund')
        self.assertEqual(refund.reference_transaction, transaction)
        self.assertEqual(refund.amount, 50)
        self.assertEqual(refund.description, 'refund payment')
        self.assertEqual(refund.vendor_tx_code, 'refund-123')

        self.assertEqual(refund.status_code, json['statusCode'])
        self.assertEqual(refund.status, json['status'])
        self.assertEqual(refund.status_detail, json['statusDetail'])
        self.assertEqual(refund.transaction_id, json['transactionId'])
        self.assertEqual(refund.retrieval_reference, json['retrievalReference'])
        self.assertEqual(refund.bank_authorisation_code, json['bankAuthorisationCode'])

    @mock.patch('sagepaypi.gateway.requests.post', side_effect=refund_created_response)
    def test_successful_refund_repeat(self, mock_post):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.transaction_id = 'dummy-transaction-id'
        transaction.type = 'Repeat'
        transaction.status_code = '0000'

        refund = transaction.refund()

        json = mock_post().json()

        # expected
        self.assertEqual(refund.type, 'Refund')
        self.assertEqual(refund.reference_transaction, transaction)
        self.assertEqual(refund.amount, transaction.amount)
        self.assertEqual(refund.description, transaction.description)

        self.assertEqual(refund.status_code, json['statusCode'])
        self.assertEqual(refund.status, json['status'])
        self.assertEqual(refund.status_detail, json['statusDetail'])
        self.assertEqual(refund.transaction_id, json['transactionId'])
        self.assertEqual(refund.retrieval_reference, json['retrievalReference'])
        self.assertEqual(refund.bank_authorisation_code, json['bankAuthorisationCode'])
