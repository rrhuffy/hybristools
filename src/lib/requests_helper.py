import logging
import os
import re

import requests


def get_session():
    requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
    session = requests.sessions.Session()
    proxy = os.environ.get('HTTPS_PROXY')
    if proxy:
        session.proxies = {
            "http": proxy,
            "https": proxy
        }
    return session


def get_session_with_basic_http_auth_and_cleaned_address(address):
    session = get_session()
    if '@' in address:  # https://user:pass@url type of basic auth credentials passing
        match = re.search(r'(https?://)([^:]+):([^@]+)@(.+)', address)
        auth_user = match.group(2)
        auth_password = match.group(3)
        session.auth = (auth_user, auth_password)
        logging.debug(f'Found @ in address "{address}", extracting basic http auth')
        address = match.group(1) + match.group(4)
        logging.debug(f'Address after extraction: "{address}"')
    return session, address


def disable_proxy():
    os.environ['NO_PROXY'] = '*'


def enable_proxy():
    os.environ.pop('NO_PROXY', None)
