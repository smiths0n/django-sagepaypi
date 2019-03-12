import mock

from sagepaypi.exceptions import InvalidTransactionStatus

from sagepaypi.models import Transaction
from tests.mocks import gone_response, auth_success_response, outcome_live_response
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

    @mock.patch('sagepaypi.gateway.default_gateway')
    def test_error__500_response(self, mock_gateway):
        mock_gateway.get_3d_secure_status.return_value = gone_response()
        mock_gateway.get_transaction_outcome.return_value = gone_response()

        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.transaction_id = 'dummy-transaction-id'
        transaction.get_3d_secure_status('pares-data')

        # not expected
        self.assertIsNone(transaction.secure_status)

    @mock.patch('sagepaypi.gateway.default_gateway')
    def test_outcome__success(self, mock_gateway):
        mock_gateway.get_3d_secure_status.return_value = auth_success_response()
        mock_gateway.get_transaction_outcome.return_value = outcome_live_response()

        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.transaction_id = 'dummy-transaction-id'
        transaction.get_3d_secure_status('pares-data')

        json = auth_success_response().json()

        # expected
        self.assertEqual(transaction.pares, 'pares-data')
        self.assertEqual(transaction.secure_status, json['status'])
