#!/usr/bin/env python3

# ExecuteFlexibleSearchException: Received HTTP500 error doesn't mean you won't know why it happened
# To figure out what's wrong with flexible search enable verbose errors and execute flexible search query in groovy:
# setparametertemporary flexible.search.exception.show.query.details true
# xg "flexibleSearchService.search('select {page},CONCAT({components1}) from {PflJspIncludeComponent} where {components1} is not null group by {page} order by {page}')"
# maybe ask if need to enable verbose errors and rerun query in groovy to see why error happened?

# TODO: pipe-aware result printing to avoid BrokenPipeError: [Errno 32] Broken pipe

# TODO: further refactor: method's arguments (especially passing 'args')

# TODO: extract removing empty columns (without checking first row == column name) into a separate script

import argparse
import html
import logging
import re

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

COLUMN_BLACKLIST = {'hjmpTS', 'createdTS', 'modifiedTS', 'TypePkString', 'OwnerPkString', 'aCLTS', 'propTS'}
# TODO: use ENV var or 0 as a default value
DEFAULT_ENTRIES_LIMIT = shell_helper.get_terminal_height() - 4


class ExecuteFlexibleSearchException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return f'ExecuteFlexibleSearchException: {self.message}'


def _execute_flexible_search_and_return_json(session, hac_address, query, csrf, max_count=100, user='admin',
                                             locale='en'):
    flex_data = {'flexibleSearchQuery': query, '_csrf': csrf, 'maxCount': max_count,
                 'user': user, 'locale': locale, 'commit': False}
    flex_data_without_query_content = {k: v for k, v in flex_data.items() if k != 'flexibleSearchQuery'}
    logging.debug(f'flex data without query content: {flex_data_without_query_content}')
    try:
        post_result = session.post(f'{hac_address}/console/flexsearch/execute', data=flex_data, verify=False)
    except requests.exceptions.ChunkedEncodingError as exc:
        raise ExecuteFlexibleSearchException(f'ChunkedEncodingError: {exc}')

    if post_result.status_code >= 400:
        raise ExecuteFlexibleSearchException(f'Received HTTP{post_result.status_code} error: {post_result.text}')

    result_json = post_result.json()

    if result_json['exception'] is not None:
        exception_message = result_json['exception']['message']
        raise ExecuteFlexibleSearchException(f'Exception during executing Flexible Search: {exception_message}')

    return result_json


def execute_flexible_search(session, hac_address, query, csrf, max_count=100, user='admin', locale='en'):
    result_json = _execute_flexible_search_and_return_json(session, hac_address, query, csrf, max_count, user, locale)
    return result_json['resultList']


def _execute_flexible_search_and_return_header_and_data(session, address, csrf_token, flexible_query, analyse_short,
                                                        no_analyse, limit, ignore_columns):
    logging.debug('Executing...')
    try:
        result_json = _execute_flexible_search_and_return_json(session=session,
                                                               hac_address=address,
                                                               query=flexible_query,
                                                               csrf=csrf_token,
                                                               max_count=limit)
    except ExecuteFlexibleSearchException as exc:
        print(exc)
        sys.exit(1)

    result_list = result_json['resultList']
    logging.debug(f'Result: {result_list}')

    if len(result_list) == 0:
        print('---No data---')
        sys.exit(0)

    result_list_unescaped = []
    for row in result_list:
        for element in row:
            result_list_unescaped.append(html.unescape(element) if element is not None else None)
    headers = result_json['headers']
    headers = [re.sub('^[pP]_', '', header) for header in headers]  # change 'p_uid' -> 'uid' etc. by removing 'p_'
    data_in_separate_lists = []
    for column_index in range(0, len(result_list_unescaped), len(headers)):
        data_in_separate_lists.append(result_list_unescaped[column_index:column_index + len(headers)])
    header_and_data = [headers]
    header_and_data.extend(data_in_separate_lists)

    # TODO: use unroll_pk.py !!
    if analyse_short or not no_analyse:
        # TODO: unroll pk until there are no more pk to check or there is empty output from current pk check
        for analyse_iteration in range(3):
            logging.debug(f'-----------Analyse #{analyse_iteration}')
            # TODO: extract checking PK to check_pk.py with input \d{13} and output: Type, unique field(s?) name + value

            # TODO: check if given types aren't in dictionary already, if not then save results as {Type: [uniqueName1,uN2]}
            # TODO: use [hostName,url] as key, to invalidate caches on new machine or other servers)

            # TODO: allow two fields per type in dictionary to for example pick 2 values from {Address}

            # get all 13 digit numbers (except current 'PK' column), because they may be a PK of something
            item_pk_set = _get_pk_set_from_header_and_data(header_and_data, ignore_columns)

            logging.debug(f'item_pk_set = {item_pk_set}')
            if item_pk_set:
                key_to_string = unroll_pk.get_key_replacements(item_pk_set, session, csrf_token, address,
                                                               not analyse_short)
                logging.debug(f'key_to_string = {key_to_string}')
                if key_to_string:
                    for row in data_in_separate_lists:
                        for column_index, column in enumerate(row):
                            for key, replace_string in key_to_string:
                                # if column isn't empty AND (at least part of) key is in column AND this is not PK col
                                if column is not None and key in column \
                                        and header_and_data[0][column_index].lower() != 'PK'.lower():
                                    row[column_index] = row[column_index].replace(key, replace_string)
                                    logging.debug(f'replacing {key} -> {replace_string}')

    logging.debug(f'Output from execute_flexible_search: {header_and_data}')
    return header_and_data


