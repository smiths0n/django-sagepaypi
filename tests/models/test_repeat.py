import mock

from sagepaypi.exceptions import InvalidTransactionStatus
from sagepaypi.models import Transaction

from tests.mocks import payment_created_response
from tests.test_case import AppTestCase


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

    def test_error__for_deferred_not_released(self):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.transaction_id = 'dummy-transaction-id'
        transaction.status_code = '0000'
        transaction.type = 'Deferred'
        transaction.instruction = ''

        with self.assertRaises(InvalidTransactionStatus) as e:
            transaction.repeat()

        self.assertEqual(
            e.exception.args[0],
            'can only repeat a successful Payment, Repeat or a released Deferred transaction'
        )

    def test_error__for_deferred_abort(self):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.transaction_id = 'dummy-transaction-id'
        transaction.status_code = '0000'
        transaction.type = 'Deferred'
        transaction.instruction = 'abort'

        with self.assertRaises(InvalidTransactionStatus) as e:
            transaction.repeat()

        self.assertEqual(
            e.exception.args[0],
            'can only repeat a successful Payment, Repeat or a released Deferred transaction'
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
    def test_successful_deferred__release(self, mock_post):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.transaction_id = 'dummy-transaction-id'
        transaction.type = 'Deferred'
        transaction.instruction = 'release'
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
