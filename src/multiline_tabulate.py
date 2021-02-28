#!/usr/bin/env python3

# TODO: add counter for entries, so we'll see how many entries are there
# TODO: extract common only if lines_per_entry_unextracted > lines_per_entry_extracted

# TODO: reorder columns to optimize line usage/number of lines as 'optimize' option
# TODO: alphabetical_columns and dont_touch_columns(already implemented :D) options

# TODO: by default aligning to left for text and to right for numbers (must do it separately on each column)
# TODO: when end of line, don't split word by \n, instead put \n in word beginning
# TODO: add a pretty BOX printing, looking like this:
# +---------+
# | h1 | h2 |
# |----+----|
# | d1 | d2 |
# | d3 | d4 |
# +---------+
# TODO: add methods add_column/add_row and allow continuous table updating

import argparse
import csv
import logging
import os
import re
from collections import defaultdict

import sys
from tqdm import tqdm

from lib import argparse_helper
from lib import logging_helper
from lib import shell_helper

SHOW_PROGRESS_THRESHOLD = 10000


class MultilineException(Exception):

    def __init__(self, message) -> None:
        self.message = message

    def __str__(self):
        return f'MultilineException: {self.message}'


def _split_into_lines(column_lengths, width, separator):
    columns_count = len(column_lengths)
    separator_length = len(separator)
    line_number = 1
    current_line_length = 0
    column_index_start = 0
    column_index = 0
    output = defaultdict(list)
    while column_index < columns_count:
        current_column_length_with_separator = column_lengths[column_index] - column_index_start + separator_length

        # if column with separator fits in current line
        if current_line_length + current_column_length_with_separator <= width:
            current_line_length += current_column_length_with_separator
            column_index_end = column_index_start + current_column_length_with_separator - 1  # -1 because it's inclusive
            output[line_number].append([column_index, column_index_start, column_index_end, True])
            column_index += 1
            column_index_start = 0
        else:
            # this column doesn't fit in current line but line contains something
            if current_line_length > 0:
                column_index_start = 0  # set caret position to beginning of next column
            # this column doesn't fit in current line and line is empty
            else:
                used_space_in_line = width - current_line_length
                if column_index_start != 0:  # we are in truncating state
                    column_index_end = used_space_in_line + column_index_start - 1  # -1 because it's inclusive
                    output[line_number].append([column_index, column_index_start, column_index_end, False])
                else:
                    # column_index_end = width - current_line_length - separator_length
                    # don't need separator because column is truncated
                    column_index_end = used_space_in_line - 1  # -1 because it's inclusive
                    output[line_number].append([column_index, column_index_start, column_index_end, False])
                column_index_start = column_index_end + 1
            line_number += 1
            current_line_length = 0
    return output


def _filter_empty_data_columns(column_lengths, header_and_data):
    # get column lengths from data without header
    column_lengths_data_only = []
    for column_index in zip(*header_and_data[1:]):
        column_lengths_data_only.append(max(
            [len(str((column if column != 'NULL' else column.replace('NULL', '')) or '')) for column in column_index]))
    # TODO: BUG: this is not filtering out values like:
    # h1 | v1
    # h2 |
    # h3 | v3

    # filter columns in header with data
    header_and_data_filtered = []
    for data_line in header_and_data:
        new_line = []
        for index, column in enumerate(data_line):
            if column_lengths_data_only[index] != 0:
                new_line.append(column)
        header_and_data_filtered.append(new_line)

    # filter column lengths for header with data
    column_lengths_filtered = []
    for index, column_length in enumerate(column_lengths):
        if column_lengths_data_only[index] != 0:
            column_lengths_filtered.append(column_length)

    return column_lengths_filtered, header_and_data_filtered


