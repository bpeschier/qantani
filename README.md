qantani
=======

Python interface for the Qantani payment API.

.. code-block:: pycon

    >>> api = qantani.QantaniAPI('merchant id', 'merchant key', 'merchant secret')
    >>> api.get_ideal_banks()
    [{'Name': 'ABN Amro', 'Id': 'ABN_AMRO'}, {'Name': 'ASN Bank', 'Id': 'ASN_BANK'}, {'Name': 'F. van Lanschot Bankiers', 'Id': 'VAN_LANSCHOT_BANKIERS'}, {'Name': 'Friesland Bank', 'Id': 'FRIESLAND_BANK'}, {'Name': 'ING', 'Id': 'ING'}, {'Name': 'Rabobank', 'Id': 'RABOBANK'}, {'Name': 'SNS Bank', 'Id': 'SNS_BANK'}, {'Name': 'Triodos Bank', 'Id': 'TRIODOS_BANK'}, {'Name': 'KNAB', 'Id': 'KNAB'}, {'Name': 'Regiobank', 'Id': 'SNS_REGIO_BANK'}]
    >>> api.create_ideal_transaction(42.42, 'bank id', 'Test payment', 'http://myreturnurl')
    {'Status': 'OK', 'BankURL': 'https://www.qantanipayments.com/api/gotobank.php?id=id&token=token', 'Code': 'code', 'TransactionID': 'tid', 'Acquirer': 'A'}
    ...


Coverage
--------

Only the Easy iDeal actions.