def _use_pager_for_header_and_data(header_and_data, pager, args):
    if pager == '':
        return '\n'.join([args.csv_delimiter.join(x if x is not None else '' for x in row) for row in header_and_data])
    elif pager == 'multiline':
        additional_parameters = multiline_tabulate.extract_arguments_as_kwargs(args)
        if args.limit == DEFAULT_ENTRIES_LIMIT:  # didn't provide limit amount -> use full screen
            additional_parameters.update({'limit_entries': None, 'limit_lines': DEFAULT_ENTRIES_LIMIT})
        return multiline_tabulate.multiline_tabulate(header_and_data, **additional_parameters)
    else:
        return ''


def _get_pk_set_from_header_and_data(header_and_data, ignore_column):
    item_pk_set = set()
    for row_index, row in enumerate(header_and_data):
        for col_index, column in enumerate(row):
            if header_and_data[0][col_index].lower() == 'PK'.lower():  # ignore data from 'PK' column
                continue

            if column and (ignore_column is None or column not in ignore_column):
                matches = re.findall(r'\d{13}', column)
                for match in matches:
                    item_pk_set.add(match)
    return item_pk_set


def _handle_cli_arguments():
    parser = argparse.ArgumentParser('Script that executes given flexible search')
    hybris_argparse_helper.add_hybris_hac_arguments(parser)
    parser.add_argument('query',
                        help='string with flexible search or path to file with flexible search or "-" if piping')
    parser.add_argument('--parameters', '-p', nargs='*',
                        help='arguments to put into flexible query by replacing with $1, $2 etc')
    # TODO: if there are more than X (1? 2? 3?) blacklisted columns, but not all then by default show them
    parser.add_argument('--no-blacklist', action='store_true',
                        help='Show blacklisted columns (like hjmpTS, createdTS etc')
    parser.add_argument('--analyse-short', '-a', action='store_true',
                        help='Analyse PK and print short item info, by default: print long item info')
    parser.add_argument('--no-analyse', '-A', action='store_true',
                        help='Do not analyse PK to get info about them, by default: print long item info')
    parser.add_argument('--watch', '-w', type=float, help='Number of seconds to wait before retrying query')
    multiline_tabulate.add_common_parser_arguments(parser)
    logging_helper.add_logging_arguments_to_parser(parser)
    parser.set_defaults(limit=DEFAULT_ENTRIES_LIMIT)
    args = parser.parse_args()
    # TODO: expand checking PK to all blacklisted by default columns
    query_lower = args.query.lower()
    is_pk_between_select_and_from = query_lower.find('select') < query_lower.find('pk') < query_lower.find('from')
    if not args.no_blacklist and 'creation' not in args.query and 'modified' not in args.query and (
            'pk' not in args.query or not is_pk_between_select_and_from):
        args.ignore_columns = f'{args.ignore_columns},' + ','.join(COLUMN_BLACKLIST)

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

    return args, flexible_query


def main():
    logging_helper.run_ipython_on_exception()
    args, flexible_query = _handle_cli_arguments()
    wrapped_execute_flexible_search_and_return_header_and_data = logging_helper.decorate_method_with_pysnooper_if_needed(
        _execute_flexible_search_and_return_header_and_data, args.logging_level)

    session, address = requests_helper.get_session_with_basic_http_auth_and_cleaned_address(args.address)
    credentials = {'user': args.user, 'password': args.password}
    csrf_token = hybris_requests_helper.log_into_hac_and_return_csrf_or_exit(session, address, credentials)

    if args.watch:
        try:
            iteration = 0
            lines_in_last_output = 0
            while True:
                last_update_time = time.asctime()
                last_update_message = f'Last update: {last_update_time} {time.time()}'
                header_and_data = wrapped_execute_flexible_search_and_return_header_and_data(session, address,
                                                                                             csrf_token,
                                                                                             flexible_query,
                                                                                             args.analyse_short,
                                                                                             args.no_analyse,
                                                                                             args.limit,
                                                                                             args.ignore_columns)
                output = last_update_message + '\n' + _use_pager_for_header_and_data(header_and_data, args.pager, args)
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
        prepared_string = wrapped_execute_flexible_search_and_return_header_and_data(session, address, csrf_token,
                                                                                     flexible_query,
                                                                                     args.analyse_short,
                                                                                     args.no_analyse,
                                                                                     args.limit,
                                                                                     args.ignore_columns)
        print(_use_pager_for_header_and_data(prepared_string, args.pager, args), end='', flush=True)


if __name__ == '__main__':
    main()