def _fit_data_into_screen(column_lengths, terminal_width, separator):
    splitted_columns_when_full_width = _split_into_lines(column_lengths, terminal_width, separator)
    line_numbers_count_when_full_width = len(splitted_columns_when_full_width)
    line_numbers_text_length = 0  # try to use one line and no numeration, so no character for line numbers is needed
    if line_numbers_count_when_full_width == 1:  # text fit in one line
        return terminal_width, line_numbers_text_length, splitted_columns_when_full_width

    # cannot fit data into single line entries
    splitted_columns_when_not_full_width = splitted_columns_when_full_width
    previous_line_number_text_length = len(str(len(splitted_columns_when_not_full_width)))
    while True:
        # get inner width by subtracting L+R line numbers length (from previous calculation) from terminal width
        inner_width = terminal_width - 2 * (previous_line_number_text_length + 1)
        # split text using new inner width
        splitted_columns_when_not_full_width = _split_into_lines(column_lengths, inner_width, separator)
        current_line_numbers_text_length = len(str(len(splitted_columns_when_not_full_width)))
        # if text splitted using new inner width have equal number of lines than before then exit loop
        if previous_line_number_text_length != current_line_numbers_text_length:
            # text splitted using new inner width have more lines than before
            # save new line numbers text length for next calculations
            previous_line_number_text_length = current_line_numbers_text_length
        else:
            return inner_width, current_line_numbers_text_length, splitted_columns_when_not_full_width


def _get_tabulated_lines(header_and_data, separator, inner_width, line_numbers_size, splitted_columns,
                         terminal_width, use_newlines, align, use_colors, limit_entries, limit_lines,
                         print_entry_breaks=False):
    output_buffer = ''
    header_and_data_len = len(header_and_data)
    if header_and_data_len < SHOW_PROGRESS_THRESHOLD:
        iterator = enumerate(header_and_data)
    else:
        print(f'Found {header_and_data_len} > {SHOW_PROGRESS_THRESHOLD}) '
              'elements to show (header and data), showing progress bar:')
        iterator = tqdm(enumerate(header_and_data), total=header_and_data_len)

    lines_so_far = 0
    for data_index, data_value in iterator:  # enumerate header and all entries
        # add underscore for header
        # TODO: bug when using it for very long texts causing multi line printing (line number "0" got underscore)
        if data_index == 0 and use_colors:
            # TODO: extract condition and use here + at this method end
            # TODO: print only in last line of multi line header
            output_buffer += shell_helper.get_underscore_start()

        if print_entry_breaks:  # print line break between entries
            # return current buffer if next line will fill whole screen
            if limit_lines is not None and lines_so_far + 1 > limit_lines:
                number_of_skipped_entry_lines = len(header_and_data) - data_index - 1
                # print(f'ending because of limits, {limit_lines}, {lines_so_far}')
                if number_of_skipped_entry_lines > 0:
                    return output_buffer + f'...and more...'
                else:
                    return output_buffer

            if use_colors:
                output_buffer += shell_helper.colorized_center(data_index, terminal_width, '-', 235, 240, 235)
            else:
                output_buffer += '-'.center(terminal_width)

            if use_newlines:
                output_buffer += '\n'

            lines_so_far += 1

        number_of_lines_per_entry = len(splitted_columns)
        for line_number, columns in splitted_columns.items():
            current_line = ''
            for column_index, column_index_start, column_index_end, use_separator in columns:
                # TODO: add test with 'pk,123,\x1b[38;5;1m123456789\x1b[39m\nitemtype,first,second' for this case
                column_or_empty = shell_helper.get_printable_text_substring(data_value[column_index] or '',
                                                                            column_index_start,
                                                                            column_index_end - column_index_start + 1)

                if align == 'r':
                    justified = column_or_empty.rjust(column_index_end - column_index_start - len(separator) + 1)
                elif align == 'l':
                    justified = column_or_empty.ljust(column_index_end - column_index_start - len(separator) + 1)
                else:
                    justified = column_or_empty.center(column_index_end - column_index_start - len(separator) + 1, ' ')
                current_line += justified

                if use_separator and column_index != len(header_and_data[0]) - 1:
                    current_line += separator

            if use_colors:
                color_dark = 245
                color_grey = 251
                if number_of_lines_per_entry == 1 and data_index % 2 == 1:
                    color = color_grey
                elif number_of_lines_per_entry == 1 and data_index % 2 != 1:
                    color = color_dark
                elif number_of_lines_per_entry != 1 and line_number % 2 == 1:
                    color = color_grey
                elif number_of_lines_per_entry != 1 and line_number % 2 != 1:
                    color = color_dark
                output_buffer += shell_helper.colorize_text('', color)

            # return current buffer if next line will fill whole screen
            if limit_lines is not None and lines_so_far + 1 > limit_lines:
                # print(f'ending because of limits2, {limit_lines}, {lines_so_far}')
                return output_buffer

            if number_of_lines_per_entry == 1:  # if using single line entries print full line
                output_buffer += current_line
                # fix for terminals that put \n if there is string (with length equal to terminal width) plus \n at end
                if use_newlines or len(current_line) != terminal_width:
                    output_buffer += '\n'
                lines_so_far += 1
            else:  # if using multi line entries print on each line: line number, space, inner text, space, line number
                left_line_number = str(line_number).rjust(line_numbers_size)
                right_line_number = str(line_number).rjust(inner_width - len(current_line) + line_numbers_size)
                output_buffer += f'{left_line_number} {current_line} {right_line_number}'
                if use_newlines:
                    output_buffer += '\n'
                lines_so_far += 1

        if data_index == 0 and use_colors:
            output_buffer += shell_helper.get_underscore_end()

    return output_buffer


