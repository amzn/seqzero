#!/usr/bin/env python3

from __future__ import print_function

import json
import sys
import argparse
import re
import os

def update_quotes(token, in_squote, in_dquote):
    for char in token:
        if char == "'" and (not in_dquote):
            in_squote = not in_squote
        elif char == '"' and (not in_squote):
            in_dquote = not in_dquote
    return in_squote, in_dquote

def tokenise(query):
    """Adjust a query to have quotes and braces as tokens.

    >>> tokenise('test "%test%" test')
    'test "% test %" test'
    >>> tokenise("test '%test%' test")
    "test '% test %' test"
    >>> tokenise('test "test" test')
    'test " test " test'
    >>> tokenise("test 'test' test")
    "test ' test ' test"
    >>> tokenise("min( test )")
    'min ( test )'
    >>> tokenise("test test.test")
    'test test . test'
    >>> tokenise("test testalias0.test")
    'test test alias0 . test'
    >>> tokenise("test TESTalias0")
    'test TEST alias0'
    """
    tokens = []
    in_squote, in_dquote = False, False
    for token in query.split():
        # Handle prefixes
        if not (in_squote or in_dquote):
            if token.startswith("'%") or token.startswith('"%'):
                if token[0] == "'": in_squote = True
                else: in_dquote = True
                tokens.append(token[:2])
                token = token[2:]
            elif token.startswith("'") or token.startswith('"'):
                if token[0] == "'": in_squote = True
                else: in_dquote = True
                tokens.append(token[0])
                token = token[1:]

        # Handle mid-token aliases
        if not (in_squote or in_dquote):
            parts = token.split(".")
            if len(parts) == 2:
                table = parts[0]
                field = parts[1]
                if 'alias' in table:
                    table_parts = table.split('alias')
                    tokens.append('alias'.join(table_parts[:-1]))
                    tokens.append('alias'+ table_parts[-1])
                else:
                    tokens.append(table)
                tokens.append('.')
                token = field

        # Handle aliases without field name.
        if not (in_squote or in_dquote):
            m = re.search(r"(?P<table>[A-Z_]+)(?P<alias>alias\d+)", token)
            if m:
                tokens.append(m.group("table"))
                tokens.append(m.group("alias"))
                continue

        # Handle suffixes
        if (in_squote and token.endswith("%'")) or \
                (in_dquote and token.endswith('%"')):
            tokens.append(token[:-2])
            tokens.append(token[-2:])
        elif (in_squote and token.endswith("'")) or \
                (in_dquote and token.endswith('"')):
            tokens.append(token[:-1])
            tokens.append(token[-1])
        elif (not (in_squote or in_dquote)) and len(token) > 1 and token.endswith("("):
            tokens.append(token[:-1])
            tokens.append(token[-1])
        else:
            tokens.append(token)
        in_squote, in_dquote = update_quotes(token, in_squote, in_dquote)

    return ' '.join(tokens)

def convert_instance(data):
    var_sql = None
    var_sql = data["sql"][0]
    for sentence in data["sentences"]:
        if args.query_split:
            if data['query-split'] == 'dev':
                continue
            elif data['query-split'] == 'test':
                continue
        else:
            if sentence['question-split'] == 'dev':
                continue
            elif sentence['question-split'] == 'test':
                continue
        text = sentence['text']
        sql = var_sql # Needed to do variable replacement correctly

        # Variable replacement
        if not args.keep_vars:
            for name in sentence['variables']:
                value = sentence['variables'][name]
                if len(value) == 0:
                    for variable in data['variables']:
                        if variable['name'] == name:
                            value = variable['example']
                text = value.join(text.split(name))
                if not args.keep_sql_vars:
                    sql = value.join(sql.split(name))

        # Tokenise
        if args.tokenise_sql:
            sql = tokenise(sql)

        # Select the output file
        output_file = out_train
        
        if args.to_stdout:
            output_file = sys.stdout

        print(text, "|||", sql, file=output_file)
        break

def make_dir(path):
    dir_path = os.path.dirname(path)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Reads json files with data and produces information in a convenient one line per question format.')
    parser.add_argument('--keep_vars', help='Do not replace the varibales with values.', action='store_true')
    parser.add_argument('--tokenise_sql', help='Apply our tokenisation scheme to the SQL.', action='store_true')
    parser.add_argument('--query_split', help='Split based on queries, not questions.', action='store_true')
    parser.add_argument('--keep_sql_vars', help='Keep vars just in SQL.', action='store_true')
    parser.add_argument('--to_stdout', help='Print all data to stdout.', action='store_true')
    parser.add_argument('--output_prefix', help='Filename prefix output_file for output files.')
    parser.add_argument('--input_file', help='Filename for input files.')
    args = parser.parse_args()

    make_dir(args.output_prefix)

    out_train = open(args.output_prefix +'.train', 'w')

    data = json.loads(open(args.input_file).read())
    if type(data) == list:
        for instance in data:
            convert_instance(instance)
    else:
        convert_instance(data)

    out_train.close()
