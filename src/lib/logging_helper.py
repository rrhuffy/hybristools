import argparse
import logging
import os
from enum import IntEnum

import pysnooper
import sys


class LogLevel(IntEnum):
    DEBUG = 10
    INFO = 20
    WARN = 30


class ExcepthookChain:
    def __init__(self, original_excepthook, new_excepthook):
        self.original_excepthook = original_excepthook
        self.new_excepthook = new_excepthook

    def __call__(self, type_, value_, traceback_):
        self.original_excepthook(type_, value_, traceback_)
        self.new_excepthook(type_, value_, traceback_)


def install_cleanup_exception_hook(callback, re_raise_exception=False):
    def cleanup_callback_exception_hook_handler(type_, value_, traceback_):
        if re_raise_exception:
            # re-raise an exception in a way that'll show exactly the same result in console as without this hook
            sys.__excepthook__(type_, value_, traceback_)

        callback()

    sys.excepthook = ExcepthookChain(sys.excepthook, cleanup_callback_exception_hook_handler)


def run_ipython_on_exception():
    # do not install exception hook if output is a pipe
    if not sys.stdout.isatty():
        return

    def cleanup_after_exception_handler():
        print('Running debugger - after debugging just execute "exit()"')
        import pdb
        pdb.pm()
        print('Quitting debugger')

    install_cleanup_exception_hook(cleanup_after_exception_handler)


def ignore_uncaught_keyboard_interrupt():
    original_excepthook = sys.excepthook

    def keyboard_interrupt_filtering_exception_hook(type_, value_, traceback_):
        if type_ == KeyboardInterrupt:
            print(' Caught KeyboardInterrupt, bye!')
        else:
            original_excepthook(type_, value_, traceback_)

    sys.excepthook = keyboard_interrupt_filtering_exception_hook


class LoggingAction(argparse.Action):
    def __init__(self,
                 option_strings,
                 dest,
                 change,
                 logging_format,
                 default=0,
                 value_min=0,
                 value_max=60,
                 required=False,
                 help=None):
        argparse.Action.__init__(
            self,
            option_strings=option_strings,
            dest=dest,
            nargs=0,
            default=default,
            required=required,
            help=help)
        self.default = default
        self.change = change
        self.value_min = value_min
        self.value_max = value_max
        self.dest = dest
        # set default logging level  https://stackoverflow.com/a/12158233/4605582
        logging.basicConfig(format=logging_format, level=default)

    def __call__(self, parser, namespace, values, option_string=None):
        current_value = getattr(namespace, self.dest, self.default)
        new_level = current_value + self.change
        setattr(namespace, self.dest, new_level)
        new_level_clamped = _clamp(new_level, self.value_min, self.value_max)
        logging.root.setLevel(new_level_clamped)


def _clamp(value, value_min, value_max):
    return max(min(value, value_max), value_min)


def add_logging_arguments_to_parser(parser, default_level=logging.INFO, logging_format='%(levelname)s: %(message)s'):
    # logging_format examples: '%(levelname)s: %(message)s' | '%(message)s'

    # if print(txt, end='') equivalent is needed: "logging.root.handlers[0].terminator=''" is doing it globally
    # or create manually two separate loggers, one normal, with endline='\n' and second, with endline=''

    parser.add_argument('-v', '--verbose', dest='logging_level',
                        action=LoggingAction, default=default_level, change=-10, logging_format=logging_format,
                        help='increase output verbosity (e.g., -vv is more than -v)')
    parser.add_argument('-q', '--quiet', dest='logging_level',
                        action=LoggingAction, default=default_level, change=10, logging_format=logging_format,
                        help='decrease output verbosity (e.g., -qq is more than -q)')


def decrease_root_logging_level(amount):
    logging.root.setLevel(get_logging_level() + amount * 10)


def increase_root_logging_level(amount):
    logging.root.setLevel(get_logging_level() - amount * 10)


def get_logging_level():
    return logging.root.getEffectiveLevel()


def decorate_method_with_pysnooper_if_needed(method, logging_level, *args, **kwargs):
    if logging_level > 0:
        return method

    depth = 1 - int(logging_level / 10)
    return decorate_method_with_pysnooper(method, depth=depth, *args, **kwargs)


def decorate_method_with_pysnooper(method, depth=1, *args, **kwargs):
    return pysnooper.snoop(depth=depth, *args, **kwargs)(method)