# TODO: kwargs instead of millions of parameters?
def multiline_tabulate(header_and_data, separator='|', width=None, use_newlines=None,
                       print_empty_columns=False, ignore_columns=None, limit_entries=None, limit_lines=None,
                       replace_dictionary=None, align='l', use_colors=True, group=True, print_entry_breaks=False,
                       sort=None, sort_descending=None, reverse=False, data_only=False, transpose=None):
    """

    :param header_and_data: data to tabulate; in form: [ ['header1', 'h2'], ['data1','d2'], ['d11', 'd22'] ]
    :param separator: character to put between entries (automatically wrap in spaces if still will fit in screen)
    :param width: maximum characters to use on single line
    :param use_newlines: whether to put or not \n character at line end (different terminals/OSes must/can't use it)
    :param print_empty_columns: should show or hide columns with empty data on each entry?
    :param ignore_columns: list of blacklisted strings for column names, in form ['colName', 'anotherBlacklistedColumn']
    :param limit_entries: maximum amount of data entries to print (if used with limit_lines, it'll use both)
    :param limit_lines: maximum lines to print (if used with limit_entries, it'll use both)
    :param replace_dictionary: used for example to name known elements like PKs: {'1234567890123': 'familiarNameForPK'}
    :param align: where align text to? [l]eft, [c]enter, [r]ight, used only if len(columns) > 1
    :param use_colors: should use brighter/darker color for even/odd lines?
    :param group: should extract common elements and print them before tabulating entries with unique columns?
    :param print_entry_breaks: should put horizontal lines with index between entries?
    :param sort: sort by column number
    :param reverse: reverse before tabulating
    :param data: print only data, without header
    :return: string with tabulated output
    """
    terminal_width = width or shell_helper.get_terminal_width()
    logging.debug(f'terminal width: {terminal_width}')
    logging.debug(f'terminal height: {limit_entries}')
    logging.debug(f'len(header_and_data): {len(header_and_data)}')
    if len(header_and_data) == 0:
        return 'No data'.center(terminal_width, '-')

    if data_only:
        header_and_data = header_and_data[1:]

    grouped_output = ''
    logging.debug(header_and_data)
    columns_in_rows = [len(i) for i in header_and_data]

    # try to fix a case when last column of last row is empty, hence triggering bug with inconsistent columns amount
    if min(columns_in_rows) != max(columns_in_rows):
        if min(columns_in_rows[:-1]) == max(columns_in_rows[:-1]):
            header_and_data[-1].append('')
            columns_in_rows = [len(i) for i in header_and_data]

    if min(columns_in_rows) != max(columns_in_rows):
        print(f'Different number of columns_in_rows!\n{columns_in_rows}')
        width_minus_debug_prefix = (width or shell_helper.get_terminal_width()) - len('DEBUG: ')

        for i, line in enumerate(header_and_data):
            if i == 0:
                logging.debug(f'Header (line {i + 1}) [{len(header_and_data[i])} columns] looks like this:')
                logging.debug(shell_helper.fit_text_printable_part_only('"' + ','.join(header_and_data[i]) + '"',
                                                                        width_minus_debug_prefix,
                                                                        postfix_if_cant_fit='..."'))
                for j, column in enumerate(header_and_data[i]):
                    safe_column = shell_helper.replace_whitespace_characters_by_their_representations(column)
                    logging.debug(shell_helper.fit_text_printable_part_only(f'{j + 1}: {safe_column}',
                                                                            width_minus_debug_prefix))
                logging.debug('Now searching for first row with different number of columns:\n')
                continue

            if len(line) != len(header_and_data[0]):
                logging.debug(f'Line {i} has different amount of columns and looks like this:')
                logging.debug(shell_helper.fit_text_printable_part_only(f'"' + ','.join(header_and_data[i]) + '"',
                                                                        width_minus_debug_prefix,
                                                                        postfix_if_cant_fit='..."'))

                # print previous line if possible
                if i - 1 > 0:
                    for j, column in enumerate(header_and_data[i - 1]):
                        safe_column = shell_helper.replace_whitespace_characters_by_their_representations(column)
                        logging.debug(shell_helper.fit_text_printable_part_only(
                            f'Previous ({i - 1} line) col {j + 1}: {safe_column}', width_minus_debug_prefix))

                # print current line
                for j, column in enumerate(line):
                    safe_column = shell_helper.replace_whitespace_characters_by_their_representations(column)
                    logging.debug(
                        shell_helper.fit_text_printable_part_only(f'Current  ({i} line) col {j + 1}: {safe_column}',
                                                                  width_minus_debug_prefix))

                # print next line if possible
                if i + 1 < len(header_and_data):
                    for j, column in enumerate(header_and_data[i + 1]):
                        safe_column = shell_helper.replace_whitespace_characters_by_their_representations(column)
                        logging.debug(shell_helper.fit_text_printable_part_only(
                            f'Next ({i + 1} line) col {j + 1}: {safe_column}', width_minus_debug_prefix))
                break
        logging.debug(f'Full input:')
        for line in header_and_data:
            logging.debug(line)
        raise MultilineException(f'Different number of columns_in_rows!\n{columns_in_rows}')

    # replace every line with proper string representation, so for example '\n\t' etc. won't mess the screen
    header_and_data_as_strings = list()
    for original_entry_line in header_and_data:
        temporary_line = list()
        for original_entry_line_value in original_entry_line:
            if original_entry_line_value is not None:
                original_lines = str(original_entry_line_value)
                fixed_whitespaces = shell_helper.replace_whitespace_characters_by_their_representations(original_lines)
                fixed_trailing_multiple_zeros = re.sub(r'(\d\.\d+?)0{2,}$', r'\g<1>0', fixed_whitespaces)
                fixed_leading_and_trailing_whitespaces = fixed_trailing_multiple_zeros.strip()
                replaced_value = fixed_leading_and_trailing_whitespaces
                if replace_dictionary is not None and replaced_value in replace_dictionary:
                    replaced_value = replace_dictionary[replaced_value]

                temporary_line.append(replaced_value)
            else:
                temporary_line.append('')
        header_and_data_as_strings.append(temporary_line)

    if group and len(columns_in_rows) > 2:
        column_indexes_to_remove = list()
        column_names_to_remove = list()
        column_values_to_remove = list()

        for i in range(columns_in_rows[0]):
            column_value = header_and_data_as_strings[1][i]
            column_name = header_and_data_as_strings[0][i]

            if all(single_line[i] == column_value for single_line in header_and_data_as_strings[2:]):
                logging.debug(f'{column_name}: {column_value} is the same everywhere, removing...')
                column_indexes_to_remove.append(i)
                column_names_to_remove.append(column_name)
                column_values_to_remove.append(column_value)
            else:
                logging.debug(f'{column_name} have different values inside')

        # if we found common values in any column
        if len(column_indexes_to_remove) > 0:
            # printing common columns
            grouped_output += 'Common'.center(terminal_width, '-')
            grouped_output += '\n'
            grouped_output += multiline_tabulate([column_names_to_remove, column_values_to_remove], width=width,
                                                 print_empty_columns=print_empty_columns)
            grouped_output += 'Unique'.center(terminal_width, '-')
            grouped_output += '\n'

            # removing common columns
            for column_index_to_remove in column_indexes_to_remove[::-1]:
                for line in header_and_data_as_strings:
                    del line[column_index_to_remove]

        logging.debug(f'column_indexes_to_remove = {column_indexes_to_remove}')
        logging.debug(f'ignore_columns = {ignore_columns}')

        if not column_indexes_to_remove and len(header_and_data_as_strings[0]) == 3:
            logging.debug('Grouping vertically didn\'t find anything. Trying to group horizontally now')
            # we can to group, previous try didn't do anything and we have 3 columns, maybe input is already transposed?
            # pk 123 312
            # code X X
            # field 1 2

            row_indexes_to_remove = list()
            row_names_to_remove = list()
            row_values_to_remove = list()

            for i, line in enumerate(header_and_data_as_strings):
                column_name = line[0]
                column_value_1 = line[1]
                column_value_2 = line[2]
                if column_value_1 == column_value_2:
                    logging.debug(f'{column_name}: {column_value_1} is the same in both columns, removing...')
                    row_indexes_to_remove.append(i)
                    row_names_to_remove.append(column_name)
                    row_values_to_remove.append(column_value_1)
                else:
                    logging.debug(f'{column_name} have different values in columns')

            # if we found common values in any column
            if len(row_indexes_to_remove) > 0:
                # printing common columns
                grouped_output += 'Common'.center(terminal_width, '-')
                grouped_output += '\n'
                grouped_output += multiline_tabulate([row_names_to_remove, row_values_to_remove],
                                                     width=width,
                                                     print_empty_columns=print_empty_columns,
                                                     use_colors=use_colors,
                                                     transpose=transpose)
                grouped_output += 'Unique'.center(terminal_width, '-')
                grouped_output += '\n'

                # removing common rows
                for row_index_to_remove in row_indexes_to_remove[::-1]:
                    del header_and_data_as_strings[row_index_to_remove]

            logging.debug(f'column_indexes_to_remove = {column_indexes_to_remove}')
            logging.debug(f'ignore_columns = {ignore_columns}')

    header_and_data_as_strings_len = len(header_and_data_as_strings)
    have_data = header_and_data_as_strings_len > 1

    # removing blacklisted columns
    # TODO: this is working only with data like ['h1', 'h2'], ['d1','d2'] - it will not work when data is transposed
    if ignore_columns is not None and have_data:
        indexes_to_remove = []
        for index, value in enumerate(header_and_data_as_strings[0]):
            # TODO: best caseless matching method: https://stackoverflow.com/a/40551443
            if any(value.lower() == blacklisted_entry.lower() for blacklisted_entry in ignore_columns):
                indexes_to_remove.append(index)
        indexes_to_remove.sort(reverse=True)  # sort in reverse order to be able to remove those indexes from lists
        for index_to_remove in indexes_to_remove:
            for entry in header_and_data_as_strings:
                del entry[index_to_remove]

        number_of_indexes_to_remove = len(indexes_to_remove)
        if number_of_indexes_to_remove > 0:
            logging.debug(f'removed {number_of_indexes_to_remove} blacklisted columns')
            columns_in_rows = [len(i) for i in header_and_data_as_strings]

    # TODO: sort columns, example below for sorting alphabetically using header columns' names as keys
    # sorted_indices = sorted(range(len(header_and_data_as_strings[0])), key=header_and_data_as_strings[0].__getitem__, reverse=True)
    # header_and_data_as_strings = [[line[idx] for idx in sorted_indices] for line in header_and_data_as_strings]

    # get maximum length of each column (using empty string when None)
    original_column_lengths = []
    for column_index in zip(*header_and_data_as_strings):
        original_column_lengths.append(
            max([shell_helper.get_printable_text_length(str(column or '')) for column in column_index]))

    # if needed then remove both header columns and data columns when any column is None or empty in all data lines
    if not print_empty_columns and have_data:
        previous_columns_count = len(original_column_lengths)
        new_column_lengths, new_header_and_data = _filter_empty_data_columns(original_column_lengths,
                                                                             header_and_data_as_strings)
        new_columns_count = len(new_column_lengths)
        if previous_columns_count != new_columns_count:
            columns_hidden_count = previous_columns_count - new_columns_count
            logging.debug(f'removed {columns_hidden_count} empty columns')

    else:  # printing empty columns or no data after header
        new_column_lengths = original_column_lengths
        new_header_and_data = header_and_data_as_strings

    logging.debug(f'new_column_lengths = {new_column_lengths}')

    if len(new_column_lengths) == 0:
        return grouped_output + 'No data'.center(terminal_width, '-')

    # when unset: transpose and force one line per entry if only one entry exists and has more than 1 column
    if transpose is None:
        should_transpose = len(header_and_data) == 2 and all(columns_in_row > 1 for columns_in_row in columns_in_rows)
    else:
        should_transpose = transpose

    if should_transpose:
        logging.debug('Transposing')
        new_header_and_data = list(map(list, zip(*new_header_and_data)))
        new_column_lengths = []
        for column_index in zip(*new_header_and_data):
            new_column_lengths.append(
                max([shell_helper.get_printable_text_length(str(column or '')) for column in column_index]))

    # sorting
    sort_effective_index = None
    sort_ascending = None
    if sort is not None:
        sort_effective_index = sort - 1 if sort > 0 else sort
        sort_ascending = True
    elif sort_descending is not None:
        sort_effective_index = sort_descending - 1 if sort_descending > 0 else sort_descending
        sort_ascending = False

    if sort_effective_index is not None and sort_ascending is not None:
        logging.debug(f'Sorting {"ascending" if sort_ascending else "descending"} by column nr {sort_effective_index}')

        # https://stackoverflow.com/questions/5967500/how-to-correctly-sort-a-string-with-a-number-inside
        # TODO: maybe natsort? https://github.com/SethMMorton/natsort
        def atof(text):
            try:
                return float(text.replace(',', '.'))
            except ValueError:
                return text

        header = new_header_and_data[0]
        first = new_header_and_data[0][sort_effective_index]
        second = new_header_and_data[1][sort_effective_index]
        both_first_and_second_row_are_floats = isinstance(atof(first), float) and isinstance(atof(second), float)

        if both_first_and_second_row_are_floats:
            to_sort = new_header_and_data
        else:
            to_sort = new_header_and_data[1:]

        sorted_data = sorted(to_sort,
                             key=lambda row: [atof(c) for c in re.split(r'[+-]?([0-9]+(?:[.,][0-9]*)?|[.,][0-9]+)',
                                                                        row[sort_effective_index])],
                             reverse=sort_ascending)

        if both_first_and_second_row_are_floats:
            new_header_and_data = sorted_data
        else:
            new_header_and_data = [header, *sorted_data]

    if reverse:
        logging.debug('Reversing')
        new_header_and_data = [new_header_and_data[0], *new_header_and_data[:0:-1]]

    logging.debug(f'new_header_and_data = {new_header_and_data}')
    logging.debug(f'new_column_lengths = {new_column_lengths}')
    columns_in_rows = [len(i) for i in new_header_and_data]

    # if only one column and aligning to left, then just straight print every element
    if all(columns_in_row == 1 for columns_in_row in columns_in_rows) and align == 'l':
        if limit_entries is None:
            one_column_output = '\n'.join([element[0] or '' for element in new_header_and_data]) + '\n'
        else:  # if limit is not None:
            one_column_output = '\n'.join(
                [element[0] or '' for element in new_header_and_data[:limit_entries + 1]]) + '\n'
            number_of_skipped_entry_lines = len(new_header_and_data) - limit_entries - 1  # -1 because of header
            if number_of_skipped_entry_lines > 0:
                one_column_output += f'...and {number_of_skipped_entry_lines} more \n'
        logging.debug('Only one column + aligning to left = straight printing elements')
        return grouped_output + one_column_output
    elif all(columns_in_row == 2 for columns_in_row in columns_in_rows):
        # TODO: when using header+one data row (hence tabulated one) provide an option to either CUT:
        # TERMINAL COLUMNS END HERE -> $
        # field  | value               $
        # field2 | very long value t...$
        # field3 | short value         $
        # TODO: or option to show all text:
        # TERMINAL COLUMNS END HERE -> $
        # field  | value               $
        # field2 | very long value that$
        #        | cannot be displayed $
        #        | in one line per row $
        # field3 | short value         $
        separator_broader = f' {separator} '
        cut = True
        cut = False
        # TODO: move to cli arguments (by default don't cut)
        output = grouped_output
        sep_len = len(separator_broader)
        for line in new_header_and_data:
            key = line[0].ljust(new_column_lengths[0])
            key_len = new_column_lengths[0]
            value_raw = line[1]
            value_len = shell_helper.get_printable_text_length(value_raw)
            if cut:
                # value = shell_helper.fit_printable_text(value_raw, terminal_width, key_len + sep_len)
                value = shell_helper.get_printable_text_substring(value_raw, 0, terminal_width - key_len - sep_len)
                output += key + separator_broader + value + '\n'
            else:  # not cutting = print everything, but pretty
                if key_len + sep_len + value_len <= terminal_width:  # if it will fit when counting printable characters
                    output += key + separator_broader + value_raw + '\n'
                else:  # we won't fit key + value in one screen
                    remaining_space_in_line = terminal_width - key_len - sep_len
                    last_pos = 0

                    # first iteration with key printed
                    value = shell_helper.get_printable_text_substring(value_raw, last_pos, remaining_space_in_line,
                                                                      postfix_if_cant_fit='')
                    last_ansi_sequence = shell_helper.get_last_ansi_sequence(value)
                    color_reset_if_needed = ''
                    if last_ansi_sequence != '':
                        color_reset_if_needed = shell_helper.reset_color()
                    output += key + separator_broader + value + color_reset_if_needed + '\n'
                    last_pos += remaining_space_in_line

                    # all other iterations without key
                    while last_pos < value_len:
                        ansi_sequence_to_reattach = last_ansi_sequence
                        value = shell_helper.get_printable_text_substring(value_raw, last_pos, remaining_space_in_line,
                                                                          postfix_if_cant_fit='')
                        last_ansi_sequence = shell_helper.get_last_ansi_sequence(value)
                        color_reset_if_needed = ''
                        if ansi_sequence_to_reattach != '':
                            color_reset_if_needed = shell_helper.reset_color()
                        output += color_reset_if_needed + "".ljust(
                            key_len) + separator_broader + ansi_sequence_to_reattach + value + '\n'
                        last_pos += remaining_space_in_line

        return output

    # try to fit data on whole screen with single line entries and if it's not possible then use multiline version
    inner_width, line_numbers_size, splitted_columns = _fit_data_into_screen(new_column_lengths,
                                                                             terminal_width,
                                                                             separator)
    if line_numbers_size == 0 and len(separator) <= 2:  # data fit into line and we are using single character separator
        # try again with broader separator
        separator_broader = f' {separator} '
        inner_width_broader, line_numbers_size_broader, splitted_columns_broader = _fit_data_into_screen(
            new_column_lengths, terminal_width, separator_broader)

        if line_numbers_size_broader == 0:  # if still fit into screen with broader separators then use new version
            inner_width = inner_width_broader
            line_numbers_size = line_numbers_size_broader
            splitted_columns = splitted_columns_broader
            separator = separator_broader

    # if using multiple lines per entry then print entry breaks automatically
    # TODO: default: print if more than 1 line per row, --breaks, --no-breaks
    if line_numbers_size > 0:
        print_entry_breaks = True

    # PyCharm needs newlines, but cmd.exe and ConEmu can't print them properly so by default use newline only in PyCharm
    if use_newlines is None:
        if os.name == 'nt':
            use_newlines = "PYCHARM_HOSTED" in os.environ
        elif os.name == 'posix':
            use_newlines = True

    # if limiting lines then decrease remaining amount by space taken by grouped part
    if limit_lines is not None:
        limit_lines -= grouped_output.count('\n')

    tabulated_lines = _get_tabulated_lines(new_header_and_data, separator, inner_width, line_numbers_size,
                                           splitted_columns, terminal_width, use_newlines, align, use_colors,
                                           limit_entries, limit_lines, print_entry_breaks)

    grouped_output_with_tabulated_lines = grouped_output + tabulated_lines
    if use_colors:
        grouped_output_with_tabulated_lines += shell_helper.reset_color()
    return grouped_output_with_tabulated_lines


