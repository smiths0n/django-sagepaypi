from django import forms

from sagepaypi.fields import CardNumberField
from tests.test_case import AppTestCase


class TestField(AppTestCase):

    def test_valid_values(self):
        values = [
            '4929000000006',
            '4929000005559',
            '4929000000014',
            '4929000000022',
            '4484000000002',
            '4462000000000003',
            '4917300000000008',
            '5404000000000001',
            '5404000000000043',
            '5404000000000084',
            '5404000000000068',
            '5573470000000001',
            '6759000000005',
            # '6705000000008',
            # '6777000000007',
            # '6766000000000',
            '374200000000004',
            '36000000000008',
            '3569990000000009',
        ]
        field = CardNumberField()

        for value in values:
            self.assertTrue(field.clean(value))

    def test_invalid_values(self):
        field = CardNumberField()

        with self.assertRaises(forms.ValidationError) as e:
            field.clean('1234')
        self.assertEqual('The credit card number you entered is invalid.', e.exception.args[0])

        with self.assertRaises(forms.ValidationError) as e:
            field.clean('')
        self.assertEqual('Please enter a credit card number.', e.exception.args[0])
