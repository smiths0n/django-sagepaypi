from datetime import date

from django.conf import settings
from django.utils.crypto import constant_time_compare, salted_hmac
from django.utils.http import int_to_base36, base36_to_int
from sagepaypi.conf import get_setting


class TransactionTokenGenerator:
    """
    Strategy object used to generate and check tokens for the transaction mechanism.
    """
    key_salt = "sagepaypi.tokens.TransactionTokenGenerator"
    secret = settings.SECRET_KEY

    def make_token(self, transaction):
        """
        Return a token that can be used once to do a transaction update.
        """
        return self._make_token_with_timestamp(transaction, self._num_days(self._today()))

    def check_token(self, transaction, token):
        """
        Check that a token is correct for a given transaction.
        """
        if not (transaction and token):
            return False
        # Parse the token
        try:
            ts_b36, _ = token.split("-")
        except ValueError:
            return False

        try:
            ts = base36_to_int(ts_b36)
        except ValueError:
            return False

        # Check that the timestamp/uid has not been tampered with
        if not constant_time_compare(self._make_token_with_timestamp(transaction, ts), token):
            return False

        # Check the timestamp is within limit. Timestamps are rounded to
        # midnight (server time) providing a resolution of only 1 day. If a
        # link is generated 5 minutes before midnight and used 6 minutes later,
        # that counts as 1 day. Therefore, SAGEPAYPI_TOKEN_URL_DAYS_VALID = 1 means
        # "at least 1 day, could be up to 2."
        if (self._num_days(self._today()) - ts) > get_setting('TOKEN_URL_DAYS_VALID'):
            return False

        return True

    def _make_token_with_timestamp(self, transaction, timestamp):
        # timestamp is number of days since 2001-1-1.  Converted to
        # base 36, this gives us a 3 digit string until about 2121
        ts_b36 = int_to_base36(timestamp)
        hash_string = salted_hmac(
            self.key_salt,
            self._make_hash_value(transaction, timestamp),
            secret=self.secret,
        ).hexdigest()[::2]  # Limit to 20 characters to shorten the URL.
        return "%s-%s" % (ts_b36, hash_string)

    def _make_hash_value(self, transaction, timestamp):
        """
        Hash the transactions's primary key and some transactions state that's sure to change
        after a transaction update to produce a token that invalidated when it's used
        """
        # Truncate microseconds so that tokens are consistent even if the
        # database doesn't support microseconds.
        transaction_timestamp = transaction.updated_at.replace(microsecond=0, tzinfo=None)
        return str(transaction.pk) + str(transaction_timestamp) + str(timestamp)

    def _num_days(self, dt):
        return (dt - date(2001, 1, 1)).days

    def _today(self):
        # Used for mocking in tests
        return date.today()


default_token_generator = TransactionTokenGenerator()
