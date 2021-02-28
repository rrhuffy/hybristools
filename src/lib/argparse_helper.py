import argparse
import os

import sys
from lib import shell_helper


def get_text_from_string_or_file_or_pipe(string_or_path):
    if shell_helper.is_piping_text() and string_or_path == '-':
        return _read_text_from_pipe().replace('\n\n', '\n')

    if os.path.exists(string_or_path):
        with open(string_or_path) as file:
            return file.read()
    else:
        return string_or_path.replace('\\n', '\n')


def str2bool(v):
    """ https://stackoverflow.com/a/43357954 """
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def add_hybris_hac_arguments(parser):
    _add_hybris_common_arguments(parser)
    parser.add_argument('--address', default=os.environ.get('HYBRIS_HAC_URL'),
                        help='HAC URL, by default using env HYBRIS_HAC_URL')


def add_hybris_hmc_arguments(parser):
    _add_hybris_common_arguments(parser)
    parser.add_argument('--address', default=os.environ.get('HYBRIS_HMC_URL'),
                        help='HMC URL, by default using env HYBRIS_HMC_URL')


def add_hybris_bo_arguments(parser):
    _add_hybris_common_arguments(parser)
    parser.add_argument('--address', default=os.environ.get('HYBRIS_BO_URL'),
                        help='BackOffice URL, by default using env HYBRIS_BO_URL')


def _add_hybris_common_arguments(parser):
    parser.add_argument('--user', default=os.environ.get('HYBRIS_USER'),
                        help='User to use to log in, by default using env HYBRIS_USER')
    parser.add_argument('--password', default=os.environ.get('HYBRIS_PASSWORD'),
                        help='Password to use to log in (leave empty for prompt), by default using env HYBRIS_PASSWORD')


def _read_text_from_pipe(encoding='utf8', errors='replace'):
    return sys.stdin.buffer.read().decode(encoding, errors)
