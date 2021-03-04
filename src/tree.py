#!/usr/bin/env python3
# https://raw.githubusercontent.com/samlanning/tree.py/master/tree.py

"""
Tree.py: Tree is a small utility that displays input from stdin in a tree-like
structure

Copyright © 2013 Sam Lanning <sam@samlanning.com>
This work is free. You can redistribute it and/or modify it under the
terms of the Do What The Fuck You Want To Public License, Version 2,
as published by Sam Hocevar. See the COPYING file for more details.

This program is free software. It comes without any warranty, to
the extent permitted by applicable law. You can redistribute it
and/or modify it under the terms of the Do What The Fuck You Want
To Public License, Version 2, as published by Sam Hocevar. See
http://www.wtfpl.net/ for more details.

"""


import argparse
import collections
import fileinput
import os
import sys


## Modes

# The different modes of parsing that tree.py can handle
class ParsingMode:
    Auto, NoInput, Normal, Grep = range(4)

# Map from command-line flags to actual values in ParsingMode
map_mode = {
    'auto': ParsingMode.Auto,
    'none': ParsingMode.NoInput,
    'normal': ParsingMode.Normal,
    'n': ParsingMode.Normal,
    'grep': ParsingMode.Grep,
    'g': ParsingMode.Grep
}


# Mappings to color codes for particular types of files / file extensions
color_main = collections.defaultdict(lambda: '0')
color_ext = collections.defaultdict(lambda: '0')


## Internal Constants

# The characters to use in tree representation
class Chars:
    # Vertical Line
    Vrt = chr(9474)
    # Tee
    Tee = chr(9500)
    # Horizontal Line
    Hrz = chr(9472)
    # Bottom Corner
    Crn = chr(9492)
    # Newline Character
    Nln = chr(10)

class SafeChars:
    # Vertical Line
    Vrt = "|"
    # Tee
    Tee = "|"
    # Horizontal Line
    Hrz = "-"
    # Bottom Corner
    Crn = "`"
    # Newline Character
    Nln = chr(10)


class Node(object):

    def __init__(self, label=None):

        self.label = label
        self.children = {}
        self.count = 0
        self.info = None


class Tree(object):

    """
    Contains the information on the data that has already been parsed, and
    methods to parse data

    """

    def __init__(self, mode, use_color, chars):

        self.mode = mode

        # Parse NoInput as "Normal" mode
        if self.mode == ParsingMode.NoInput:
            self.mode = ParsingMode.Normal

        self.color = use_color

        self.root = Node()

        self.dir_count = 0
        self.file_count = 0

        # The strings to concatenate together to form the tree structure
        class Segs:
            Vertical = chars.Vrt + "   "
            Tee = chars.Tee + chars.Hrz + chars.Hrz + " "
            Bottom = chars.Crn + chars.Hrz + chars.Hrz + " "
            Blank = "    "

        self.segs = Segs

    def add_line(self, line):

        """
        Parse a line using the correct mode
        """

        line = line.strip()

        path = None
        info = {}

        if self.mode == ParsingMode.Normal:
            path = line

        elif self.mode == ParsingMode.Grep:

            if line.startswith("Binary file ") and line.endswith(" matches"):
                path = line[12:][:-8]
                info['binary'] = True
            else:
                try:
                    (f, match) = line.split(':', 1)
                except ValueError:
                    print("ERROR: Input Text is not known grep output: {}"
                          .format(line))
                    exit()
                else:
                    path = f



        if path is not None:
            node = self.root

            for i, seg in enumerate(split_path(path)):

                if seg not in node.children:
                    node.children[seg] = Node(seg)

                node = node.children[seg]

            node.info = info
            node.count += 1


    def gen_lines(self, node=None, prefix=[], prefix_string='',
                  parent_path=''):

        """
        Print the tree as required (recursively)

        """

        if node is None:
            node = self.root

        # Only true if not the "top level" empty node
        increase_prefix = False
        path = parent_path

        if node.label is not None:
            path = os.path.join(path, node.label)

            line = prefix_string

            # Get properties about this file / directory

            if len(node.children) > 0 or os.path.isdir(path):
                self.dir_count += 1

                line += color(node.label, color_main['di'], self.color)

            else:
                self.file_count += 1

                if self.mode == ParsingMode.Grep:
                    # Show count
                    if 'binary' in node.info and node.info['binary']:
                        line += '[{}] '.format(color('BIN', color_main['bin'],
                                                     self.color))
                    else:
                        line += '[{}] '.format(color(node.count,
                                                     color_main['count'],
                                                     self.color))

                (f, ext) = os.path.splitext(path)
                line += color(node.label, color_ext[ext], self.color)

            yield line

            increase_prefix = True

        if len(node.children) > 0:

            # Default (current) prefix
            child_prefix_mid = prefix
            child_prefix_bot = prefix
            child_prefix_string_mid = ''
            child_prefix_string_bot = ''

            if increase_prefix:
                child_prefix = ''
                for i in prefix:
                    if i:
                        child_prefix += self.segs.Vertical
                    else:
                        child_prefix += self.segs.Blank

                child_prefix_mid = child_prefix_mid + [1]
                child_prefix_bot = child_prefix_bot + [0]
                child_prefix_string_mid = child_prefix + self.segs.Tee
                child_prefix_string_bot = child_prefix + self.segs.Bottom

            j = 0
            last = len(node.children) - 1
            for i, child in sorted(node.children.items()):
                if j == last:
                    yield from self.gen_lines(child, child_prefix_bot,
                                              child_prefix_string_bot, path)
                else:
                    yield from self.gen_lines(child, child_prefix_mid,
                                              child_prefix_string_mid, path)
                j += 1


