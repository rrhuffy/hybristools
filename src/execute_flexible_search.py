#!/usr/bin/env python3

# TODO: move code from top level to main() function and add overriding by pysnooper when -vv provided

# TODO: extract removing empty columns (without checking first row == column name) into a separate script
import argparse
import ast
import csv
import html
import logging
import os
import re
from json.decoder import JSONDecodeError

import requests
import sys
import time

import multiline_tabulate
import unroll_pk
from lib import argparse_helper
from lib import hybris_argparse_helper
from lib import hybris_requests_helper
from lib import logging_helper
from lib import requests_helper
from lib import shell_helper

logging_helper.run_ipython_on_exception()

COLUMN_BLACKLIST = {'hjmpTS', 'createdTS', 'modifiedTS', 'TypePkString', 'OwnerPkString', 'aCLTS', 'propTS'}
replace_dictionary = None
if os.path.exists(f'{__file__}.dat'):
    with open(f'{__file__}.dat') as replace_dictionary_file:
        reader = csv.reader(replace_dictionary_file)
        replace_dictionary = dict((key, val) for key, val in reader)

parser = argparse.ArgumentParser('Script that executes given flexible search')
hybris_argparse_helper.add_hybris_hac_arguments(parser)
parser.add_argument('query', help='string with flexible search or path to file with flexible search or "-" if piping')
parser.add_argument('--parameters', '-p', nargs='*',
                    help='arguments to put into flexible query by replacing with $1, $2 etc')
parser.add_argument('--unescape', action='store_true', help='Try to unescape escaped values from database')
parser.add_argument('--translated', action='store_true', help='Show translated query')
# TODO: if there are more than X (1? 2? 3?) blacklisted columns, but not all then by default show them
parser.add_argument('--no-blacklist', action='store_true', help='Show blacklisted columns (like hjmpTS, createdTS etc')
parser.add_argument('--analyse-short', '-a', action='store_true', help='Analyse PK and print short item info')
parser.add_argument('--no-analyse', '-A', action='store_true', help='Do not analyse PK to get info about them')
parser.add_argument('--watch', '-w', type=float, help='Number of seconds to wait before retrying query')
multiline_tabulate.add_common_parser_arguments(parser)
logging_helper.add_logging_arguments_to_parser(parser)

default_entries_limit = shell_helper.get_terminal_height() - 3
parser.set_defaults(limit=default_entries_limit)
is_piping_text = shell_helper.is_piping_text()

args = parser.parse_args()
# TODO: expand checking PK to all blacklisted by default columns
query_lower = args.query.lower()
is_pk_between_select_and_from = query_lower.find('select') < query_lower.find('pk') < query_lower.find('from')
if not args.no_blacklist and 'creation' not in args.query and (
        'pk' not in args.query or not is_pk_between_select_and_from):
    args.ignore_columns = (f'{args.ignore_columns},' or '') + ','.join(COLUMN_BLACKLIST)

# TODO: accept --param key=value --param key2=value2 then replace ?key and ?key2 with value/value2, cleaner than $1, $2
flexible_query = argparse_helper.get_text_from_string_or_file_or_pipe(args.query)
flexible_query = flexible_query.rstrip(';')
if args.parameters:
    for i, parameter in enumerate(args.parameters):
        flexible_query = flexible_query.replace(f'${i + 1}', parameter)
    if f'${i + 2}' in flexible_query:
        print(f"Probably you should provide additional parameter for replacing with ${i + 2}")
elif '$1' in flexible_query:
    print("No parameters given, but $1 found in query, probably you've forgotten to add parameter")

logging.debug('Full flexible search query:')
logging.debug(flexible_query)
session, address = requests_helper.get_session_with_basic_http_auth_and_cleaned_address(args.address)
assert address, 'You must provide an address!'

credentials = {'user': args.user, 'password': args.password}
csrf_token = hybris_requests_helper.log_into_hac_and_return_csrf_or_exit(session, address, credentials)


def execute_flexible_search(session, url, query, csrf, max_count=100, user='admin', locale='en', commit=False):
    # TODO: optimistic solution: just do a POST with last csrf (if fresh enough) and log-in in case of error?
    # TODO: maybe also check last csrf get time vs last server startup time (which invalidates all csrfs)?
    flex_data = {'flexibleSearchQuery': query, '_csrf': csrf, 'maxCount': max_count,
                 'user': user, 'locale': locale, 'commit': commit}
    flex_data_without_query_content = {k: v for k, v in flex_data.items() if k != 'flexibleSearchQuery'}
    logging.debug(f'flex data without query content: {flex_data_without_query_content}')
    return session.post(url, data=flex_data, verify=False)


