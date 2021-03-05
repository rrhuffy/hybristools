#!/usr/bin/env python3
import argparse
import logging
import re

from lib import hybris_argparse_helper
from lib import hybris_requests_helper
from lib import logging_helper
from lib import requests_helper

parser = argparse.ArgumentParser('Script that changes log4j2 logger levels')
hybris_argparse_helper.add_hybris_hac_arguments(parser)
logging_helper.add_logging_arguments_to_parser(parser)
parser.add_argument('logger', help='logger name')
parser.add_argument('level', help='logger level', choices=['ALL', 'DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL', 'TRACE'])
args = parser.parse_args()

logging.debug(f'Changing logger {args.logger} level to {args.level}')

session, address = requests_helper.get_session_with_basic_http_auth_and_cleaned_address(args.address)
credentials = {'user': args.user, 'password': args.password}
hybris_requests_helper.log_into_hac_and_return_csrf_or_exit(session, address, credentials)

script_get_result = session.get(address + '/platform/log4j')
script_csrf_token = re.search(r'name="_csrf"\s+value="(.+?)"\s*/>', script_get_result.text).group(1)

form_data = {'loggerName': args.logger, 'levelName': args.level, '_csrf': script_csrf_token}
logging.debug('...executing...')
script_post_result = session.post(address + '/platform/log4j/changeLevel', data=form_data)
logging.debug('logger level changed')
