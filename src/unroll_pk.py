#!/usr/bin/env python3

# TODO: UX improvement: save cursor position, write original data into stderr, restore cursor position,
#  then write result in stdout overwriting previous stderr (may need to clear whole screen to avoid characters left from previous stderr stream)

# TODO: HANA and Azure SQL crashes when doing UNION ALL on different columns, fix that so unroll_pk can be used in cloud

# TODO: separate PK -> [Type](field)value and provide extractPk command

# TODO: BUG: when analyse#0 returns some pk it is also unwrapped...even if it is a "pk"

import argparse
import inspect
import logging
import re

import requests
import sys

from lib import argparse_helper
from lib import hybris_argparse_helper
from lib import hybris_requests_helper
from lib import logging_helper
from lib import requests_helper
from lib import shell_helper

# TODO: figure out how to write eg. PaymentInfo but effectively work for subtypes like InvoicePaymentInfo
# TODO: implement multiple keys, for example CatalogVersion should use catalog.id+version, or CartEntry: pk+product
# TODO: leave OOTB types here and read additional ones from environment variable
CUSTOM_TYPE_TO_UNIQUE_QUALIFIER = {'Warehouse': 'code',
                                   'PaymentInfo': 'code',
                                   'InvoicePaymentInfo': 'code',
                                   'SiteMapPage': 'code',
                                   'SolrEndpointUrl': 'url',
                                   'OrderEntry': 'product',
                                   'CartEntry': 'product',
                                   'PatchExecution': 'patchId',
                                   'SalesAreaCustomerData': 'salesArea',
                                   # 'CatalogVersion': 'catalog',
                                   'CatalogVersion': 'version',
                                   'CatalogVersionSyncCronJobHistory': 'statusLine',
                                   'ClassAttributeAssignment': 'classificationAttribute'
                                   }