def run():
    logging.debug('Executing...')
    url_to_execute = address + '/console/flexsearch/execute'
    try:
        flex_post_result = execute_flexible_search(session=session,
                                                   url=url_to_execute,
                                                   query=flexible_query,
                                                   csrf=csrf_token,
                                                   max_count=args.limit,
                                                   user=credentials['user'])
    except requests.exceptions.ChunkedEncodingError as exc:
        return f'Caught: {exc}'
    logging.debug('Printing results:')
    if flex_post_result.status_code == 500:
        logging.debug(f'HTTP500: {flex_post_result.text}')
        return 'Received HTTP500 error. To print HTML use -v'
    try:
        result_json = flex_post_result.json()
    except JSONDecodeError as exc:
        print(f'Got exception: {exc} while trying to get json from response from url: '
              f'{url_to_execute} with status code {flex_post_result.status_code} and content:\n{flex_post_result.text}')
        sys.exit(1)

    if result_json['exception'] is not None:
        exception_message = result_json['exception']['message']
        print(f'Error: {exception_message}')
        sys.exit(1)

    query_in_format_string = result_json['query'].replace('{', '{{').replace('}', '}}').replace('?', '{}')
    if args.translated:
        translated_query = query_in_format_string.format(*ast.literal_eval(result_json['parametersAsString']))
        print(f'Translated query:\n{translated_query}')
        print('-' * shell_helper.get_terminal_width())
    result_list_unescaped = []
    result_list = result_json['resultList']
    logging.debug('Result (first 2000}:')
    logging.debug(result_list)
    if len(result_list) == 0:
        return 'No data'.center(shell_helper.get_terminal_width(), '-') + '\n'
    for row in result_list:
        for element in row:
            if element is not None:
                unescaped_element = html.unescape(element)  # unescape escaped response
                if args.unescape:
                    unescaped_element = html.unescape(unescaped_element)  # unescape data from db that is escaped
                result_list_unescaped.append(unescaped_element)
            else:
                result_list_unescaped.append(None)
    headers = result_json['headers']
    headers = [re.sub('^[pP]_', '', header) for header in headers]  # change 'p_uid' -> 'uid' etc. by removing 'p_'
    data_in_separate_lists = []
    for column_index in range(0, len(result_list_unescaped), len(headers)):
        data_in_separate_lists.append(result_list_unescaped[column_index:column_index + len(headers)])
    header_and_data = [headers]
    header_and_data.extend(data_in_separate_lists)

    # TODO: use unroll_pk.py !!
    if args.analyse_short or not args.no_analyse:
        # TODO: unroll pk until there are no more pk to check or there is empty output from current pk check
        for analyse_iteration in range(3):
            logging.debug(f'-----------Analyse #{analyse_iteration}')
            # TODO: extract checking PK to check_pk.py with input \d{13} and output: Type, unique field(s?) name + value

            # TODO: check if given types aren't in dictionary already, if not then save results as {Type: [uniqueName1,uN2]}
            # TODO: use [hostName,url] as key, to invalidate caches on new machine or other servers)

            # TODO: allow two fields per type in dictionary to for example pick 2 values from {Address}

            # get all 13 digit numbers (except current 'PK' column), because they may be a PK of something
            item_pk_set = get_pk_set_from_header_and_data(header_and_data)

            # remove pks of items found in custom pk-to-name dictionary
            if replace_dictionary:
                for key in replace_dictionary.keys():
                    item_pk_set.discard(key)

            logging.debug(f'item_pk_set = {item_pk_set}')
            if item_pk_set:
                key_to_string = unroll_pk.get_key_replacements(item_pk_set, session, csrf_token, address,
                                                               not args.analyse_short, credentials['user'])
                logging.debug(f'key_to_string = {key_to_string}')
                if key_to_string:
                    for row in data_in_separate_lists:
                        for column_index, column in enumerate(row):
                            for key, replace_string in key_to_string:
                                # if column isn't empty AND (at least part of) key is in column AND this is not PK col
                                if column is not None and key in column and header_and_data[0][column_index].lower() != 'PK'.lower():
                                    row[column_index] = row[column_index].replace(key, replace_string)
                                    logging.debug(f'replacing {key} -> {replace_string}')

    if args.reverse:
        header_and_data = [header_and_data[0], *reversed(header_and_data[1::])]

    logging.debug(f'Output from execute_flexible_search: {header_and_data}')

    if args.pager == '':
        # TODO: search for regex "csv.delimiter" and refactor this argument
        return '\n'.join([args.csv_delimiter.join(x if x is not None else '' for x in row) for row in header_and_data])
    elif args.pager == 'multiline':
        additional_parameters = multiline_tabulate.extract_arguments_as_kwargs(args)
        if args.limit == default_entries_limit:  # didn't provide limit amount -> use full screen
            additional_parameters.update({'limit_entries': None, 'limit_lines': default_entries_limit})

        # decrease logging level by one before using/printing multiline_tabulate
        logging_helper.decrease_root_logging_level(1)

        return multiline_tabulate.multiline_tabulate(header_and_data, replace_dictionary=replace_dictionary,
                                                     **additional_parameters)


def get_pk_set_from_header_and_data(header_and_data_):
    item_pk_set = set()
    for row_index, row in enumerate(header_and_data_):
        for col_index, column in enumerate(row):
            if header_and_data_[0][col_index].lower() == 'PK'.lower():  # ignore data from 'PK' column
                continue

            if column and (args.ignore_columns is None or column not in args.ignore_columns):
                matches = re.findall(r'\d{13}', column)
                for match in matches:
                    item_pk_set.add(match)
    return item_pk_set


if args.watch:
    try:
        iteration = 0
        lines_in_last_output = 0
        while True:
            last_update_time = time.asctime()
            last_update_message = f'Last update: {last_update_time} {time.time()}'
            output = last_update_message + '\n' + run()
            if iteration == 0:
                print(output, end='', flush=True)
            else:
                move_up = shell_helper.get_move_up(lines_in_last_output)
                clear_to_end_of_screen = shell_helper.clear_to_end_of_screen()
                print(f'{move_up}{clear_to_end_of_screen}{output}', end='', flush=True)

            lines_in_last_output = output.count('\n')
            iteration += 1

            time.sleep(args.watch)
    except KeyboardInterrupt:
        print('\r  ')
else:
    print(run(), end='', flush=True)
