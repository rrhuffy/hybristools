#!/usr/bin/env python3
import argparse
import json

from lib import hybris_argparse_helper
from lib import hybris_requests_helper
from lib import logging_helper
from lib import requests_helper

parser = argparse.ArgumentParser('Script for getting list of running CronJobs from HAC')
hybris_argparse_helper.add_hybris_hac_arguments(parser)
logging_helper.add_logging_arguments_to_parser(parser)
args = parser.parse_args()
session, address = requests_helper.get_session_with_basic_http_auth_and_cleaned_address(args.address)
credentials = {'user': args.user, 'password': args.password}
hybris_requests_helper.log_into_hac_and_return_csrf_or_exit(session, address, credentials)
for cronjob in session.get(f'{address}/monitoring/cronjobs/data').json():
    print(json.dumps(cronjob))
