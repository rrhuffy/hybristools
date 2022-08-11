#!/usr/bin/env python3

import argparse
import csv
import datetime
import itertools
import logging
import os
import re
import subprocess
import sys
import time
from collections import Counter

from lib import logging_helper

if os.name == 'nt':
    import tailer

# TODO: figure out how to trigger notifications in multiple environments then uncomment and use all notify-call calls

# TODO: separate thread for checking date, if script started on 2000/1/1 23:59 then after minute we won't read new logs
# Start new thread, give it output queue and current log path, let it start listening (and populate queue if find regex)
# In main thread do queue.get with few seconds timeout (suppress exceptions if needed) then check if date changed:
# - if changed: kill thread and start new with new log path
# - if not: continue to next iteration of infinite loop (== do queue.get)

CRITICAL_MESSAGES = ['<-- Wrapper Stopped',
                     'Context initialization failed',
                     'SEVERE: Exception',
                     'startup failed due to previous errors',
                     'Error creating bean with name']


def check_line(line, ignored_messages, context, exit_callback=None):
    launching_triggered = False

    if context.print_from and not context.print_in_progress:
        match = re.search(context.print_from, line)
        if match:
            context.print_in_progress = True

    if context.print_in_progress:
        print(line.rstrip())

    if context.print_to:
        match = re.search(context.print_to, line)
        if match:
            context.print_in_progress = False
            if exit_callback:
                exit_callback()
            sys.exit(0)

    if context.check_beans or (context.launching and context.startup):
        match = re.search(r"Error creating bean with name '([^']+)'.*", line)
        if match:
            bean_error_message = match.group(0)
            if ignored_messages is not None and not any(
                    (ignored in bean_error_message for ignored in ignored_messages)):
                context.counter.update([(match.group(1))])
                if context.counter.get(match.group(1)) == 1:
                    logging.error(bean_error_message)
                    subprocess.call(f'notify-send "Error in spring beans:" "{bean_error_message}"', shell=True)

        match = re.search(r"org\.springframework\.beans\.factory\.\w+Exception: (.+)", line)
        if match:
            bean_error_message = match.group(0)
            if ignored_messages is not None and not any(
                    (ignored in bean_error_message for ignored in ignored_messages)):
                context.counter.update([(match.group(1))])
                if context.counter.get(match.group(1)) == 1:
                    logging.error(bean_error_message)
                    # subprocess.call(f'notify-send "Error in spring beans:" "{bean_error_message}"', shell=True)

    if context.launching:
        match = re.search(r'\d{4}.*Launching a JVM.*', line)
        if match:
            launching_triggered = True
            searched_text = match.group(0)
            logging.info(f'Found regex in {searched_text}')
            # if logging_helper.get_logging_level() <= logging_helper.LogLevel.INFO:
            #     subprocess.call(f'notify-send "Found regex:" "{searched_text}"', shell=True)
            if not context.startup:
                if exit_callback:
                    exit_callback()
                sys.exit(0)

    if context.startup:
        match = re.search(r'\d{4}.*Server startup in (\d+) ms.*', line)
        if match:
            searched_text = match.group(0)
            logging.info(f'Found regex in {searched_text}')
            # if logging_helper.get_logging_level() <= logging_helper.LogLevel.INFO:
            #     subprocess.call(f'notify-send "Found regex:" "{searched_text}"', shell=True)

            print_beans_report(context)

            if exit_callback:
                exit_callback()
            sys.exit(0)

    # check for critical messages only when server is launching (ignore errors happening during server shutdown)
    if context.startup and (not context.launching or launching_triggered):
        any_critical_found = False
        for critical_message in CRITICAL_MESSAGES:
            match = re.search(critical_message, line)
            if match:
                logging.critical(f'Found critical regex [{critical_message}] in line [{line.rstrip()}]')
                any_critical_found = True

        if any_critical_found:
            logging.critical('Exiting because of error(s) above')
            sys.exit(1)

    if not (context.print_from and context.print_to) and not context.launching and not context.startup:
        match = re.search(context.regex, line)
        if match:
            if logging_helper.get_logging_level() <= logging_helper.LogLevel.INFO:
                searched_text = match.group(0)
                logging.info(f'Found regex: {searched_text}')
                # subprocess.call(f'notify-send "Found regex:" "{searched_text}"', shell=True)
                if context.check_beans:
                    print_beans_report(context)
            if exit_callback:
                exit_callback()
            sys.exit(0)


