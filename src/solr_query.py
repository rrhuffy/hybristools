#!/usr/bin/env python3
import argparse
import json
import logging
import os
import re
from collections import defaultdict
from datetime import datetime
from urllib.parse import quote_plus
from urllib.parse import urljoin

import sys

from lib import logging_helper
from lib import requests_helper

logging_helper.run_ipython_on_exception()

ignorable_fields = ['autosuggest', 'spellcheck']

parser = argparse.ArgumentParser('Script for executing query on last indexed (flip|flop) SOLR index')
parser.add_argument('query', nargs='?', default='*:*', help='Query to execute, by default *:*')
parser.add_argument('--index', default='.', help='Regex with index to use, case insensitive, default "." == any index')
# TODO: maybe find solr address by using HAC (from ENV)? solrserver.instances.standalone.* and *.endpoint properties
parser.add_argument('--address',
                    default=os.environ.get('HYBRIS_SOLR_URL') if os.environ.get('HYBRIS_SOLR_URL') else
                    os.environ.get('HYBRIS_HAC_URL').replace('/hac', '').replace(':9002', ':8983'),
                    help='SOLR address, by default: HYBRIS_HAC_URL with removed /hac suffix and changed 9002 into 8983')
parser.add_argument('--user', default='solrserver', help='User to log into SOLR, by default solrserver')
parser.add_argument('--password', default='server123', help='Password to use to log into SOLR, by default server123')
logging_helper.add_logging_arguments_to_parser(parser)
args = parser.parse_args()
session, address = requests_helper.get_session_with_basic_http_auth_and_cleaned_address(args.address)

metrics_address = urljoin(args.address, 'solr/admin/metrics?type=gauge&prefix=CORE')
get = session.get(metrics_address, auth=(args.user, args.password), verify=False)

name_to_index_with_timestamp = defaultdict(list)

for metric in get.json()['metrics'].values():
    name = metric['CORE.coreName']
    prefix_name = name.replace('_flip', '').replace('_flop', '')

    if 'backoffice' in name:
        continue

    logging.debug(f'Found name: {name} prefix_name: {prefix_name}')

    if name.endswith('flop'):
        flop_time = datetime.strptime(metric['CORE.startTime'], '%Y-%m-%dT%H:%M:%S.%fZ')
        name_to_index_with_timestamp[prefix_name].append([name, flop_time])
    elif name.endswith('flip'):
        flip_time = datetime.strptime(metric['CORE.startTime'], '%Y-%m-%dT%H:%M:%S.%fZ')
        name_to_index_with_timestamp[prefix_name].append([name, flip_time])
    else:
        custom_time = datetime.strptime(metric['CORE.startTime'], '%Y-%m-%dT%H:%M:%S.%fZ')
        name_to_index_with_timestamp[prefix_name].append([name, custom_time])

index_names = "\n".join(name_to_index_with_timestamp.keys())
index_to_use = None
if len(name_to_index_with_timestamp) > 0:
    # exit if regex for searching index is not provided and we have more than 1 result
    if args.index == '.' and len(name_to_index_with_timestamp) > 1:
        logging.error(f'More than one index found, use --index to provide regex, available ones:\n{index_names}')
        sys.exit(1)

    for index_name, flip_and_flop in name_to_index_with_timestamp.items():
        if re.search(args.index, index_name, re.IGNORECASE):
            # we found requested index name, now check whether flip or flow is fresher
            if len(flip_and_flop) > 1:
                index_to_use = flip_and_flop[0][0] if flip_and_flop[0][1] > flip_and_flop[1][1] else flip_and_flop[1][0]
            else:
                index_to_use = flip_and_flop[0][0]
            logging.debug(f'Using index "{index_to_use}" for requested "{args.index}"')
            break

if index_to_use is None:
    logging.error(f'Could not find index using regex "{args.index}", available ones:\n{index_names}')
    sys.exit(1)

logging.debug(f'Index: "{index_to_use}", query: "{args.query}", results:')
safe_query = quote_plus(args.query, safe=':')
address = f'{args.address}/solr/{index_to_use}/select?q={safe_query}'
requests_get = session.get(address, auth=(args.user, args.password), verify=False)
result_json = requests_get.json()

if result_json['responseHeader']['status'] == 400:
    error_msg = result_json['error']['msg']
    error_class = result_json['error']['metadata'][1]
    logging.error(f'Error during execution: {error_class}: {error_msg}')
    sys.exit(1)

# filtering out unwanted fields
for doc in result_json['response']['docs']:
    to_remove = []
    for key, val in doc.items():
        if any([field in key for field in ignorable_fields]):
            to_remove.append(key)
    for to_remove_x in to_remove:
        del doc[to_remove_x]

print(json.dumps(result_json, ensure_ascii=False, indent=4))
