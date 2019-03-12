import uuid

from django.core.exceptions import ValidationError
from django.db import models

from sagepaypi.constants import COUNTRY_CHOICES, US_STATE_CHOICES
from sagepaypi.models import CardIdentifier

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

    def test_first_name(self):
        field = self.get_field(CardIdentifier, 'first_name')
        self.assertModelField(field, models.CharField)
        self.assertEqual(field.max_length, 100)

    def test_last_name(self):
        field = self.get_field(CardIdentifier, 'last_name')
        self.assertModelField(field, models.CharField)
        self.assertEqual(field.max_length, 100)

    def test_billing_address_1(self):
        field = self.get_field(CardIdentifier, 'billing_address_1')
        self.assertModelField(field, models.CharField)
        self.assertEqual(field.max_length, 255)

    def test_billing_address_2(self):
        field = self.get_field(CardIdentifier, 'billing_address_2')
        self.assertModelField(field, models.CharField, True, True)
        self.assertEqual(field.max_length, 255)

    def test_billing_city(self):
        field = self.get_field(CardIdentifier, 'billing_city')
        self.assertModelField(field, models.CharField)
        self.assertEqual(field.max_length, 255)

    def test_billing_postal_code(self):
        field = self.get_field(CardIdentifier, 'billing_postal_code')
        self.assertModelField(field, models.CharField, True, True)
        self.assertEqual(field.max_length, 12)

    def test_billing_country(self):
        field = self.get_field(CardIdentifier, 'billing_country')
        self.assertModelField(field, models.CharField)
        self.assertEqual(field.max_length, 2)

    def test_billing_state(self):
        field = self.get_field(CardIdentifier, 'billing_state')
        self.assertModelField(field, models.CharField, True, True)
        self.assertEqual(field.max_length, 2)

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

    def test_billing_address(self):
        card = CardIdentifier(
            billing_address_1='88 The Road',
            billing_address_2='Some Estate',
            billing_postal_code='412',
            billing_city='City',
            billing_country='US',
            billing_state='AL'
        )
        self.assertEqual(
            card.billing_address,
            {
                'address1': card.billing_address_1,
                'address2': card.billing_address_2,
                'city': card.billing_city,
                'country': card.billing_country,
                'postalCode': card.billing_postal_code,
                'state': card.billing_state
            }
        )

    def test_display_text(self):
        self.assertEqual(
            CardIdentifier(card_type='Visa', last_four_digits='1234').display_text,
            'Visa (1234)'
        )

    # validation

    def test_postal_code_required_when_country_not_IE(self):
        card = CardIdentifier(
            first_name='Foo',
            last_name='User',
            billing_address_1='88 The Road',
            billing_city='City',
            billing_country='GB'
        )
        with self.assertRaises(ValidationError) as e:
            card.clean()

        self.assertEqual(e.exception.args[0], {'billing_postal_code': 'This field is required.'})

    def test_postal_code_not_required_when_country_is_IE(self):
        card = CardIdentifier(
            first_name='Foo',
            last_name='User',
            billing_address_1='88 The Road',
            billing_city='City',
            billing_country='IE'
        )
        card.clean()

    def test_state_required_when_country_is_US(self):
        card = CardIdentifier(
            first_name='Foo',
            last_name='User',
            billing_address_1='88 The Road',
            billing_postal_code='412',
            billing_city='City',
            billing_country='US'
        )
        with self.assertRaises(ValidationError) as e:
            card.clean()

        self.assertEqual(e.exception.args[0], {'billing_state': 'This field is required.'})

    def test_state_not_required_when_country_is_not_US(self):
        card = CardIdentifier(
            first_name='Foo',
            last_name='User',
            billing_address_1='88 The Road',
            billing_city='City',
            billing_country='IE'
        )
        card.clean()
