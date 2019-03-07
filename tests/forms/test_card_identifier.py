from datetime import date

import dateutil
import mock

from sagepaypi.forms import CardIdentifierForm
from tests.mocks import card_identifier_response
from tests.test_case import AppTestCase


class TestForm(AppTestCase):

    def setUp(self):
        self.data = {
            'first_name': 'Andy',
            'last_name': 'Other',
            'billing_address_1': '88 The Road',
            'billing_address_2': 'Some Estate',
            'billing_city': 'City',
            'billing_country': 'US',
            'billing_postal_code': '412',
            'billing_state': 'AL',
            'card_holder_name': 'A N OTHER',
            'card_number': '4929000005559',
            'card_expiry_date_0': date.today().month,
            'card_expiry_date_1': date.today().year,
            'card_security_code': '123',
            'reusable': 'on'
        }

    @mock.patch('sagepaypi.gateway.requests.post', side_effect=card_identifier_response)
    def test_is_valid(self, mock_post):
        form = CardIdentifierForm(self.data)
        self.assertTrue(form.is_valid())

    @mock.patch('sagepaypi.gateway.requests.post', side_effect=card_identifier_response)
    def test_has_card_identifier_from_sagepay(self, mock_post):
        form = CardIdentifierForm(self.data)

        json = mock_post('card-identifiers').json()

        assert form.is_valid()

        self.assertEqual(form.instance.merchant_session_key, 'test-identifier')
        self.assertEqual(form.instance.card_identifier, json['cardIdentifier'])
        self.assertEqual(form.instance.card_identifier_expiry, dateutil.parser.parse(json['expiry']))
        self.assertEqual(form.instance.card_type, json['cardType'])

    @mock.patch('sagepaypi.gateway.requests.post', side_effect=card_identifier_response)
    def test_save_creates_model_instance(self, mock_post):
        form = CardIdentifierForm(self.data)

        json = mock_post('card-identifiers').json()

        assert form.is_valid()

        instance = form.save()

        self.assertEqual(instance.merchant_session_key, 'test-identifier')
        self.assertEqual(instance.card_identifier, json['cardIdentifier'])
        self.assertEqual(instance.card_identifier_expiry, dateutil.parser.parse(json['expiry']))
        self.assertEqual(instance.card_type, json['cardType'])
        self.assertEqual(instance.last_four_digits, '5559')
        self.assertEqual(instance.expiry_date, date.today().strftime('%m%y'))
        self.assertEqual(instance.first_name, 'Andy')
        self.assertEqual(instance.last_name, 'Other')
        self.assertEqual(instance.billing_address_1, '88 The Road')
        self.assertEqual(instance.billing_address_2, 'Some Estate')
        self.assertEqual(instance.billing_city, 'City')
        self.assertEqual(instance.billing_country, 'US')
        self.assertEqual(instance.billing_postal_code, '412')
        self.assertEqual(instance.billing_state, 'AL')
        self.assertTrue(instance.reusable)

    def test_is_not_valid__without_card_details(self):
        data = self.data.copy()

        del data['card_holder_name']

        form = CardIdentifierForm(self.data)

        self.assertFalse(form.is_valid())

        self.assertEqual(form.instance.merchant_session_key, '')
        self.assertEqual(form.instance.card_identifier, '')
        self.assertEqual(form.instance.card_type, '')
        self.assertIsNone(form.instance.card_identifier_expiry)

    def test_correct_errors_from_sagepay_are_pushed_in_form_errors(self):
        self.skipTest('')
