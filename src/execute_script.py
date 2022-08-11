#!/usr/bin/env python3
import argparse
import logging
import re

import sys
from bs4 import BeautifulSoup

from lib import argparse_helper
from lib import hybris_argparse_helper
from lib import hybris_requests_helper
from lib import logging_helper
from lib import requests_helper


class ScriptExecutionResponse:
    def __init__(self, output_text, execution_result, error_message):
        self.output_text = output_text
        self.execution_result = execution_result
        self.error_message = error_message

    def __repr__(self):
        return f'ScriptExecutionResponse({repr(self.output_text)}, ' \
               f'{repr(self.execution_result)}, {repr(self.error_message)})'

    def __str__(self):
        if self.error_message:
            if self.output_text:
                # both output and error message available
                return f'Output:\n{self.output_text}\nError:\n{self.error_message}'
            else:
                # only error message available
                return self.error_message

        if self.output_text and not self.execution_result:
            # only output text available
            return self.output_text
        elif self.execution_result and not self.output_text:
            # only execution_result available
            return self.execution_result
        elif self.output_text and self.execution_result:
            # both output and execution result available
            return f'Output:\n{self.output_text}\nResult:\n{self.execution_result}'
        else:
            logging.debug('Neither output nor execution result available')
            return ''


def execute_script(script, script_type, rollback, address, user, password, session=None):
    # TODO: check if address is set here, because it will fail
    if session is None:
        session, address = requests_helper.get_session_with_basic_http_auth_and_cleaned_address(address)

    credentials = {'user': user, 'password': password}
    hybris_requests_helper.log_into_hac_and_return_csrf_or_exit(session, address, credentials)
    script_get_result = session.get(address + '/console/scripting/')
    script_csrf_token = re.search(r'name="_csrf"\s+value="(.+?)"\s*/>', script_get_result.text).group(1)
    form_data = {'script': script, '_csrf': script_csrf_token, 'scriptType': script_type, 'commit': not rollback}
    form_data_without_script = {k: v for k, v in form_data.items() if k != 'script'}
    logging.debug(f'form_data_without_script: {form_data_without_script}')
    logging.debug('...executing...')
    execute_address = address + '/console/scripting/execute'
    script_post_result = session.post(execute_address, data=form_data)
    logging.debug('done, printing results:')
    if script_post_result.status_code == 500:
        bs = BeautifulSoup(script_post_result.text, 'html.parser')
        textarea = bs.find('textarea')
        if textarea:
            html = textarea.text
            number_of_lines_to_show = 20
            first_n_lines = '\n'.join(html.strip().split('\n')[0:number_of_lines_to_show])
            msg = f'Received HTTP500, printing first {number_of_lines_to_show} lines of result:\n{first_n_lines}'
        else:
            msg = f'Received HTTP500'
        return ScriptExecutionResponse(None, None, msg)
    elif script_post_result.status_code == 504:
        msg = (f'Received HTTP504 Gateway Timeout Error after {int(script_post_result.elapsed.total_seconds())}s while '
               f'executing POST with script to execute in {execute_address}. '
               f'\nAdd loggers to your script and check result in Hybris logs')
        return ScriptExecutionResponse(None, None, msg)
    result_json = script_post_result.json()
    logging.debug(result_json)

    if not result_json:
        return ScriptExecutionResponse('No result', None, None)
    elif result_json.get('stacktraceText', None):
        return ScriptExecutionResponse(result_json['outputText'].strip(), None, result_json['stacktraceText'])
    else:
        return ScriptExecutionResponse(result_json['outputText'].strip(), result_json['executionResult'], None)


def _handle_cli_arguments():
    parser = argparse.ArgumentParser('Script that executes given beanshell/groovy script')
    hybris_argparse_helper.add_hybris_hac_arguments(parser)
    parser.add_argument('script',
                        help='string with beanshell/groovy file '
                             'or string with script (use literal \\n for newline) '
                             'or "-" if piping script')
    parser.add_argument('type', help='type of script', choices=['groovy', 'beanshell'])
    # TODO: maybe instead of "--parameters 1 2 3 4" accept "1 2 3 4" as last parameters? (what about optional limit?)
    parser.add_argument('--parameters', '-p', nargs='*',
                        help='arguments to put into script by replacing with $1, $2 etc')
    parser.add_argument('--rollback', action='store_true', help='Execute script in rollback mode')
    logging_helper.add_logging_arguments_to_parser(parser)
    args = parser.parse_args()
    script = argparse_helper.get_text_from_string_or_file_or_pipe(args.script)
    assert script is not None, 'Cannot load script'

    if args.parameters:
        for i, parameter in enumerate(args.parameters):
            parameter_to_replace = f'${i + 1}'
            if parameter_to_replace not in script:
                print(f'WARN: Unexpected parameter {parameter_to_replace} with value {repr(parameter)}')
            script = script.replace(parameter_to_replace, parameter)

        next_parameter = f'${len(args.parameters) + 1}'
        if next_parameter in script:
            print(f"WARN: Probably you should provide additional parameter for replacing with {next_parameter}")
    elif '$1' in script:
        print("No parameters given, but $1 found in query, probably you've forgotten to add parameter")

    logging.debug('Full script:')
    logging.debug(script)
    return args, script


def main():
    logging_helper.run_ipython_on_exception()
    args, script = _handle_cli_arguments()
    wrapped_execute_script = logging_helper.decorate_method_with_pysnooper_if_needed(execute_script, args.logging_level)
    response = wrapped_execute_script(script, args.type, args.rollback, args.address, args.user, args.password)
    assert isinstance(response, ScriptExecutionResponse)
    logging.debug(f'Response: {repr(response)}')
    print(response)
    sys.exit(1 if response.error_message else 0)


if __name__ == '__main__':
    main()
