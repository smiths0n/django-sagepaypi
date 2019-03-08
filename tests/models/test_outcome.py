import mock

from sagepaypi.exceptions import InvalidTransactionStatus

from sagepaypi.models import Transaction
from tests.mocks import gone_response, transaction_outcome_response
from tests.test_case import AppTestCase


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
