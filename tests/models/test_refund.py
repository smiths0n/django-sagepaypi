import mock

from sagepaypi.exceptions import InvalidTransactionStatus
from sagepaypi.models import Transaction

from tests.mocks import refund_created_response
from tests.test_case import AppTestCase


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

    @mock.patch('sagepaypi.gateway.default_gateway')
    def test_successful_refund__payment(self, mock_gateway):
        mock_gateway.submit_transaction.return_value = refund_created_response()

        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.transaction_id = 'dummy-transaction-id'
        transaction.type = 'Payment'
        transaction.status_code = '0000'

        refund = transaction.refund()

        json = refund_created_response().json()

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

    @mock.patch('sagepaypi.gateway.default_gateway')
    def test_successful_refund__with_kwargs(self, mock_gateway):
        mock_gateway.submit_transaction.return_value = refund_created_response()

        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.transaction_id = 'dummy-transaction-id'
        transaction.type = 'Payment'
        transaction.status_code = '0000'

        refund = transaction.refund(amount=50, description='refund payment', vendor_tx_code='refund-123')

        json = refund_created_response().json()

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

    @mock.patch('sagepaypi.gateway.default_gateway')
    def test_successful_refund_repeat(self, mock_gateway):
        mock_gateway.submit_transaction.return_value = refund_created_response()

        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.transaction_id = 'dummy-transaction-id'
        transaction.type = 'Repeat'
        transaction.status_code = '0000'

        refund = transaction.refund()

        json = refund_created_response().json()

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
