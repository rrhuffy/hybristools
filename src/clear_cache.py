#!/usr/bin/env python3
import argparse

from lib import hybris_argparse_helper
from lib import hybris_requests_helper
from lib import requests_helper

parser = argparse.ArgumentParser('Script for clearing hybris cache')
hybris_argparse_helper.add_hybris_hac_arguments(parser)
args = parser.parse_args()

session, address = requests_helper.get_session_with_basic_http_auth_and_cleaned_address(args.address)
credentials = {'user': args.user, 'password': args.password}
csrf_token = hybris_requests_helper.log_into_hac_and_return_csrf_or_exit(session, address, credentials)
script_post_result = session.post(address + '/monitoring/cache/regionCache/clear', data={'_csrf': csrf_token})
