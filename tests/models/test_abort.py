from datetime import timedelta
import dateutil
import mock

from sagepaypi.exceptions import InvalidTransactionStatus
from sagepaypi.models import Transaction

from tests.mocks import abort_instruction_transaction
from tests.test_case import AppTestCase


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