def print_beans_report(context):
    if len(context.counter.keys()) > 0:
        logging.info(context.counter)
    else:
        logging.info('Nothing weird found in beans')


# TODO: remove Bunch and use normal arguments or create context class
class Bunch(dict):
    def __init__(self, **kw):
        dict.__init__(self, kw)
        self.__dict__ = self

    def __getstate__(self):
        return self

    def __setstate__(self, state):
        self.update(state)
        self.__dict__ = self

    def __repr__(self):
        return '\n'.join(["%s=%r" % (attribute, value) for (attribute, value) in self.__dict__.items()])


def main():
    parser = argparse.ArgumentParser(description='Script that listens server logs for given regex')
    parser.add_argument('regex', nargs='?', help='regex to search in logs')
    parser.add_argument('--beans', action='store_true', help='Check info about bean errors in logs')
    logging_helper.add_logging_arguments_to_parser(parser)
    parser.add_argument('--launching', action='store_true', help='Listen "Launching a JVM"')
    parser.add_argument('--startup', action='store_true', help='Listen "Server startup in X ms"')
    parser.add_argument('--print-from', help='Print logs starting from regex')
    parser.add_argument('--print-to', help='Print logs ending on regex')
    args = parser.parse_args()

    if args.print_from and args.print_to:
        logging.info(f'Printing text between [{args.print_from}] and [{args.print_to}]')
    elif args.launching and args.startup:
        logging.info('Listening for server launching and startup')
    elif args.launching:
        logging.info('Listening for server launching')
    elif args.startup:
        logging.info('Listening for server startup')
    else:
        logging.info(f'Listening server logs for "{args.regex}"')

    # try to load ignored messages from csv file
    ignored_messages = None
    if os.path.exists(f'{__file__}.dat'):
        with open(f'{__file__}.dat') as ignored_messages:
            reader = csv.reader(ignored_messages)
            ignored_messages = set([row[0] for row in reader])

    hybris_dir = os.getenv('HYBRIS_DIR')
    date_yyyymmdd = datetime.datetime.now().strftime("%Y%m%d")
    log_path = f'{hybris_dir}/log/tomcat/console-{date_yyyymmdd}.log'
    context = Bunch(counter=Counter(), print_from=args.print_from, print_to=args.print_to, regex=args.regex,
                    print_in_progress=False, launching=args.launching, startup=args.startup,
                    check_beans=args.beans)

    if os.name == 'nt':
        # handle situation when log file doesn't exist yet
        if not os.path.exists(log_path):
            spinner = itertools.cycle('|/-\\')
            while not os.path.exists(log_path):
                next_spinner = next(spinner)
                print(f'\rLog {log_path} does not exist yet, waiting...{next_spinner}', end='', flush=True)
                time.sleep(0.25)
            print()  # add newline after end of waiting (with spinner animation, without end line characters on console)

        with open(log_path, 'r') as logfile:
            for line in tailer.follow(logfile):
                check_line(line, ignored_messages, context)
    elif os.name == 'posix':
        with subprocess.Popen(['tail', '-F', '-n', '0', log_path], stdout=subprocess.PIPE) as tail:
            try:
                for line_to_decode in tail.stdout:
                    check_line(line_to_decode.decode(), ignored_messages,
                               context, exit_callback=lambda: tail.kill())
            except KeyboardInterrupt:
                logging.info('Bye')
                sys.exit(1)
    else:
        logging.critical(f'Unsupported os found: {os.name}, exiting...')
        sys.exit(1)


if __name__ == '__main__':
    main()
