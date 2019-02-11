import uuid

from django.core.exceptions import ValidationError
from django.db import models

from sagepaypi.constants import get_country_choices, get_us_state_choices
from sagepaypi.models import Customer
from tests.test_case import AppTestCase


class TestModel(AppTestCase):

    # fields

    def test_id(self):
        field = self.get_field(Customer, 'id')
        self.assertModelField(field, models.UUIDField)
        self.assertFalse(field.editable)
        self.assertTrue(field.primary_key)

    def test_created_at(self):
        field = self.get_field(Customer, 'created_at')
        self.assertModelField(field, models.DateTimeField, blank=True)
        self.assertTrue(field.auto_now_add)

    def test_first_name(self):
        field = self.get_field(Customer, 'first_name')
        self.assertModelField(field, models.CharField)
        self.assertEqual(field.max_length, 100)

    def test_last_name(self):
        field = self.get_field(Customer, 'last_name')
        self.assertModelField(field, models.CharField)
        self.assertEqual(field.max_length, 100)

    def test_billing_address_1(self):
        field = self.get_field(Customer, 'billing_address_1')
        self.assertModelField(field, models.CharField)
        self.assertEqual(field.max_length, 255)

    def test_billing_address_2(self):
        field = self.get_field(Customer, 'billing_address_2')
        self.assertModelField(field, models.CharField, True, True)
        self.assertEqual(field.max_length, 255)

    def test_billing_city(self):
        field = self.get_field(Customer, 'billing_city')
        self.assertModelField(field, models.CharField)
        self.assertEqual(field.max_length, 255)

    def test_billing_postal_code(self):
        field = self.get_field(Customer, 'billing_postal_code')
        self.assertModelField(field, models.CharField, True, True)
        self.assertEqual(field.max_length, 12)

    def test_billing_country(self):
        field = self.get_field(Customer, 'billing_country')
        self.assertModelField(field, models.CharField)
        self.assertEqual(field.max_length, 2)
        self.assertEqual(field.choices, get_country_choices())

    def test_billing_state(self):
        field = self.get_field(Customer, 'billing_state')
        self.assertModelField(field, models.CharField, True, True)
        self.assertEqual(field.max_length, 2)
        self.assertEqual(field.choices, get_us_state_choices())

    # properties

    def test_str(self):
        pk = uuid.uuid4()
        self.assertEqual(Customer(pk=pk).__str__(), str(pk))

    def test_billing_address(self):
        customer = Customer(
            billing_address_1='88 The Road',
            billing_address_2='Some Estate',
            billing_postal_code='412',
            billing_city='City',
            billing_country='US',
            billing_state='AL'
        )
        self.assertEqual(
            customer.billing_address,
            {
                'address1': customer.billing_address_1,
                'address2': customer.billing_address_2,
                'city': customer.billing_city,
                'country': customer.billing_country,
                'postalCode': customer.billing_postal_code,
                'state': customer.billing_state
            }
        )

    # validation

    def test_postal_code_required_when_country_not_IE(self):
        customer = Customer(
            first_name='Foo',
            last_name='User',
            billing_address_1='88 The Road',
            billing_city='City',
            billing_country='GB'
        )
        with self.assertRaises(ValidationError) as e:
            customer.clean()

        self.assertEqual(e.exception.args[0], {'billing_postal_code': 'This field is required.'})

    def test_postal_code_not_required_when_country_is_IE(self):
        customer = Customer(
            first_name='Foo',
            last_name='User',
            billing_address_1='88 The Road',
            billing_city='City',
            billing_country='IE'
        )
        customer.clean()

    def test_state_required_when_country_is_US(self):
        customer = Customer(
            first_name='Foo',
            last_name='User',
            billing_address_1='88 The Road',
            billing_postal_code='412',
            billing_city='City',
            billing_country='US'
        )
        with self.assertRaises(ValidationError) as e:
            customer.clean()

        self.assertEqual(e.exception.args[0], {'billing_state': 'This field is required.'})

    def test_state_not_required_when_country_is_not_US(self):
        customer = Customer(
            first_name='Foo',
            last_name='User',
            billing_address_1='88 The Road',
            billing_city='City',
            billing_country='IE'
        )
        customer.clean()
