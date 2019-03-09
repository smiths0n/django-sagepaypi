class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data


GOOD_TRANSACTION_DATA = {
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


def card_identifier_response(*args, **kwargs):
    if args[0].endswith('merchant-session-keys'):
        return MockResponse({
            'merchantSessionKey': 'test-identifier',
            'expiry': '2015-06-16T10:46:23.693+01:00'
        }, 201)
    elif args and args[0].endswith('card-identifiers'):
        return MockResponse({
            'cardIdentifier': 'C6F92981-8C2D-457A-AA1E-16EBCD6D3AC6',
            'expiry': '2015-06-16T10:46:23.693+01:00',
            'cardType': 'Visa'
        }, 201)


def card_identifier_failed_response(*args, **kwargs):
    if args[0].endswith('merchant-session-keys'):
        return MockResponse({
            'merchantSessionKey': 'test-identifier',
            'expiry': '2015-06-16T10:46:23.693+01:00'
        }, 201)
    elif args and args[0].endswith('card-identifiers'):
        return MockResponse({
            'errors': [
                {'property': 'cardDetails.cardholderName', 'clientMessage': 'Error cardholderName', 'code': 1},
                {'property': 'cardDetails.cardNumber', 'clientMessage': 'Error cardNumber', 'code': 1},
                {'property': 'cardDetails.expiryDate', 'clientMessage': 'Error expiryDate', 'code': 1},
                {'property': 'cardDetails.securityCode', 'clientMessage': 'Error securityCode', 'code': 1},
                {'property': 'unknown.property', 'clientMessage': 'Unknown property error', 'code': 1}
            ]
        }, 422)


def gone_response(*args, **kwargs):
    return MockResponse({}, 500)


def malformed_response(*args, **kwargs):
    return MockResponse({
        'status': 'Jesus christ that broke everything',
        'statusCode': '9999'
    }, 400)


def payment_created_response(*args, **kwargs):
    data = GOOD_TRANSACTION_DATA.copy()
    data['transactionType'] = 'Payment'
    return MockResponse(data, 201)


def refund_created_response(*args, **kwargs):
    data = GOOD_TRANSACTION_DATA.copy()
    data['transactionType'] = 'Refund'
    return MockResponse(data, 201)


def transaction_outcome_response(*args, **kwargs):
    data = GOOD_TRANSACTION_DATA.copy()
    data['transactionType'] = 'Payment'
    return MockResponse(data, 200)


def transaction_3d_auth_response(*args, **kwargs):
    return MockResponse({
        'paReq': 'random-sagepay-pa-request',
        'acsUrl': 'https://test.sagepay.com/mpitools/accesscontroler?action=pareq',
        'status': '3DAuth',
        'statusCode': '2007',
        'statusDetail': 'Please redirect your customer to the ACSURL to complete the 3DS Transaction',
        'transactionId': 'C105B177-C8D2-0EDF-50A3-16EEBD6D4FFB'
    }, 202)


def transaction_3d_auth_status(*args, **kwargs):
    if args[0].endswith('3d-secure'):
        return MockResponse({
            'status': 'Authenticated'
        }, 200)

    else:
        data = GOOD_TRANSACTION_DATA.copy()
        data['transactionType'] = 'Payment'
        return MockResponse(data, 200)


def abort_instruction_transaction(*args, **kwargs):
    if args[0].endswith('/instructions'):
        return MockResponse({
            'instructionType': 'abort',
            'date': '2016-09-08T11:27:34.728+01:00'
        }, 201)
    elif 'transactions' in args[0]:
        data = GOOD_TRANSACTION_DATA.copy()
        data['statusCode'] = '2006'
        data['statusDetail'] = 'The Abort was Successful.'
        data['retrievalReference'] = 0
        return MockResponse(data, 200)


def release_instruction_transaction(*args, **kwargs):
    return MockResponse({
        'instructionType': 'release',
        'date': '2016-09-08T11:27:34.728+01:00'
    }, 201)


def void_instruction_transaction(*args, **kwargs):
    if args[0].endswith('/instructions'):
        return MockResponse({
            'instructionType': 'void',
            'date': '2016-09-08T11:27:34.728+01:00'
        }, 201)
    elif 'transactions' in args[0]:
        data = GOOD_TRANSACTION_DATA.copy()
        data['statusCode'] = '2005'
        data['statusDetail'] = 'The Void was Successful.'
        data['retrievalReference'] = 0
        return MockResponse(data, 200)