def split_path(path, l=None):

    """
    Split up a string path into a list of each element
    """

    if l is None:
        l = []
    (head, tail) = os.path.split(path)
    if head and head != path:

        split_path(head, l)
        l.append(tail)
    else:
        l.append(head or tail)
    return l


def setup_color(args):

    """
    Using environment variables, setup the dictionaries of colour lookups
    """

    def parse_environment_variable(var):
        if var in os.environ:
            for entry in os.environ[var].split(':'):
                if entry != '':
                    try:
                        match, color = entry.split('=')
                    except ValueError:
                        print("ERROR: Could not understand entry {} in "
                              "environment variable {}".format(entry, var))
                        exit(1)
                    else:
                        if match.startswith("*."):
                            color_ext[match[1:]] = color
                        else:
                            color_main[match] = color

    color_main['count'] = '01;32'
    color_main['bin'] = '01;35'

    parse_environment_variable('LS_COLORS')

    parse_environment_variable('TREE_COLORS')


def color(string, color, do_color):
    """
    Wrap a string in an ansi color code
    """

    if do_color:
        return '\033[{}m{}\033[0m'.format(color, string)
    else:
        return string


def main():

    """
    Run when the program is being used standalone, uses stdin as the input
    """

    parser = TreeArgumentParser()

    parser.add_argument('-i', '--mode', '--input-mode',
                        choices=map_mode,
                        default='auto',
                        nargs='?',
                        const='normal',
                    )

    parser.add_argument('-c', '--color', '--colour',
                        choices=['auto', 'always', 'none'],
                        default='auto',
                    )

    parser.add_argument('-e', '--encoding',
                        choices=['auto', 'utf-8', 'ascii'],
                        default='auto',
                    )

    parser.add_argument('-a', action='store_true')

    parser.add_argument('target', nargs='?', default='.')

    args = parser.parse_args()

    # Character set to use
    chars = SafeChars

    if (args.encoding == 'utf-8' or
        args.encoding == 'auto' and sys.stdout.encoding == 'UTF-8'):
        # Switch to UTF-8 Chars
        chars = Chars

    # Are we using ANSI Escape Codes for Color?
    use_color = (args.color == 'always' or
                 args.color == 'auto' and hasattr(sys.stdout, "isatty") and sys.stdout.isatty())

    # Work out parsing mode (auto detect tty)
    args.mode = map_mode[args.mode]

    if args.mode == ParsingMode.Auto:
        if hasattr(sys.stdin, "isatty") and sys.stdin.isatty():
            args.mode = ParsingMode.NoInput
        else:
            args.mode = ParsingMode.Normal

    # Create Tree
    t = Tree(args.mode, use_color, chars)

    # Setup colour dicts using environment variables
    if use_color:
        setup_color(args)

    # If the mode is ParsingMode.NoInput, we walk the directory structure
    # instead
    if args.mode == ParsingMode.NoInput:
        # parser.print_usage()

        def recursive_add(target):
            for child in sorted(os.listdir(target)):
                # Only show hiddent files if required
                if args.a or not child.startswith('.'):
                    full = os.path.join(target, child)
                    t.add_line(full)
                    if os.path.isdir(full):
                        try:
                            recursive_add(full)
                        except OSError as e:
                            print("Error Reading Target: {}".format(e),
                                  file=sys.stderr)

        try:
            recursive_add(args.target)
        except OSError as e:
            print("Error Reading Target: {}".format(e))
            exit(1)

    else:
        try:
            for line in sys.stdin:
                t.add_line(line)
        except KeyboardInterrupt:
            # Gracefully handle interrupt when stdin is not being piped and
            # user exits
            pass
        except UnicodeDecodeError:
            print("ERROR: tree.py could not read from stdin!")
            exit(1)


    for line in t.gen_lines():
        print(line)

    # print ("\n{} director{}, {} file{}"
    #        .format(t.dir_count, "y" if t.dir_count == 1 else "ies",
    #                t.file_count, "s"[t.file_count==1:]))


