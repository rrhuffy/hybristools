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


def _read_text_from_pipe(encoding='utf8', errors='replace'):
    return sys.stdin.buffer.read().decode(encoding, errors)
