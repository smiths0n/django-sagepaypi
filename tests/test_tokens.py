from datetime import date, timedelta

from django.conf import settings
from django.test import override_settings

from sagepaypi.tokens import TransactionTokenGenerator
from sagepaypi.models import Transaction

from tests.test_case import AppTestCase


class TokenGeneratorTest(AppTestCase):
    fixtures = ['tests/fixtures/test']

    """ originally taken from django token generator tests for password resets """

    def _create_transaction(self):
        return Transaction.objects.create(
            type="Payment",
            card_identifier_id='67c8ce90-c178-4f78-8176-b87f3ccd52a1',
            amount=1,
            currency='GBP',
            description='Payment for goods'
        )

    def test_make_token(self):
        transaction = self._create_transaction()
        p0 = TransactionTokenGenerator()
        tk1 = p0.make_token(transaction)
        self.assertTrue(p0.check_token(transaction, tk1))

    def test_10265(self):
        """
        The token generated for a transaction created in the same request
        will work correctly.
        """
        transaction = self._create_transaction()
        p0 = TransactionTokenGenerator()
        tk1 = p0.make_token(transaction)
        reload = Transaction.objects.get(pk=transaction.pk)
        tk2 = p0.make_token(reload)
        self.assertEqual(tk1, tk2)

    @override_settings(SAGEPAYPI_TOKEN_URL_DAYS_VALID=1)
    def test_timeout(self):
        """
        The token is valid after n days, but no greater.
        """
        class Mocked(TransactionTokenGenerator):
            def __init__(self, today):
                self._today_val = today

            def _today(self):
                return self._today_val

        transaction = self._create_transaction()
        p0 = TransactionTokenGenerator()
        tk1 = p0.make_token(transaction)
        p1 = Mocked(date.today() + timedelta(settings.SAGEPAYPI_TOKEN_URL_DAYS_VALID))
        self.assertTrue(p1.check_token(transaction, tk1))
        p2 = Mocked(date.today() + timedelta(settings.SAGEPAYPI_TOKEN_URL_DAYS_VALID + 1))
        self.assertFalse(p2.check_token(transaction, tk1))

    def test_check_token_with_nonexistent_token_and_transaction(self):
        transaction = self._create_transaction()
        p0 = TransactionTokenGenerator()
        tk1 = p0.make_token(transaction)
        self.assertIs(p0.check_token(None, tk1), False)
        self.assertIs(p0.check_token(transaction, None), False)

    def test_token_with_different_secret(self):
        """
        A valid token can be created with a secret other than SECRET_KEY by
        using the TransactionTokenGenerator.secret attribute.
        """
        transaction = self._create_transaction()
        new_secret = 'abcdefghijkl'
        # Create and check a token with a different secret.
        p0 = TransactionTokenGenerator()
        p0.secret = new_secret
        tk0 = p0.make_token(transaction)
        self.assertTrue(p0.check_token(transaction, tk0))
        # Create and check a token with the default secret.
        p1 = TransactionTokenGenerator()
        self.assertEqual(p1.secret, settings.SECRET_KEY)
        self.assertNotEqual(p1.secret, new_secret)
        tk1 = p1.make_token(transaction)
        # Tokens created with a different secret don't validate.
        self.assertFalse(p0.check_token(transaction, tk1))
        self.assertFalse(p1.check_token(transaction, tk0))
