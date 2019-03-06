from datetime import date
from dateutil.relativedelta import relativedelta

from django import forms

from sagepaypi.fields import CardExpiryDateField
from tests.test_case import AppTestCase


class TestField(AppTestCase):

    def test_valid_values(self):
        today = date.today()
        next_month = today + relativedelta(months=1)
        next_year = today + relativedelta(years=1)
        five_year_time = today + relativedelta(years=5)
        values = [
            [None, None],
            ['', ''],
            [today.month, today.year],
            [next_month.month, next_month.year],
            [next_year.month, next_year.year],
            [five_year_time.month, five_year_time.year],
        ]

        field = CardExpiryDateField(required=False)
        for value in values:
            field.clean(value)

    def test_invalid_values(self):
        today = date.today()
        last_month = today - relativedelta(months=1)

        field = CardExpiryDateField()
        with self.assertRaises(forms.ValidationError) as e:
            field.clean([last_month.month, last_month.year])
        self.assertEqual('This expiry date has passed.', e.exception.args[0])

    def test_compress(self):
        field = CardExpiryDateField()

        self.assertEqual(field.compress(['1', '2019']), date(2019, 1, 31))
        self.assertEqual(field.compress(['12', '2020']), date(2020, 12, 31))

        invalid_months = [
            ['invalid', '2019'],
            [None, '2019'],
            ['99', '2019']
        ]
        for value in invalid_months:
            with self.assertRaises(forms.ValidationError) as e:
                field.compress(value)
            self.assertEqual('Please enter a valid month.', e.exception.args[0])

        invalid_years = [
            ['1', 'invalid'],
            ['1', None]
        ]
        for value in invalid_years:
            with self.assertRaises(forms.ValidationError) as e:
                field.compress(value)
            self.assertEqual('Please enter a valid year.', e.exception.args[0])
