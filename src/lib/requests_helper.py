import logging
import os
import re

import requests
import subprocess

USER_AGENT_FIREFOX = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:94.0) Gecko/20100101 Firefox/94.0'
USER_AGENT_CURL = 'curl/7.54.1'
USER_AGENT_HYBRISTOOLS = 'hybristools'


def get_session():
    requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
    session = requests.sessions.Session()
    set_user_agent(session)
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


def set_user_agent(session, custom_user_agent=None):
    if custom_user_agent:
        session.headers['User-Agent'] = custom_user_agent
    else:
        try:
            # try to get user from git global config
            postfix = subprocess.check_output('git config --global --get user.email'.split(' ')).decode().strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            import getpass
            user = getpass.getuser()
            import socket
            hostname = socket.gethostname()
            postfix = f'{user}@{hostname}'

        user_agent = USER_AGENT_HYBRISTOOLS  # or USER_AGENT_CURL or USER_AGENT_FIREFOX
        if postfix:
            user_agent += f'-{postfix}'

        session.headers['User-Agent'] = user_agent
