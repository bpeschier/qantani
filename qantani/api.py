import io
import hashlib
from xml.etree import ElementTree as Tree
from xml.etree.ElementTree import ParseError

import requests

from .exceptions import APIError


class QantaniAPI:
    endpoint_url = 'https://www.qantanipayments.com/api/'

    def __init__(self, merchant_id, merchant_key, merchant_secret):
        self.merchant_id = merchant_id
        self.merchant_key = merchant_key
        self.merchant_secret = merchant_secret

    def create_checksum(self, params):
        """
        Checksum is an SHA1-hash of the parameters sent to the API

        It can be calculated by:

        1. Order parameters by key.
        2. Flatten all values (in order).
        3. Add the Merchant Secret to the end.
        4. Take a SHA1-hash from the result

        """
        ordered = sorted(params.items())
        values = ''.join([str(v) for (k, v) in ordered])
        hash_source = '{values}{secret}'.format(
            values=values, secret=self.merchant_secret)
        return hashlib.sha1(hash_source.encode('utf-8')).hexdigest()

    @staticmethod
    def validate_transaction_checksum(checksum, transaction_id, transaction_code, status, salt):
        """
        Validate the checksum given back in the return URL.

        Checksum for transactions is made up of the SHA1-hash of:

        [transaction_id] + [transaction_code] + [status] + [salt]
        """
        joined = ''.join([str(transaction_id), transaction_code, str(status), str(salt)])
        hashed = hashlib.sha1(joined.encode('utf-8')).hexdigest()
        return hashed == checksum

    #
    # Request and response
    #

    def _request(self, command, parameters, response_xpath):
        """
        Send a request to the Qantani API.

        parameters should be a dict.
        response_xpath should be an XPath query to a single element in the response.
        """
        transaction = Tree.Element('Transaction')

        # Create action
        action = Tree.SubElement(transaction, 'Action')
        name = Tree.SubElement(action, 'Name')
        version = Tree.SubElement(action, 'Version')
        name.text = command
        version.text = '1'

        # Add parameters
        if parameters:
            params = Tree.SubElement(transaction, 'Parameters')
            # Convert dict into elements
            for key, value in parameters.items():
                node = Tree.SubElement(params, key)
                node.text = str(value)

        # Add merchant
        merchant = Tree.SubElement(transaction, 'Merchant')
        merchant_id = Tree.SubElement(merchant, 'ID')
        merchant_key = Tree.SubElement(merchant, 'Key')
        checksum = Tree.SubElement(merchant, 'Checksum')
        merchant_id.text = str(self.merchant_id)
        merchant_key.text = str(self.merchant_key)
        checksum.text = self.create_checksum(parameters)

        # Create request
        tree = Tree.ElementTree(transaction)
        output = io.StringIO()
        tree.write(output, encoding='unicode', xml_declaration=True)
        request = {'data': output.getvalue()}

        # Get response; verify SSL is correct(ish)
        response = requests.post(self.endpoint_url, data=request, verify=True)

        if response.status_code != 200:
            raise APIError('Qantani has an error')

        try:
            root = Tree.fromstring(response.text)
        except ParseError:
            raise APIError('Qantani delivered broken XML')

        # Check status
        status = root.find('Status')
        if status is None:
            raise APIError('Qantani does not follow their own API')
        if not status.text == 'OK':
            raise APIError(root.find('.//Description').text)

        return self._xml_to_python(root.find(response_xpath))

    def _xml_to_python(self, element):
        """
        Quick and dirty conversion based on Qantani answers.

        Collapses XML children into lists and dicts where applicable.

        All same elements in a list-type element:
        <L><E>A</E><E>B</E><E>C</E></L> => [A, B, C]

        Leaf nodes in an element:
        <E><A/><B/><C/></E> => {'E': {'A': ..., 'B': ..., 'C': ...}}
        """
        if len(element) == 0:  # Leaf node
            return {element.tag: element.text}
        else:  # we have children
            children = [self._xml_to_python(el) for el in element]
            all_dicts = all(isinstance(c, dict) for c in children)
            all_single_dicts = all_dicts and all(len(d) == 1 for d in children)
            all_same_dicts = all_single_dicts \
                and all(d.keys() == children[0].keys() for d in children)

            if all_same_dicts:  # collapse into list
                return [list(c.values())[0] for c in children]
            elif all_single_dicts:  # collapse dicts
                return {element.tag: dict([list(d.items())[0] for d in children])}
            else:
                return {element.tag: children}

    #
    # Api-methods
    #

    def get_ideal_banks(self):
        """
        Request all banks available when using iDeal

        Returns a list of dicts representing each bank with an id and a name:

        [
            {
                'Id': 'ASN_BANK',
                'Name': 'ASN Bank'
            },
            ...
        ]
        """
        return self._request('IDEAL.GETBANKS', {}, './Banks')

    def create_ideal_transaction(self, amount, bank_id, description, return_url):
        """
        Initiate a transaction using iDeal.

        Returns a dict with the return URL and transaction details.

        {
            'Status': 'OK',
            'BankURL': 'https://www.qantanipayments.com/api/gotobank.php?id=<id>&token=<token>',
            'Code': '<code>',
            'TransactionID': '<id>',
            'Acquirer': 'A'
        }
        """
        return self._request('IDEAL.EXECUTE', {
            'Amount': '{:.2f}'.format(amount),
            'Currency': 'EUR',
            'Bank': bank_id,
            'Description': description,
            'Return': return_url,
        }, './Response')['Response']

    def check_transaction_status(self, transaction_id, transaction_code):
        """
        Check the status of any transaction.

        Returns:

        {
            'Date': 'YYYY-MM-DD HH:MM',
            'ID': '<id>',
            'Paid': '<Y/N>',
            'Definitive': '<Y/N>',
            'Consumer': {
                'Name': <None or '<name>'>,
                'IBAN': <None or '<iban>'>,
                'Bank': '<bank IBAN code>'
            },
            'MerchantID': '<your merchant id>',
            'CurrentDate': 'YYYY-MM-DD HH:MM'
        }
        """
        return self._request('TRANSACTIONSTATUS', {
            'TransactionID': transaction_id,
            'TransactionCode': transaction_code,
        }, './Transaction')['Transaction']
