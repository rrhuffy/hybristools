#!/usr/bin/env python3
# example to confirm/show N+1 problem:
# jdbc_logger.py --params --print --script="flexibleSearchService.search(\"select {pk} from {BaseStore} where {pk}='8796256896989'\").result.each{println it.getWarehouses()}"
# SELECT  item_t0.PK  FROM basestore item_t0 WHERE ( item_t0.PK ='8796256896989') AND (item_t0.TypePkString=8796112683090 )
# SELECT * FROM basestore WHERE PK=8796256896989
# SELECT * FROM languages WHERE PK=8796093055008
# SELECT  item_t1.PK  FROM basestore2warehouserel item_t0 JOIN warehouses item_t1 ON  item_t0.TargetPK = item_t1.PK  WHERE ( item_t0.Qualifier  = 'BaseStore2WarehouseRel' AND  item_t0.SourcePK  = 8796256896989 AND  item_t0.LanguagePK  IS NULL) AND (item_t1.TypePkString=8796112453714 ) order by  item_t0.SequenceNumber  ASC , item_t0.PK  ASC
# SELECT * FROM warehouses WHERE PK=8796256896981
# commit

import argparse
import re
import tempfile

from lib import hybris_argparse_helper
from lib import hybris_requests_helper
from lib import logging_helper
from lib import requests_helper
import execute_script
import logging

logging_helper.run_ipdb_or_pdb_on_exception()

logging.basicConfig(level=logging.INFO,
                    format='%(levelname)s:%(message)s',
                    handlers=[
                        # logging.FileHandler(f'{__file__}.log'),
                        logging.StreamHandler()
                    ])

parser = argparse.ArgumentParser('Script for jdbc analysis')
parser.add_argument('--traces', action='store_true', help='Enable traces')
parser.add_argument('--params', action='store_true', help='Enable params')
parser.add_argument('--times', action='store_true', help='Enable printing time of queries')
parser.add_argument('--no-blacklist', action='store_true', help='Prevent removing blacklisted queries')
parser.add_argument('--no-clear-cache', action='store_true', help='Prevent clearing caches')
parser.add_argument('--script', help='Groovy script to execute')
parser.add_argument('--print', action='store_true', help='Print results in stdout instead of saving in file')
hybris_argparse_helper.add_hybris_hac_arguments(parser)
logging_helper.add_logging_arguments_to_parser(parser)
args = parser.parse_args()

session, address = requests_helper.get_session_with_basic_http_auth_and_cleaned_address(args.address)

credentials = {'user': args.user, 'password': args.password}
hybris_requests_helper.log_into_hac_and_return_csrf_or_exit(session, address, credentials)

main_page = session.get(address + '/monitoring/database')
csrf_token = re.search(r'name="_csrf"\s+value="(.+?)"\s*/>', main_page.text).group(1)


def post_with_error_check(address_, csrf_token):
    response = session.post(address_, headers={'X-CSRF-TOKEN': csrf_token})
    if response.status_code > 400:
        raise Exception(f'Cannot run POST on {address_} because {response} {response.__dict__}')


# TODO execute from groovy script
post_with_error_check(f"{address}/monitoring/database/stacktrace/{'true' if args.traces else 'false'}", csrf_token)
post_with_error_check(f"{address}/monitoring/database/params/{'true' if args.params else 'false'}", csrf_token)

if not args.no_clear_cache:
    # TODO: refactor execute_script.py to allow reusing session
    script = '''cacheRegionProvider.getRegions().each{it.clearCache()}
    net.sf.ehcache.CacheManager.ALL_CACHE_MANAGERS.each{it.clearAll()}
    de.hybris.platform.core.Registry.getCurrentTenant().getCache().clear()
    org.apache.log4j.Logger.getLogger(de.hybris.platform.servicelayer.internal.jalo.ScriptingJob).info("Cleared caches")'''
    scripting_address = address + '/console/scripting'
    execute_script._internal_execute_script(session, scripting_address, csrf_token, script, 'groovy', False)

post_with_error_check(address + '/monitoring/database/clearlog', csrf_token)

post_with_error_check(address + '/monitoring/database/logs/true', csrf_token)

if args.script:
    if not args.print:
        logging.info(f'Executing script: {args.script}')
    groovy_script_response = execute_script._internal_execute_script(session, scripting_address, csrf_token,
                                                                     args.script, 'groovy', False)
    if not args.print:
        logging.info(f'Result: {groovy_script_response}')
else:
    input('Logging started, press Enter to stop logging and save results')

post_with_error_check(address + '/monitoring/database/logs/false', csrf_token)

logs = session.get(address + '/monitoring/database/logs/download?downloadSize=-1')

if args.no_blacklist:
    BLACKLIST = []
else:
    BLACKLIST = ['FROM composedtypes', 'FROM metainformations', 'FROM SYSTEMINIT', 'FROM scripts', 'commit',
                 'tasks_aux_queue', 'tasks_aux_workers', 'tasks_aux_scheduler', 'taskconditions', 'INSERT INTO pgrels']

filtered_logs_list = []
for line in logs.text.rstrip('\n').split('\n'):
    if any(blacklisted in line for blacklisted in BLACKLIST):
        logging.debug(f'filtered out line: {line}')
        continue
    columns = line.split('|')
    if columns == '':
        continue

    # params + traces
    # 113|master|250918-14:12:00:529|1 ms|statement|SELECT * FROM users WHERE PK=?|SELECT * FROM users WHERE PK=8796093087748|PreparedStatementImpl:52:DataSourceImplFactory:101:...
    # params
    # 80|master|250918-14:10:56:440|1 ms|statement|SELECT * FROM users WHERE PK=?|SELECT * FROM users WHERE PK=8796093087748
    # traces
    # 77|master|250918-14:14:44:346|0 ms|statement|SELECT * FROM users WHERE PK=?|PreparedStatementImpl:52:DataSourceImplFactory:101:...
    # nothing
    # 99|master|250918-14:10:41:51|0 ms|statement|SELECT * FROM users WHERE PK=?

    # last line has len(columns)==6 with empty last one
    # 52|master|250918-14:20:47:400|1 ms|commit|

    if args.params and args.traces:
        if len(columns) == 6:
            line = columns[4] + ',' + columns[5]
        else:
            line = columns[6] + ',' + columns[7]
    elif args.params:
        if len(columns) == 6 and columns[5] == '':
            line = columns[4]
        else:
            line = columns[6]
    elif args.traces:
        if len(columns) == 6:
            line = columns[4] + ',' + columns[5]
        else:
            line = columns[5] + ',' + columns[6]
    else:
        if len(columns) == 6 and columns[5] == '':
            line = columns[4]
        else:
            line = columns[5]

    if args.times:
        line = columns[3] + ":" + line

    filtered_logs_list.append(line)
filtered_logs = '\n'.join(filtered_logs_list)

if args.print:
    print(filtered_logs)
else:
    with tempfile.NamedTemporaryFile(delete=False) as fp:
        fp.write(filtered_logs.encode())
        logging.info(f'output saved in {fp.name}')
        logging.info(f'you can use: cat {fp.name} | p')
    total_lines_count = len(filtered_logs.split("\n"))
    logging.info(f'total lines: {total_lines_count}')
    logging.info(f'first 500 characters of output:\n{filtered_logs[:500]}')
