import os
import shutil

import math
import sys

ANSI_ESCAPE_SEQUENCE_START = '\x1b'
ANSI_ESCAPE_SEQUENCE_END = 'm'


def get_terminal_width():
    # when piping stdout linux is executing commands in separate process (terminal-less), that's why shutil won't work
    # so instead of "echo x | program.py | cat" you should use "echo x | (export COLUMNS; program.py | cat"

    # because PyCharm is using separate process for execution, shutil.get_terminal_size() is giving 80, 24
    if "PYCHARM_HOSTED" in os.environ:
        return 210

    return shutil.get_terminal_size().columns


def get_terminal_height():
    # when piping stdout linux is executing commands in separate process (terminal-less), that's why shutil won't work
    # so instead of "echo x | program.py | cat" you should use "echo x | (export COLUMNS; program.py | cat"

    # because PyCharm is using separate process for execution, shutil.get_terminal_size() is giving 80, 24
    if "PYCHARM_HOSTED" in os.environ:
        return 40

    return shutil.get_terminal_size().lines


def fit_text(text, width=None, already_used_characters=0, postfix='...'):
    width = width or get_terminal_width()
    if already_used_characters + len(text) > width - len(postfix):
        return text[:width - already_used_characters - len(postfix)] + postfix
    else:
        return text


# TODO: instead of three letter "..." use one character elypsisis: "…" (few places here and maybe another elsewhere?)
def fit_text_printable_part_only(text, width=None, already_used_characters=0, postfix_if_cant_fit='...'):
    width = width or get_terminal_width()
    return get_printable_text_substring(text, 0, width - already_used_characters,
                                        postfix_if_cant_fit=postfix_if_cant_fit)


def get_printable_text_substring(text, _from, _len, postfix_if_cant_fit='...'):
    # print(f'get_printable_text_substring({repr(text)}, {_from}, {_len})')
    # TODO: https://unix.stackexchange.com/questions/111899/how-to-strip-color-codes-out-of-stdout-and-pipe-to-file-and-stdout
    escape_sequence_in_progress = False
    printable_characters = 0
    output = []
    flags = []
    characters_to_skip = _from
    characters_skipped = 0
    for character in text:
        if character == ANSI_ESCAPE_SEQUENCE_START:
            escape_sequence_in_progress = True

        if printable_characters >= _len and not escape_sequence_in_progress:  # text is longer than we can fit
            if len(postfix_if_cant_fit) > 0:
                removed_so_far = 0
                for i in range(len(output) - 1, 0, -1):
                    if not flags[i]:  # not non-printable = printable
                        removed_so_far += 1
                    del output[i]
                    if removed_so_far == len(postfix_if_cant_fit):
                        break

                output.extend(list(postfix_if_cant_fit))
            break

        if characters_skipped < characters_to_skip:  # if we still skipping X printable characters
            if not escape_sequence_in_progress:
                characters_skipped += 1
        else:  # normal mode (after skipping)
            output.append(character)
            flags.append(escape_sequence_in_progress)

            if not escape_sequence_in_progress:
                printable_characters += 1

        if escape_sequence_in_progress and character == ANSI_ESCAPE_SEQUENCE_END:
            escape_sequence_in_progress = False

    return ''.join(output)


def get_printable_text_length(text):
    escape_sequence_in_progress = False
    printable_characters = 0
    current_sequence_length = 0
    for character in text.rstrip():
        if character == ANSI_ESCAPE_SEQUENCE_START:
            escape_sequence_in_progress = True
            current_sequence_length = 0

        if not escape_sequence_in_progress:
            printable_characters += 1
        else:
            current_sequence_length += 1

        if escape_sequence_in_progress and character == ANSI_ESCAPE_SEQUENCE_END:
            escape_sequence_in_progress = False
            current_sequence_length = 0

    printable_characters += current_sequence_length

    return printable_characters


def get_last_ansi_sequence(text):
    starting_pos = text.rfind(ANSI_ESCAPE_SEQUENCE_START)
    if starting_pos == -1:
        return ''
    ending_pos = text.find(ANSI_ESCAPE_SEQUENCE_END, starting_pos)
    if ending_pos == -1:
        return ''

    return text[starting_pos:ending_pos + 1]


def colorized_center(text, width, fill_char, left_color, middle_color, right_color, rainbow=False):
    output = ''
    text_len = len(str(text))
    remaining_len = width - text_len
    for i in range(int(math.floor(remaining_len / 2))):
        cur_color_index = left_color if not rainbow else i % 16
        output += colorize_text(fill_char, cur_color_index)
    output += colorize_text(text, middle_color)
    for i in range(int(math.ceil(remaining_len / 2))):
        cur_color_index = right_color if not rainbow else i % 16
        output += colorize_text(fill_char, cur_color_index)
    output += colorize_text('', 255)
    return output


# TODO: split into color_start, color_end then implement:
# def colorize_text(text, color, normal_color):
#     return color_start(color) + text + color_end(normal_color)


def colorize_text(text, color):
    return f'\x1b[38;5;{color}m{text}'


def reset_color():
    return '\x1b[39m'


def clear_to_end_of_line():
    return '\x1b[K'


def clear_to_end_of_screen():
    return '\x1b[J'


def get_underscore_start():
    return '\x1b[4m'


def get_underscore_end():
    return '\x1b[24m'


def get_move_left(character_count):
    if character_count > 0:
        return f'\x1b[{character_count}D'
    else:
        return ''


def get_move_up(lines):
    return f'\x1b[{lines}A'


if __name__ == '__main__':
    orig = '12345\x1b[38;5;m1'
    for i in range(4, 6 + 1):
        out_dots = get_printable_text_substring(orig, 0, i)
        out_empty = get_printable_text_substring(orig, 0, i, postfix_if_cant_fit="")
        print(f'{i}# {orig} + "..." -> {out_dots} ({len(out_dots)}:{get_printable_text_length(out_dots)})')
        print(f'{i}# {orig} + ""    -> {out_empty} ({len(out_empty)}:{get_printable_text_length(out_empty)})')


def replace_whitespace_characters_by_their_representations(original_lines):
    # TODO: use string.translate
    replace_pairs = [['\n', '\\n'], ['\t', '\\t'], ['\r', '\\r'], ['\f', '\\f'], ['\b', '\\b'], ['\x0b', '\\x0b']]
    text = original_lines
    for replace_from, replace_to in replace_pairs:
        text = text.replace(replace_from, replace_to)
    return text


def is_piping_text():
    return not os.isatty(sys.stdin.fileno())


def read_text_from_pipe(encoding='utf8', errors='replace'):
    return sys.stdin.buffer.read().decode(encoding, errors)
