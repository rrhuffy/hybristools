#!/usr/bin/env python3
import argparse
import html
import logging
import os
import re
import sys

from lib import hybris_argparse_helper
from lib import hybris_requests_helper
from lib import logging_helper
from lib import requests_helper
from lib import shell_helper

is_piping_text = shell_helper.is_piping_text()

parser = argparse.ArgumentParser('Script for importing impex from file or text')
hybris_argparse_helper.add_hybris_hac_arguments(parser)
parser.add_argument('impex', help='string with impex (use literal \\n for newline) '
                                  'OR path to impex file '
                                  'OR "-" if piping text into this script')
logging_helper.add_logging_arguments_to_parser(parser)
args = parser.parse_args()

is_using_file_with_impex = os.path.exists(args.impex)

session, address = requests_helper.get_session_with_basic_http_auth_and_cleaned_address(args.address)

credentials = {'user': args.user, 'password': args.password}
hybris_requests_helper.log_into_hac_and_return_csrf_or_exit(session, address, credentials)

impex_get_result = session.get(address + '/console/impex/import')
impex_csrf_token = re.search(r'name="_csrf"\s+value="(.+?)"\s*/>', impex_get_result.text).group(1)

if is_using_file_with_impex:
    logging.debug(f'Using file with impex: {args.impex}')
    hybris_dir = os.getenv('HYBRIS_DIR')

    logging.debug(f'File size: {os.path.getsize(args.impex)}')
    if os.path.getsize(args.impex) == 0:
        logging.info(f'Exiting because of empty file in path: {args.impex}')
        sys.exit(0)

    with open(args.impex, 'rb') as file:
        files = {'file': file,
                 'maxThreads': (None, '2'),
                 'enableCodeExecution': (None, 'on'),
                 'legacyMode': (None, 'off'),
                 'validationEnum': (None, 'IMPORT_STRICT'),
                 'encoding': (None, 'UTF-8'),
                 '_csrf': (None, impex_csrf_token), }

        impex_post_result = session.post(f'{address}/console/impex/import/upload?_csrf={impex_csrf_token}', files=files)

else:  # not using file == using text either from pipe or from argument
    if is_piping_text:
        script_content = shell_helper.read_text_from_pipe().replace('\n\n', '\n')
        script_content_split = script_content.split('\n')
        script_content_first_line = script_content_split[0]
        logging.debug(f'First line of impex from a pipe: {script_content_first_line}')
    else:  # not piping text and provided text isn't a file
        script_content = args.impex.replace('\\n', '\n')
        script_content_split = script_content.split('\n')
        script_content_first_line = script_content_split[0]
        logging.debug(f'First line of impex from argument (after replacing literal \\n to newline): ' +
                      f'{script_content_first_line}')
    logging.debug(f'Full script:\n{script_content}')
    impex_data = {'scriptContent': script_content, '_csrf': impex_csrf_token, 'validationEnum': 'IMPORT_STRICT',
                  'maxThreads': 32, 'encoding': 'UTF-8', '_legacyMode': 'on', '_enableCodeExecution': 'on'}
    impex_data_without_script_content = {k: v for k, v in impex_data.items() if k != 'scriptContent'}
    logging.debug(f'impex data without script content: {impex_data_without_script_content}')
    logging.debug('...executing...')

    # validating impex
    logging.debug('Validating script...')
    validation_post_result = session.post(address + '/console/impex/import/validate', data=impex_data)

    assert 'Import script is invalid' not in validation_post_result.text, 'Import script is invalid'

    impex_csrf_token = re.search(r'name="_csrf"\s+value="(.+?)"\s*/>', validation_post_result.text).group(1)
    impex_data = {'scriptContent': script_content, '_csrf': impex_csrf_token, 'validationEnum': 'IMPORT_STRICT',
                  'maxThreads': 32, 'encoding': 'UTF-8', 'legacyMode': 'off', 'enableCodeExecution': 'on'}

    logging.debug('executing...')

    impex_post_result = session.post(address + '/console/impex/import', data=impex_data)

assert impex_post_result.status_code != 500, '500 Server Runtime Exception'

result_string = re.search(r'<span id="impexResult".*\s*data-result="(.+)"', impex_post_result.text).group(1)
if 'Import has encountered problems' in result_string:
    home_dir = os.path.expanduser("~")
    path = f'{home_dir}/impexImport.result'
    with open(path, 'wt', encoding='utf-8') as file:
        error_message_html = re.search(r'<!-- result -->.*<pre>(?:\s|\n)*(.*)</pre>', impex_post_result.text,
                                       re.DOTALL).group(1)
        error_message = html.unescape(error_message_html)
        file.write(error_message.replace('\r\n', '\n'))
    result_string += f'\nError happened during execution of: {args.impex[:256]}'
    result_string += f'\nSaved result in file: {path}'
    number_of_lines_to_show = 10
    error_message_split = error_message.split('\n')
    error_message_lines = len(error_message_split)
    if error_message_lines > number_of_lines_to_show:
        first_n_lines = '\n'.join(error_message_split[0:number_of_lines_to_show])
        result_string += f'\nFirst {number_of_lines_to_show} lines of result:\n{first_n_lines}'
    else:
        result_string += f'\nResult:\n{error_message}'
    logging.debug(f'Result for {args.impex[:100]}: {result_string}')
    sys.exit(1)

logging.debug(f'Result for {args.impex[:100]}: {result_string}')
sys.exit(0)