# TODO: '│' (longer than pipe, creating continuous line) as a separator + --ascii switch changing to '|' (regular pipe)
def add_common_parser_arguments(_parser):
    _parser.add_argument('--ignore_columns', help='Comma separated list of column names ignored from printing')
    _parser.add_argument('--width', help='Width/columns in one row, default max terminal width', type=int)
    _parser.add_argument('--separator', default='|', help='Separator character, default "|"')
    _parser.add_argument('--csv-delimiter', default='\t', help='CSV delimiter character, default: "\\t"')
    _parser.add_argument('--csv-quotechar', default="'", help='CSV quotechar character, default: "\'"')
    _parser.add_argument('--empty', action='store_true', help='Should print empty columns? default: False')
    # TODO: use --feature + --no-feature  https://stackoverflow.com/a/15008806
    _parser.add_argument('--use-colors', default=True, type=argparse_helper.str2bool,
                         help='Should use different terminal colors? default: True')
    # TODO: use --feature + --no-feature  https://stackoverflow.com/a/15008806
    _parser.add_argument('--breaks', '-b', action='store_true',
                         help='Should print entry breaks with entry number? default: False')
    _parser.add_argument('--group', '-g', action='store_true', dest='group',
                         help='Should group common values? default: False')
    # TODO: -g table output, -G linear output
    _parser.add_argument('--no-group', action='store_false', dest='group',

                         help='Should group common values? default: False')
    _parser.set_defaults(group=False)
    _parser.add_argument('--transpose', '-t', action='store_true', dest='transpose',
                         help='Force transpose (default: transpose if 2 rows)')
    _parser.add_argument('--no-transpose', '-T', action='store_false', dest='transpose',
                         help='Force no transpose (default: transpose if 2 rows)')
    _parser.set_defaults(transpose=None)
    _parser.add_argument('--align', default='l',
                         choices=['l', 'r', 'c'], help='Align text to: [l-left, r-right, c-center], default l')
    _parser.add_argument('limit', nargs='?', default=shell_helper.get_terminal_height() - 5,
                         help='Limit maximum number of entries to show, default: whole screen', type=int)
    _parser.add_argument('--reverse', '-r', action='store_true', dest='reverse',
                         help='Reverse before tabulating? default: False')
    _parser.add_argument('--data-only', '-d', action='store_true', help='Print only data, without header')
    # TODO: -s sort ascending, -S sort descending, + --sort-asc, --sort-desc ?
    # TODO: allow -s1,2,3 and --sort="column1 name",2,"column 3 name" then sort either by number (if int) or column name (if string)
    _parser.add_argument('--sort', '-s', help='Sort by column number (ascending)', type=int)
    _parser.add_argument('--sort-descending', '-S', help='Sort by column number (descending)', type=int)
    _parser.add_argument('--pager', default='multiline',
                         help='Pager to use (empty for nothing), multiline tabulate by default')
    # TODO: argument --jira to print result in form:
    #   ||Heading 1||Heading 2||
    #   |Col A1|Col A2|
    # TODO: instead of printing "415051" maybe print "415 051"?


