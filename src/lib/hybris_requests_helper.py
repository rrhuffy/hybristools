import getpass
import logging
import re

import requests
import sys
from keepasshttplib import keepasshttplib
from lib import helpers
from lib import requests_helper

keepasshttplib_client = keepasshttplib.Keepasshttplib()


# TODO:
# https://stackoverflow.com/questions/13030095/how-to-save-requests-python-cookies-to-a-file/13031628#13031628

def return_csrf_if_session_is_valid(session, url):
    if not url.endswith('/'):
        logging.debug(f'url "{url}" does not ends with /')

    text = session.get(url, verify=False).text
    if 'HTTP Status 404' in text:
        print(f'Found 404 in url {url}, probably bad HAC address')
        return None
    elif 'hybris administration console | Login' not in text:
        csrf = None
        try:
            csrf = re.search(r'name="_csrf"\s+value="(.+?)"\s*/>', text).group(1)
        except AttributeError:
            print(f'Cannot find _csrf in:\n{text}')
        return csrf
    else:
        return None


def log_into_hac_and_return_csrf_or_exit(session, address, credentials=None):
    if credentials is None:
        credentials = {'user': '', 'password': ''}
    requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

    # avoid unnecessary redirect from https://server:9002/hac into https://server:9002/hac/
    if not address.endswith('/'):
        logging.debug(f'address "{address}" does not ends with /, adding postfix.')
        address = address + '/'
    get_credentials_from_keepass_if_empty(address, credentials)

    address_to_cookies_map = helpers.load_object_from_file(file_path=f'{__file__}.cache.gitignored', default=dict())
    try:
        cookies = address_to_cookies_map[address]
        session.cookies = cookies
        csrf = return_csrf_if_session_is_valid(session, address)
        if csrf is not None:
            logging.debug(f'Using cached cookies: {cookies} with csrf: {csrf}')
            return csrf
        else:
            logging.debug(f'Session {cookies} expired, getting new one:')
            return _internal_log_in(address, credentials, session, address_to_cookies_map)
    except KeyError:
        logging.debug(f'Cannot find saved session, getting new one:')
        return _internal_log_in(address, credentials, session, address_to_cookies_map)


def get_credentials_from_keepass_if_empty(address, credentials):
    # if credentials aren't provided then try to get it from keepasshttplib
    logging.debug('credentials: ' + str(credentials))
    if not credentials['password'] or not credentials['user']:
        logging.debug(f'No credentials provided, trying to fetch them for {address}')
        try:
            requests_helper.disable_proxy()
            credentials['user'], credentials['password'] = keepasshttplib_client.get_credentials(address)
        except (IndexError, TypeError):
            logging.error(f'Cannot find credentials for {address}')
        finally:
            requests_helper.enable_proxy()
    assert credentials['user'], 'You must provide an user!'
    # if couldn't find password then ask for it
    if not credentials['password']:
        credentials['password'] = getpass.getpass('password:')
        # getpass is leaving empty line, so move terminal cursor one line up after using it
        # print(shell_helper.get_move_up(1), end='')
        # TODO: https://stackoverflow.com/questions/23539184/after-starting-process-how-to-get-parents-pid-in-the-child
        # if everywhere in caller's path there is expect_keepass.py then do not move cursor
    assert credentials['password'], 'You must provide an password!'


def _internal_log_in(address, credentials, session, address_to_cookies_map):
    logging.debug(f'Opening login page ({address})...')
    # 1811 is redirecting to /hac/login.jsp, 2005 is redirecting to /hac/login so we must rely on 302 redirect from /hac
    login_get_result = session.get(address, verify=False)

    try:
        login_csrf_token = re.search(r'name="_csrf"\s+value="(.+?)"\s*/>', login_get_result.text).group(1)
    except AttributeError:
        logging.error(f'Cannot find _csrf in url: "{address}", status: {login_get_result.status_code}, '
                      f'printing html:\n{login_get_result.text}')
        sys.exit(1)

    login_data = {'j_username': credentials['user'], 'j_password': credentials['password'], '_csrf': login_csrf_token,
                  '_spring_security_remember_me': True}
    logging.debug('Sending credentials...')
    login_response = session.post(address + 'j_spring_security_check', data=login_data)
    if "You're" not in login_response.text:
        login_get_result = session.get(address, verify=False)
        if "You're" not in login_get_result.text:
            print(f'Cannot log in (tried user: {credentials["user"]} on address: {address}), '
                  f'printing html:\n{login_get_result.text}')
            sys.exit(1)

    cookies = session.cookies
    address_to_cookies_map.update({address: cookies})
    helpers.save_object_to_file(address_to_cookies_map, file_path=f'{__file__}.cache.gitignored')
    post_login_csrf_token = None
    try:
        post_login_csrf_token = re.search(r'name="_csrf"\s+value="(.+?)"\s*/>', login_response.text).group(1)
    except AttributeError as exc:
        print(f'Caught an exception: {exc} when trying to find a csrf in:\n'
              f'url:{address}j_spring_security_check\nstatus code: {login_response.status_code}\n{login_response.text}')
        sys.exit(1)
    logging.debug(f'Logged in, new session: {cookies} with csrf: {post_login_csrf_token}')
    return post_login_csrf_token
