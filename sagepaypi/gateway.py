import dateutil.parser
from enum import IntEnum

import requests
from requests.auth import HTTPBasicAuth

from sagepaypi.conf import get_setting


class SagepayHttpResponse(IntEnum):
    HTTP_200 = 200  # Success! Everything worked as expected.
    HTTP_201 = 201  # Success! Everything worked as expected and a new resource has been created.
    HTTP_202 = 202  # The request has been accepted for processing, but the processing has not been completed.
    HTTP_204 = 204  # The request has been successfully processed and is not returning any content.
    HTTP_400 = 400  # The request could not be understood, generally a malformed body.
    HTTP_401 = 401  # Authentication credentials are missing or incorrect.
    HTTP_403 = 403  # The request was formed correctly but is unsuccessful.
    # Usually transaction request is declined or rejected.
    HTTP_404 = 404  # The resource does not exist.
    HTTP_405 = 405  # The method requested is not permitted against this resource.
    HTTP_408 = 408  # Request timeout.
    HTTP_422 = 422  # The request was well-formed but contains invalid values or missing properties.
    HTTP_500 = 500  # An issue occurred at Sage Pay.
    HTTP_502 = 502  # An issue occurred at Sage Pay.


class SagepayGateway:

    @classmethod
    def basic_auth(cls):
        return HTTPBasicAuth(
            get_setting('INTEGRATION_KEY'),
            get_setting('INTEGRATION_PASSWORD')
        )

    @classmethod
    def vendor_name(cls):
        return get_setting('VENDOR_NAME')

    @classmethod
    def api_url(cls):
        if get_setting('TEST_MODE'):
            return 'https://pi-test.sagepay.com/api/v1'
        return 'https://pi-live.sagepay.com/api/v1'

    def get_merchant_session_key(self):
        url = '%s/merchant-session-keys' % self.api_url()
        post_data = {'vendorName': self.vendor_name()}

        response = requests.post(url, json=post_data, auth=self.basic_auth())

        if response.status_code != SagepayHttpResponse.HTTP_201:
            return None

        data = response.json()
        merchant_session_key = data['merchantSessionKey']
        expiry = dateutil.parser.parse(data['expiry'])

        return merchant_session_key, expiry

    def create_card_identifier(self, data):
        url = '%s/card-identifiers' % self.api_url()
        session_key = self.get_merchant_session_key()

        if not session_key:
            return None

        headers = {'Authorization': 'Bearer %s' % session_key[0]}

        return requests.post(url, json=data, headers=headers), session_key[0]

    def get_3d_secure_status(self, transaction_id, data):
        url = '%s/transactions/%s/3d-secure' % (self.api_url(), transaction_id)

        return requests.post(url, json=data, auth=self.basic_auth())

    def get_transaction_outcome(self, transaction_id):
        url = '%s/transactions/%s' % (self.api_url(), transaction_id)

        return requests.get(url, auth=self.basic_auth())

    def submit_transaction(self, data):
        url = '%s/transactions' % self.api_url()

        return requests.post(url, json=data, auth=self.basic_auth())

    def submit_transaction_instruction(self, transaction_id, data):
        url = '%s/transactions/%s/instructions' % (self.api_url(), transaction_id)

        return requests.post(url, json=data, auth=self.basic_auth())


default_gateway = SagepayGateway()
