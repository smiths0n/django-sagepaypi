from django.test import RequestFactory

from sagepaypi.models import Transaction

from tests.test_case import AppTestCase


class TestTemplateTags(AppTestCase):
    fixtures = ['tests/fixtures/test']

    def test_sagepay_secure_redirect_form_renders(self):
        transaction = Transaction.objects.get(pk='ec87ac03-7c34-472c-823b-1950da3568e6')
        transaction.transaction_id = 'some-unique-key'
        transaction.acs_url = 'http://url.com'
        transaction.pareq = 'some-unique-string'
        transaction.save()

        fake_request = RequestFactory().get('/')

        html = self.render_template(
            """{% load sagepaypi_tags %}{% sagepay_secure_redirect_form transaction %}""",
            {'request': fake_request, 'transaction': transaction}
        )

        self.assertIn('form', html)
