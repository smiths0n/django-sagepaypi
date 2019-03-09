import uuid

from django.core.exceptions import ValidationError
from django.db import models

from sagepaypi.constants import get_transaction_type_choices, get_currency_choices
from sagepaypi.models import CardIdentifier, Transaction

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






