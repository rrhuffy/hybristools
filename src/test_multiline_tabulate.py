import pytest

from multiline_tabulate import multiline_tabulate, get_header_and_data_from_string

DEFAULT_WIDTH = 80
NEWLINE = '\n'
EMPTY = ''


def assert_equal_strings_with_pretty_message(actual, expected):
    assert actual == expected, (f'\n'
                                f'--- Actual string:\n'
                                f'{actual}{NEWLINE if not actual.endswith(NEWLINE) else EMPTY}'
                                f'--- Is not equal to expected string:\n'
                                f'{expected}{NEWLINE if not expected.endswith(NEWLINE) else EMPTY}')


def test_2x2_not_transposed():
    header_and_data = [['h1', 'h2'],
                       ['d1', 'd2']]
    tabulated_text = multiline_tabulate(header_and_data, width=DEFAULT_WIDTH, transpose=False)
    expected = f'''
h1 | h2
d1 | d2
'''.lstrip()
    assert_equal_strings_with_pretty_message(tabulated_text, expected)


def test_2x2_transposed():
    header_and_data = [['h1', 'h2'],
                       ['d1', 'd2']]
    tabulated_text = multiline_tabulate(header_and_data, width=DEFAULT_WIDTH, transpose=True)
    expected = f'''
h1 | d1
h2 | d2
'''.lstrip()
    assert_equal_strings_with_pretty_message(tabulated_text, expected)


def test_grouping_with_unique_single_column():
    header_and_data = [['h1', 'h2'],
                       ['1', '2'],
                       ['1', '3']]
    tabulated_text = multiline_tabulate(header_and_data, group=True, width=DEFAULT_WIDTH)
    expected = f'''
{'Common'.center(DEFAULT_WIDTH, '-')}
h1
1
{'Unique'.center(DEFAULT_WIDTH, '-')}
h2
2
3
'''.lstrip()
    assert_equal_strings_with_pretty_message(tabulated_text, expected)


def test_grouping_single_column_with_unique_multiple_columns():
    header_and_data = [['h1', 'h2', 'h3'],
                       ['1', '2', '3'],
                       ['2', '2', '4'],
                       ['3', '2', '5']]
    tabulated_text = multiline_tabulate(header_and_data, group=True, width=DEFAULT_WIDTH)
    expected = f'''
{'Common'.center(DEFAULT_WIDTH, '-')}
h2
2
{'Unique'.center(DEFAULT_WIDTH, '-')}
h1 | h3
1  | 3
2  | 4
3  | 5
'''.lstrip()
    assert_equal_strings_with_pretty_message(tabulated_text, expected)


def test_grouping_multiple_columns_with_unique_multiple_columns():
    header_and_data = [['h1', 'h2', 'h3', 'h4'],
                       ['1', '2', '3', '4'],
                       ['2', '2', '4', '4'],
                       ['3', '2', '5', '4']]
    tabulated_text = multiline_tabulate(header_and_data, group=True, width=DEFAULT_WIDTH)
    expected = f'''
{'Common'.center(DEFAULT_WIDTH, '-')}
h2 | 2
h4 | 4
{'Unique'.center(DEFAULT_WIDTH, '-')}
h1 | h3
1  | 3
2  | 4
3  | 5
'''.lstrip()
    assert_equal_strings_with_pretty_message(tabulated_text, expected)


@pytest.mark.parametrize("input_string, output",
                         (['h1\th2\nd1\td2',
                           [['h1', 'h2'], ['d1', 'd2']]],
                          ['h1\th2\n1\t2\n1\t3',
                           [['h1', 'h2'], ['1', '2'], ['1', '3']]],
                          ['h1\th2\th3\n1\t2\t3\n2\t2\t4\n3\t2\t5',
                           [['h1', 'h2', 'h3'], ['1', '2', '3'], ['2', '2', '4'], ['3', '2', '5']]]))
def test_get_header_and_data_from_string_parametrized(input_string, output):
    assert get_header_and_data_from_string(input_string, delimiter='\t') == output


# TODO
def test_missing_separator_in_last_line_bug():
    header_and_data = [['column1', 'column2', 'column3'],
                       ['value1', 'value2', 'value3']]
    tabulated_text = multiline_tabulate(header_and_data, group=True, width=18, transpose=False, use_colors=False)
    expected = f'''
--------0---------
1 column1|       1
2 column2|       2
3 column3|       3
--------1---------
1 value1 |       1
2 value2 |       2
3 value3 |       3'''.lstrip()
    assert_equal_strings_with_pretty_message(tabulated_text, expected)
