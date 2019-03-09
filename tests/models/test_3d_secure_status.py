import mock

from sagepaypi.exceptions import InvalidTransactionStatus

from sagepaypi.models import Transaction
from tests.mocks import gone_response, transaction_3d_auth_status
from tests.test_case import AppTestCase


class TestTransactionOutcome(AppTestCase):
    fixtures = ['tests/fixtures/test']

    def test_error__no_transaction_id(self):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')

        with self.assertRaises(InvalidTransactionStatus) as e:
            transaction.get_3d_secure_status('pares-data')

        self.assertEqual(
            e.exception.args[0],
            'transaction is missing a transaction_id'
        )

    @mock.patch('sagepaypi.gateway.requests.post', side_effect=gone_response)
    def test_error__500_response(self, mock_post):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.transaction_id = 'dummy-transaction-id'
        transaction.get_3d_secure_status('pares-data')

        # not expected
        self.assertIsNone(transaction.secure_status)

    @mock.patch('sagepaypi.gateway.requests.post', side_effect=transaction_3d_auth_status)
    def test_outcome__success(self, mock_post):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.transaction_id = 'dummy-transaction-id'
        transaction.get_3d_secure_status('pares-data')

        json = mock_post('/3d-secure').json()

        # expected
        self.assertEqual(transaction.pares, 'pares-data')
        self.assertEqual(transaction.secure_status, json['status'])
