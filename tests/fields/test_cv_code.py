from django import forms

from sagepaypi.fields import CardCVCodeField
from tests.test_case import AppTestCase


class TestField(AppTestCase):

    def test_valid_values(self):
        values = [
            '123',
            '1234',
            ' 123',
            '123 ',
            '12 3'
        ]
        for value in values:
            field = CardCVCodeField()
            self.assertTrue(field.clean(value))

    def test_invalid_values(self):
        values = [
            '12',
            'x',
            'abc',
            '12a',
            ' 12',
            '12 '
        ]
        for value in values:
            field = CardCVCodeField()
            with self.assertRaises(forms.ValidationError) as e:
                field.clean(value)
            self.assertEqual('The security code you entered is invalid.', e.exception.args[0])
