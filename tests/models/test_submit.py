import mock

from sagepaypi.models import Transaction
from tests.mocks import (
    gone_response,
    malformed_response,
    payment_created_response,
    transaction_3d_auth_response,
)
from tests.test_case import AppTestCase


class TestSubmitTransaction(AppTestCase):
    fixtures = ['tests/fixtures/test']

    @mock.patch('sagepaypi.gateway.default_gateway')
    def test_submit_transaction__success(self, mock_gateway):
        mock_gateway.submit_transaction.return_value = payment_created_response()
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.submit_transaction()

        json = payment_created_response().json()

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

    @mock.patch('sagepaypi.gateway.default_gateway')
    def test_submit_transaction__requires_3d_auth(self, mock_gateway):
        mock_gateway.submit_transaction.return_value = transaction_3d_auth_response()

        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.submit_transaction()

        json = transaction_3d_auth_response().json()

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

    @mock.patch('sagepaypi.gateway.default_gateway')
    def test_submit_transaction__bad_response(self, mock_gateway):
        mock_gateway.submit_transaction.return_value = malformed_response()

        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.submit_transaction()

        json = malformed_response().json()

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

    @mock.patch('sagepaypi.gateway.default_gateway')
    def test_submit_transaction__500_response(self, mock_gateway):
        mock_gateway.submit_transaction.return_value = gone_response()

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