def get_key_replacements(item_pk_set, session_, csrf_token_, address, analyse_long, user='admin'):
    user = user or 'admin'
    sql_correct_item_pk_list = ','.join(item_pk_set)
    if sql_correct_item_pk_list:
        # original query to get item pk, Type code and unique qualifiers:
        # SELECT
        #     {i.pk},
        #     {t.code},
        #     {ad.qualifier}
        # FROM {
        #     AttributeDescriptor AS ad
        #     JOIN Type AS t ON {ad.EnclosingType} = {t.PK}
        #     JOIN Item AS i ON {t.PK} = {i.itemType}
        # }
        # WHERE
        #     {ad.unique} = '1'
        # AND {i.PK} IN ('1','2','3')

        # but time needed to complete with 12 PK was:
        # real    5m18,650s
        # user    0m0,345s
        # sys     0m0,054s
        # (and about 70s for a single query with just one PK...)

        # it was mostly because doing a query with {Item} is being unwrapped to hundreds of specific tables
        # that had to be joined with {Type} (also being unwrapped) and {AttributeDescriptor}

        # after splitting into separate queries times changed to:
        # real    0m3,583s
        # user    0m0,309s
        # sys     0m0,084s

        # get Type PK from Item PK
        item_pk_to_type_template = 'Select {pk}, {itemType} from {Item} where {PK} in ($ALL_PK_TO_CHECK)'
        item_pk_to_type_query = item_pk_to_type_template.replace('$ALL_PK_TO_CHECK', sql_correct_item_pk_list)
        logging.debug(f'item_pk_to_type_query = {item_pk_to_type_query}')

        flex_data = {'flexibleSearchQuery': item_pk_to_type_query, '_csrf': csrf_token_,
                     'maxCount': len(item_pk_set), 'user': user, 'locale': 'en', 'commit': True}
        try:
            flex_post_result = session_.post(address + '/console/flexsearch/execute', data=flex_data)
        except requests.exceptions.ChunkedEncodingError:
            logging.error(f"ChunkedEncodingError while sending POST to {address + '/console/flexsearch/execute'}")
            return []

        if 500 <= flex_post_result.status_code:
            logging.error(f'Could not get pk to item type mapping, received status {flex_post_result.status_code} '
                          f'when executed {item_pk_to_type_query}')
            return []

        result_json = flex_post_result.json()
        result_list_item_pk_to_type = result_json['resultList']
        logging.debug(f'result_json[result_list_item_pk_to_type] = {result_list_item_pk_to_type}')

        if result_list_item_pk_to_type:
            item_pk_to_type_pk_dict = {item_pk: type_pk for item_pk, type_pk in result_list_item_pk_to_type}
            type_pk_set = set(item_pk_to_type_pk_dict.values())
            sql_correct_type_pk_list = ','.join(type_pk_set)

            # get Type name from Type PK
            type_pk_to_type_name_template = 'select {pk}, {code} from {Type} where {PK} in ($ALL_PK_TO_CHECK)'
            type_pk_to_type_name_query = type_pk_to_type_name_template.replace('$ALL_PK_TO_CHECK',
                                                                               sql_correct_type_pk_list)
            logging.debug(f'type_pk_to_type_name_query = {type_pk_to_type_name_query}')

            flex_data = {'flexibleSearchQuery': type_pk_to_type_name_query, '_csrf': csrf_token_,
                         'maxCount': len(type_pk_set), 'user': user, 'locale': 'en', 'commit': True}
            flex_post_result = session_.post(address + '/console/flexsearch/execute', data=flex_data)
            result_json = flex_post_result.json()
            result_list_type_pk_to_type_name = result_json['resultList']
            logging.debug(f'result_json[result_list_type_pk_to_type_name] = {result_list_type_pk_to_type_name}')

            type_pk_to_type_name_dict = {type_pk: type_name for type_pk, type_name in result_list_type_pk_to_type_name}

            # TODO: don't query (from now till end) for PKs of types included in CUSTOM_TYPE_TO_UNIQUE_QUALIFIER
            type_pk_to_qualifier_dict = dict()
            for type_pk, type_name in type_pk_to_type_name_dict.items():
                if type_name in CUSTOM_TYPE_TO_UNIQUE_QUALIFIER:
                    type_pk_to_qualifier_dict[type_pk] = CUSTOM_TYPE_TO_UNIQUE_QUALIFIER[type_name]

            # get unique qualifiers from Type PK
            type_pk_to_qualifier_template = """
            select {enclosingType}, {qualifier} 
            from {AttributeDescriptor} 
            where {unique} = '1' and {enclosingType} in ($ALL_PK_TO_CHECK)""".strip()

            type_pk_to_qualifier_query = type_pk_to_qualifier_template.replace('$ALL_PK_TO_CHECK',
                                                                               sql_correct_type_pk_list)
            logging.debug(f'type_pk_to_qualifier_query = {type_pk_to_qualifier_query}')

            # because one type can have multiple unique fields we need to adjust maxCount by maximum number of unique fields

            # TODO: FlexibleSearch: xf "select * from {PageTemplate} where {name} like '%Product Details%'" -a
            # Is giving:
            # PK    | p_name                        | p_active | p_catalogversion                | p_frontendtemplatename     | p_uid
            # 8x PK | Product Details Page Template | true     | [CatalogVersion](version)Online | product/productLayout1Page | ProductDetailsPageTemplate

            # CatalogVersion example:
            # qualifier | fieldType        | extension | uniq | localized | editable
            # version   | java.lang.String | catalog   | 1    | 0         | 1
            # catalog   | Catalog          | catalog   | 1    | 0         | 0

            # Catalog example:
            # qualifier | fieldType        | extension | uniq | localized | editable
            # id        | java.lang.String | catalog   | 1    | 0         | 1

            # JobLogLevel example:
            # qualifier | extension | uniq
            # code      | core      | 1
            # itemtype  | core      | 1

            # to check maximum number of unique fields by type run this flexible search:
            # Select {ad.enclosingType} as typePK, {t.code} as TypeCode, count({ad.PK}) as uniqQualifiers,
            # GROUP_CONCAT(DISTINCT {ad.qualifier}) as qualifiers
            # from {AttributeDescriptor as ad join Type as t on {ad.enclosingType}={t.pk}}
            # where {ad.unique} = '1' group by {ad.enclosingType} order by count({ad.PK}) desc

            maximum_supported_unique_fields_by_type = 6  # you should update this value sometimes

            flex_data = {'flexibleSearchQuery': type_pk_to_qualifier_query, '_csrf': csrf_token_,
                         'maxCount': len(type_pk_set) * maximum_supported_unique_fields_by_type,
                         'user': user, 'locale': 'en', 'commit': True}
            flex_post_result = session_.post(address + '/console/flexsearch/execute', data=flex_data)
            result_json = flex_post_result.json()
            result_list_type_pk_to_qualifier = result_json['resultList']
            logging.debug(f'result_json[result_list_type_pk_to_qualifier] = {result_list_type_pk_to_qualifier}')
            if result_list_type_pk_to_qualifier or type_pk_to_qualifier_dict:
                preferred_field_names = ['id', 'uid', 'code', 'qualifier']
                not_preferred_field_names = ['catalogVersion']

                if result_list_type_pk_to_qualifier:
                    for type_pk, qualifier in result_list_type_pk_to_qualifier:
                        if type_pk in type_pk_to_qualifier_dict and qualifier not in preferred_field_names:
                            continue
                        if qualifier in not_preferred_field_names:
                            continue

                        if type_pk in type_pk_to_qualifier_dict:
                            current_type_name = type_pk_to_type_name_dict[type_pk]
                            current_qualifier = type_pk_to_qualifier_dict[type_pk]
                            logging.debug(f'Type "{current_type_name}" has already qualifier '
                                          f'"{current_qualifier}" but it will now be overridden by "{qualifier}"')

                        type_pk_to_qualifier_dict[type_pk] = qualifier

                # TODO: HANA and Azure SQL crashes when doing UNION ALL on different columns, where MySQL works...
                # TODO: Group by type_name and execute multiple statements, one per type (with multiple PK per type)
                # TODO 2: Before changes do a refactor to simplify executing FS
                # This is working on Mysql (b2bdevweb01)
                # xf "SELECT * FROM ({{SELECT {PK}, {code} FROM {Media} WHERE {PK} = '8796101738526'}} UNION ALL {{SELECT {PK}, {catalogVersion} FROM {ProductBrandSpecificContent} WHERE {PK} = '8796094147325'}}) uniontable"
                # This is not working on HANA (b2bpprodweb01)
                # xf "SELECT * FROM ({{SELECT {PK}, {code} FROM {Media} WHERE {PK} = '8802523611166'}} UNION ALL {{SELECT {PK}, {catalogVersion} FROM {ProductBrandSpecificContent} WHERE {PK} = '8796096277245'}}) uniontable"

                # TODO: check env var with dict [url,sql], if no entry try mssql for external, mysql for localhost; if error try second one and save in dict/env
                subquery_template_mysql = "{{{{SELECT {{PK}}, {{{qualifier}}} FROM {{{type_name}}} WHERE {{PK}} = '{item_pk}'}}}}"
                subquery_template_mssql = "{{{{SELECT CONVERT(nvarchar(100),{{PK}}) as PK, CONVERT(nvarchar(100),{{{qualifier}}}) as QUALIFIER FROM {{{type_name}}} WHERE {{PK}} = '{item_pk}'}}}}"
                subquery_template = subquery_template_mysql if 'localhost' in address else subquery_template_mssql

                # example for MSSQL (but then it won't work in MySQL...)
                # subquery_template = "{{{{SELECT {{PK}}, CONVERT(CHAR, {{{qualifier}}}) as v FROM {{{type_name}}} WHERE {{PK}} = '{item_pk}'}}}}"
                subquery_template_list = list()
                for item_pk, type_pk in item_pk_to_type_pk_dict.items():
                    try:
                        if type_pk in type_pk_to_type_name_dict:
                            type_name = type_pk_to_type_name_dict[type_pk]
                        qualifier = type_pk_to_qualifier_dict[type_pk]
                        last_frame = inspect.currentframe()
                        _globals = last_frame.f_globals
                        _locals = last_frame.f_locals
                        subquery = subquery_template.format_map(dict(list(_globals.items()) + list(_locals.items())))
                        subquery_template_list.append(subquery)
                    except KeyError as error:  # couldn't find PK replacement
                        continue

                subqueries_joined_by_union_all = ' UNION ALL '.join(subquery_template_list)
                final_query = f'SELECT * FROM ({subqueries_joined_by_union_all}) uniontable'
                logging.debug(f'final_query = {final_query}')

                flex_data = {'flexibleSearchQuery': final_query, '_csrf': csrf_token_,
                             'maxCount': len(subquery_template_list),
                             'user': user, 'locale': 'en', 'commit': True}
                flex_post_result = session_.post(address + '/console/flexsearch/execute', data=flex_data)
                result_json = flex_post_result.json()
                if 'exception' in result_json and result_json['exception'] is not None:
                    # TODO: extract method for FS query with this check
                    print(
                        f'ERROR: Caught exception when executing query: {final_query}, exception was: {result_json["exception"]["message"]}')
                result_list_final_query = result_json['resultList']
                logging.debug(f'result_json[result_list_final_query] = {result_list_final_query}')

                # TODO: if can't find unique element try to find code/id/uid
                if result_list_final_query:
                    item_pk_to_unique_value_dict = {pk: val for pk, val in result_list_final_query}

                    # PK can also appear in list like below:
                    # column = ',#1,8796093055008,'
                    # key = '8796093055008'

                    key_to_string = []
                    for key in item_pk_to_unique_value_dict.keys():
                        try:
                            type_pk = item_pk_to_type_pk_dict[key]
                            repl_type = type_pk_to_type_name_dict[type_pk]
                            repl_uniq_field = type_pk_to_qualifier_dict[type_pk]
                            repl_uniq_value = item_pk_to_unique_value_dict[key]

                            if analyse_long:
                                replace_string = f'[{repl_type}]({repl_uniq_field}){repl_uniq_value}'
                            else:
                                replace_string = f'_{repl_uniq_value}'

                            key_to_string.append([key, replace_string])
                        except KeyError:
                            continue
                    return key_to_string


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Script for finding info about Item with given PK')
    hybris_argparse_helper.add_hybris_hac_arguments(parser)
    parser.add_argument('text', help='string with pk to unroll or "-" if piping')
    parser.add_argument('--analyse-short', '-a', action='store_true', help='Analyse PK and print short item info')
    parser.add_argument('--no-analyse', '-A', action='store_true', help='Do not analyse PK to get info about them')

    logging_helper.add_logging_arguments_to_parser(parser)

    default_entries_limit = shell_helper.get_terminal_height() - 2
    parser.set_defaults(limit=default_entries_limit)
    args = parser.parse_args()

    session, address = requests_helper.get_session_with_basic_http_auth_and_cleaned_address(args.address)
    assert address, 'You must provide an address!'

    credentials = {'user': args.user, 'password': args.password}
    csrf_token = hybris_requests_helper.log_into_hac_and_return_csrf_or_exit(session, address, credentials)
    text = argparse_helper.get_text_from_string_or_file_or_pipe(args.text)
    logging.debug(f'text: {text}')

    if args.no_analyse:
        try:
            print(text.rstrip())
        except BrokenPipeError:
            sys.exit(0)
        sys.exit(0)

    # clean_or_dummy="sed -E s/\w+Model\s\(([0-9]{13})@[0-9]+\)/\1/g"
    # TODO: unit tests with examples:
    # [CategoryModel (8796128182414)]
    # [CategoryModel (8796128182414), CategoryModel (8796097544334)]
    text = re.sub(r'\w+Model\s\(([0-9]{13})(?:@[0-9]+)?\)', r'\1', text)
    logging.debug(f'text after cleaning XModel (PK@Y): {text}')

    # TODO: unroll pk until there are no more pk to check or there is empty output from current pk check
    for analyse_iteration in range(3):
        logging.debug(f'-----------Analyse #{analyse_iteration}')
        # TODO: extract checking PK to check_pk.py with input \d{13} and output: Type, unique field(s?) name + value

        # TODO: check if given types aren't in dictionary already, if not then save results as {Type: [uniqueName1,uN2]}
        # TODO: use [hostName,url] as key, to invalidate caches on new machine or other servers)

        # TODO: allow two fields per type in dictionary to for example pick 2 values from {Address}

        # get all 13 digit numbers (except current 'PK' column), because they may be a PK of something
        item_pk_set = {match for match in re.findall(r'(?<!pk\036)\d{13}', text, re.IGNORECASE)}
        logging.debug(f'item_pk_set = {item_pk_set}')
        if item_pk_set:
            _key_to_string = get_key_replacements(item_pk_set, session, csrf_token, address, not args.analyse_short,
                                                  credentials['user'])
            logging.debug(f'_key_to_string = {_key_to_string}')
            if _key_to_string:
                for key, replace_string in _key_to_string:
                    logging.debug(f'replacing {key} -> {replace_string} (repr: {replace_string!r})')
                    text = text.replace(key, replace_string)

    try:
        for line in text.split('\n'):
            print(line.rstrip())
    except BrokenPipeError:
        sys.exit(0)
