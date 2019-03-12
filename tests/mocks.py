class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data


TRANSACTION_DATA = {
    'amount': {
        'saleAmount': 100,
        'totalAmount': 100,
        'surchargeAmount': 0
    },
    'status': 'Ok',
    '3DSecure': {
        'status': 'CardNotEnrolled'
    },
    'currency': 'GBP',
    'statusCode': '0000',
    'avsCvcCheck': {
        'status': 'NotChecked',
        'address': 'NotProvided',
        'postalCode': 'NotProvided',
        'securityCode': 'NotProvided'
    },
    'statusDetail': 'The Authorisation was Successful.',
    'paymentMethod': {
        'card': {
            'cardType': 'Visa',
            'expiryDate': '0399',
            'cardIdentifier': '9641440A-E5AC-4191-8CAE-DC6C1AE11BCA',
            'lastFourDigits': '5559'
        }
    },
    'transactionId': 'C105B177-C8D2-0EDF-50A3-16EEBD6D4FFB',
    'transactionType': 'Payment',
    'bankResponseCode': '00',
    'retrievalReference': 1234567,
    'bankAuthorisationCode': '000000'
}


def auth_required_response():
    return MockResponse({
        'paReq': 'random-sagepay-pa-request',
        'acsUrl': 'https://test.sagepay.com/mpitools/accesscontroler?action=pareq',
        'status': '3DAuth',
        'statusCode': '2007',
        'statusDetail': 'Please redirect your customer to the ACSURL to complete the 3DS Transaction',
        'transactionId': 'C105B177-C8D2-0EDF-50A3-16EEBD6D4FFB'
    }, 202)


def auth_success_response():
    return MockResponse({
        'status': 'Authenticated'
    }, 201)


def card_identifier_response():
    return MockResponse({
        'cardIdentifier': 'C6F92981-8C2D-457A-AA1E-16EBCD6D3AC6',
        'expiry': '2015-06-16T10:46:23.693+01:00',
        'cardType': 'Visa'
    }, 201), 'merchant-session-key'


def card_identifier_failed_response():
    return MockResponse({
        'errors': [
            {'property': 'cardDetails.cardholderName', 'clientMessage': 'Error cardholderName', 'code': 1},
            {'property': 'cardDetails.cardNumber', 'clientMessage': 'Error cardNumber', 'code': 1},
            {'property': 'cardDetails.expiryDate', 'clientMessage': 'Error expiryDate', 'code': 1},
            {'property': 'cardDetails.securityCode', 'clientMessage': 'Error securityCode', 'code': 1},
            {'property': 'unknown.property', 'clientMessage': 'Unknown property error', 'code': 1}
        ]
    }, 422), 'merchant-session-key'


def created_payment_response():
    data = TRANSACTION_DATA.copy()
    return MockResponse(data, 201)


def created_refund_response():
    data = TRANSACTION_DATA.copy()
    data['transactionType'] = 'Refund'
    return MockResponse(data, 201)


def created_repeat_response():
    data = TRANSACTION_DATA.copy()
    data['transactionType'] = 'Repeat'
    return MockResponse(data, 201)


def gone_response():
    return MockResponse({}, 500)


def malformed_response():
    return MockResponse({
        'status': 'Jesus christ that broke everything',
        'statusCode': '9999'
    }, 400)


def outcome_aborted_response():
    data = TRANSACTION_DATA.copy()
    data['statusCode'] = '2006'
    data['statusDetail'] = 'The Abort was Successful.'
    data['retrievalReference'] = 0
    return MockResponse(data, 200)


def outcome_live_response():
    data = TRANSACTION_DATA.copy()
    return MockResponse(data, 200)


def outcome_void_response():
    data = TRANSACTION_DATA.copy()
    data['statusCode'] = '2005'
    data['statusDetail'] = 'The Void was Successful.'
    data['retrievalReference'] = 0
    return MockResponse(data, 200)


def instruction_abort_response():
    return MockResponse({
        'instructionType': 'abort',
        'date': '2016-09-08T11:27:34.728+01:00'
    }, 201)


def instruction_release_response():
    return MockResponse({
        'instructionType': 'release',
        'date': '2016-09-08T11:27:34.728+01:00'
    }, 201)


def instruction_void_response():
    return MockResponse({
        'instructionType': 'void',
        'date': '2016-09-08T11:27:34.728+01:00'
    }, 201)
