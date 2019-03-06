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
        field = CardCVCodeField()
        for value in values:
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
        field = CardCVCodeField()
        for value in values:
            with self.assertRaises(forms.ValidationError) as e:
                field.clean(value)
            self.assertEqual('The security code you entered is invalid.', e.exception.args[0])

        with self.assertRaises(forms.ValidationError) as e:
            field.clean('')
        self.assertEqual('Please enter the three or four digit security code.', e.exception.args[0])