def extract_arguments_as_kwargs(_args):
    return {'ignore_columns': _args.ignore_columns.split(',') if _args.ignore_columns is not None else None,
            'width': _args.width,
            'separator': _args.separator,
            'align': _args.align,
            'limit_entries': _args.limit,
            'print_empty_columns': _args.empty,
            'use_colors': _args.use_colors,
            'group': _args.group,
            'print_entry_breaks': _args.breaks,
            'sort': _args.sort,
            'sort_descending': _args.sort_descending,
            'reverse': _args.reverse,
            'data_only': _args.data_only,
            'transpose': _args.transpose}


def get_header_and_data_from_string(str, delimiter, quotechar="'"):
    csv_reader = csv.reader(re.split(r'\r?\n', str), delimiter=delimiter, quotechar=quotechar)
    data_split_by_lines = [row for row in csv_reader]
    return data_split_by_lines


def main():
    parser = argparse.ArgumentParser(description='Script for printing tabular data (single or multi line per row)')
    parser.add_argument('data',
                        help='String with data to put into table and print on console '
                             'OR "-" if piping anything here '
                             'CSV must be RFC-4180 compliant and separated by TAB (excel-tab) '
                             'OR if using other separator then provide it with --csv-delimiter switch')
    add_common_parser_arguments(parser)
    logging_helper.add_logging_arguments_to_parser(parser)
    is_piping_text = shell_helper.is_piping_text()
    # no parameters given but piping
    if len(sys.argv) == 1 and is_piping_text:
        print('Seems like you are piping a text into this script, but you didn\'t provide "-" as argument, exiting...')
        parser.print_help()
        sys.exit(1)
    args = parser.parse_args()
    multiline_tabulate_wrapped = logging_helper.decorate_method_with_pysnooper_if_needed(multiline_tabulate,
                                                                                         args.logging_level)
    if is_piping_text and args.data == '-':  # piping
        data = shell_helper.read_text_from_pipe().rstrip('\n').replace('\r', '')

        # remove leading whitespaces
        data = data.lstrip()
    else:  # not piping
        data = args.data.replace('\\t', '\t').replace('\\n', '\n')

    data_split_by_lines = get_header_and_data_from_string(data,
                                                          delimiter=args.csv_delimiter,
                                                          quotechar=args.csv_quotechar)
    try:
        print(multiline_tabulate_wrapped(data_split_by_lines, **extract_arguments_as_kwargs(args)))
    except MultilineException as exc:
        data_without_multiple_newlines = data.replace('\n\n', '\n')
        print(f'Caught exception when trying to tabulate:\n{data_without_multiple_newlines}')


if __name__ == '__main__':
    main()
