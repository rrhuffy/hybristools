#!/usr/bin/env python3
import re

from lib import shell_helper

ANSI_ESCAPE_SEQUENCE_START = '\x1b'
ANSI_ESCAPE_SEQUENCE_END = 'm'
MAX_COLUMNS = shell_helper.get_terminal_width()
# TODO: compute that value to avoid problems with shells with custom tab size (after "tabs 4" for example)
TAB_SIZE = 8

for line in re.split('\r?\n', shell_helper.read_text_from_pipe()):
    escape_sequence_in_progress = False
    printable_characters_printed = 0
    output = []
    for character in line.rstrip():
        if character == ANSI_ESCAPE_SEQUENCE_START:
            escape_sequence_in_progress = True

        if printable_characters_printed >= MAX_COLUMNS and not escape_sequence_in_progress:
            output[-3:] = ['.' * 3]  # change last 3 characters to dots
            output.append(shell_helper.reset_color())  # and reset coloring in this line
            break

        output.append(character)

        if not escape_sequence_in_progress:
            if character == '\t':
                printable_characters_printed += TAB_SIZE - (printable_characters_printed % TAB_SIZE)
            else:
                printable_characters_printed += 1
        if escape_sequence_in_progress and character == ANSI_ESCAPE_SEQUENCE_END:
            escape_sequence_in_progress = False

    if output:
        print(''.join(output))
