import dateutil
import mock
from django.test import override_settings

from sagepaypi.gateway import default_gateway, SagepayGateway
from tests.mocks import MockResponse
from tests.test_case import AppTestCase


def mocked_gone_response(*args, **kwargs):
    return MockResponse({}, 500)


def mocked_success_requests(*args, **kwargs):
    if args[0] == 'https://pi-test.sagepay.com/api/v1/merchant-session-keys':
        return MockResponse({
            'merchantSessionKey': 'unique-key',
            'expiry': '2015-08-11T11:45:16.285+01:00'
        }, 201)
    else:
        return MockResponse({}, 201)


@override_settings(SAGEPAYPI_VENDOR_NAME='vendor')
@override_settings(SAGEPAYPI_INTEGRATION_KEY='user')
@override_settings(SAGEPAYPI_INTEGRATION_PASSWORD='pass')
@override_settings(SAGEPAYPI_TEST_MODE=True)
class TestGateway(AppTestCase):

    def test_default_gateway(self):
        self.assertTrue(isinstance(default_gateway, SagepayGateway))

    def test_basic_auth(self):
        auth = default_gateway.basic_auth()

        self.assertEqual(auth.username, 'user')
        self.assertEqual(auth.password, 'pass')

    def test_vendor_name(self):
        vendor_name = default_gateway.vendor_name()

        self.assertEqual(vendor_name, 'vendor')

    def test_api_url__when_dev(self):
        url = default_gateway.api_url()

        self.assertEqual(url, 'https://pi-test.sagepay.com/api/v1')

    @override_settings(SAGEPAYPI_TEST_MODE=False)
    def test_api_url__when_live(self):
        url = default_gateway.api_url()

        self.assertEqual(url, 'https://pi-live.sagepay.com/api/v1')

    @mock.patch('sagepaypi.gateway.requests.post', side_effect=mocked_success_requests)
    def test_get_merchant_session_key(self, mock_post):
        default_gateway.get_merchant_session_key()

        self.assertIn(
            mock.call(
                'https://pi-test.sagepay.com/api/v1/merchant-session-keys',
                auth=default_gateway.basic_auth(),
                json={'vendorName': 'vendor'}
            ),
            mock_post.call_args_list
        )

    @mock.patch('sagepaypi.gateway.requests.post', side_effect=mocked_success_requests)
    def test_get_merchant_session_key(self, mock_post):
        merchant_session_key = default_gateway.get_merchant_session_key()

        self.assertEqual(merchant_session_key[0], 'unique-key')
        self.assertEqual(merchant_session_key[1], dateutil.parser.parse('2015-08-11T11:45:16.285+01:00'))

    @mock.patch('sagepaypi.gateway.requests.post', side_effect=mocked_gone_response)
    def test_get_merchant_session_key__returns_none_when_http_error(self, mock_post):
        merchant_session_key = default_gateway.get_merchant_session_key()

        self.assertIsNone(merchant_session_key)

    @mock.patch('sagepaypi.gateway.requests.post', side_effect=mocked_success_requests)
    def test_create_card_identifier(self, mock_post):
        default_gateway.create_card_identifier({'foo': 1})

        self.assertIn(
            mock.call(
                'https://pi-test.sagepay.com/api/v1/merchant-session-keys',
                auth=default_gateway.basic_auth(),
                json={'vendorName': 'vendor'}
            ),
            mock_post.call_args_list
        )
        self.assertIn(
            mock.call(
                'https://pi-test.sagepay.com/api/v1/card-identifiers',
                headers={'Authorization': 'Bearer unique-key'},
                json={'foo': 1}
            ),
            mock_post.call_args_list
        )

    @mock.patch('sagepaypi.gateway.requests.post', side_effect=mocked_success_requests)
    def test_get_3d_secure_status(self, mock_post):
        default_gateway.get_3d_secure_status('123', {'foo': 1})

        self.assertIn(
            mock.call(
                'https://pi-test.sagepay.com/api/v1/transactions/123/3d-secure',
                auth=default_gateway.basic_auth(),
                json={'foo': 1}
            ),
            mock_post.call_args_list
        )

    @mock.patch('sagepaypi.gateway.requests.get', side_effect=mocked_success_requests)
    def test_get_transaction_outcome(self, mock_get):
        default_gateway.get_transaction_outcome('123')

        self.assertIn(
            mock.call(
                'https://pi-test.sagepay.com/api/v1/transactions/123',
                auth=default_gateway.basic_auth()
            ),
            mock_get.call_args_list
        )

    @mock.patch('sagepaypi.gateway.requests.post', side_effect=mocked_success_requests)
    def test_submit_transaction(self, mock_post):
        default_gateway.submit_transaction({'foo': 1})

        self.assertIn(
            mock.call(
                'https://pi-test.sagepay.com/api/v1/transactions',
                auth=default_gateway.basic_auth(),
                json={'foo': 1}
            ),
            mock_post.call_args_list
        )

    @mock.patch('sagepaypi.gateway.requests.post', side_effect=mocked_success_requests)
    def test_submit_transaction_instruction(self, mock_post):
        default_gateway.submit_transaction_instruction('123', {'foo': 1})

        self.assertIn(
            mock.call(
                'https://pi-test.sagepay.com/api/v1/transactions/123/instructions',
                auth=default_gateway.basic_auth(),
                json={'foo': 1}
            ),
            mock_post.call_args_list
        )
