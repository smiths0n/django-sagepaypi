import uuid

from django.db import models

from sagepaypi.models import CardIdentifier, Customer
from tests.test_case import AppTestCase


class TestModel(AppTestCase):

    # fields

    def test_id(self):
        field = self.get_field(CardIdentifier, 'id')
        self.assertModelField(field, models.UUIDField)
        self.assertFalse(field.editable)
        self.assertTrue(field.primary_key)

    def test_created_at(self):
        field = self.get_field(CardIdentifier, 'created_at')
        self.assertModelField(field, models.DateTimeField, blank=True)
        self.assertTrue(field.auto_now_add)

    def test_customer(self):
        field = self.get_field(CardIdentifier, 'customer')
        self.assertModelPKField(field, Customer, on_delete=models.CASCADE, related_name='card_identifiers')

    def test_reusable(self):
        field = self.get_field(CardIdentifier, 'reusable')
        self.assertModelField(field, models.BooleanField)
        self.assertFalse(field.default)

    def test_merchant_session_key(self):
        field = self.get_field(CardIdentifier, 'merchant_session_key')
        self.assertModelField(field, models.CharField)
        self.assertEqual(field.max_length, 100)

    def test_card_type(self):
        field = self.get_field(CardIdentifier, 'card_type')
        self.assertModelField(field, models.CharField)
        self.assertEqual(field.max_length, 255)

    def test_last_four_digits(self):
        field = self.get_field(CardIdentifier, 'last_four_digits')
        self.assertModelField(field, models.CharField)
        self.assertEqual(field.max_length, 4)

    def test_expiry_date(self):
        field = self.get_field(CardIdentifier, 'expiry_date')
        self.assertModelField(field, models.CharField)

    def test_card_identifier(self):
        field = self.get_field(CardIdentifier, 'card_identifier')
        self.assertModelField(field, models.CharField)
        self.assertEqual(field.max_length, 100)

    # properties

    def test_str(self):
        pk = uuid.uuid4()
        self.assertEqual(CardIdentifier(pk=pk).__str__(), str(pk))

    def test_display_text(self):
        self.assertEqual(
            CardIdentifier(card_type='Visa', last_four_digits='1234').display_text,
            'Visa (1234)'
        )