class TreeArgumentParser(argparse.ArgumentParser):

    """
    ArgumentParser to print customized help messages

    """

    def format_usage(self):
        return ('Usage: {} [-h]  [-i [none|normal|grep|g|n]] [other options ...] [target]'
                '\n'.format(os.path.basename(sys.argv[0])))

    def format_help(self):

        return (
            self.format_usage() + '\n'

            'A small utility that displays input from stdin in a tree-like structure    \n'
            '                                                                           \n'
            '-h, --help                 show the help message                           \n'
            '                                                                           \n'
            '-i, --mode, --input-mode   The input type. If ommitted, the default is     \n'
            '                           "auto", if -i is given with no argument, then   \n'
            '                           "normal" is used.                               \n'
            '                                                                           \n'
            '                           Values:                                         \n'
            '                            - auto:   (default when -i is not included in  \n'
            '                                      the command)                         \n'
            '                                      automatically try and detect whether \n'
            '                                      data is being piped to tree, and if  \n'
            '                                      so, use "normal" mode, otherwise use \n'
            '                                      "none" (checks if stdin is a tty)    \n'
            '                            - none:   don\'t read from stdin, display a    \n'
            '                                      target directory instead!            \n'
            '                            - normal: [or n] (default when -i is included  \n'
            '                                      but no value given)                  \n'
            '                                      Accept input which is one filename   \n'
            '                                      per line                             \n'
            '                            - grep:   [or g] Accept input that is like grep\n'
            '                                      multi-file output (i.e. "file: match"\n'
            '                                      for each line, with single files     \n'
            '                                      possibly appearing multiple times)   \n'
            '                                                                           \n'
            '-c, --color, --colour      Use color in the tree.                          \n'
            '                                                                           \n'
            '                           Values:                                         \n'
            '                            - auto:   try and automatically detect         \n'
            '                            - always                                       \n'
            '                            - none                                         \n'
            '                                                                           \n'
            '-a                         Include hidden files                            \n'
            '                                                                           \n'
            '-e, --encoding             Which characters should be used to draw the tree\n'
            '                                                                           \n'
            '                           Values:                                         \n'
            '                            - auto:   try and detect which would be best   \n'
            '                                      (default)                            \n'
            '                            - utf-8                                        \n'
            '                            - ascii                                        \n'
            '                                                                           \n'
        )


if __name__ == "__main__":
    main()