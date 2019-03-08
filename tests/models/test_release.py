from datetime import timedelta
import dateutil
import mock

from sagepaypi.exceptions import InvalidTransactionStatus
from sagepaypi.models import Transaction

from tests.mocks import release_instruction_transaction
from tests.test_case import AppTestCase


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

    def test_error__instruction_amount_greater_than_original(self):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.transaction_id = 'dummy-transaction-id'
        transaction.type = 'Deferred'
        transaction.status_code = '0000'
        transaction.amount = 100
        transaction.created_at = transaction.utc_now() - timedelta(days=15)

        with self.assertRaises(InvalidTransactionStatus) as e:
            transaction.release(amount=101)

        self.assertEqual(
            e.exception.args[0],
            'can only release up to the original amount and no more'
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

    @mock.patch('sagepaypi.gateway.requests.post', side_effect=release_instruction_transaction)
    def test_successful_instruction__with_amount(self, mock_post):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.transaction_id = 'dummy-transaction-id'
        transaction.type = 'Deferred'
        transaction.status_code = '0000'
        transaction.amount = 100
        transaction.created_at = transaction.utc_now() - timedelta(days=15)

        transaction.release(amount=99)

        json = mock_post().json()

        # expected
        self.assertEqual(transaction.instruction, json['instructionType'])
        self.assertEqual(transaction.instruction_created_at, dateutil.parser.parse(json['date']))
