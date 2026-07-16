#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#     "mcp",
#     "requests",
#     "PySnooper",
#     "PyNaCl",
# ]
# ///
"""MCP server exposing SAP Commerce (hybris) tools to AI agents.

Provides structured JSON access to hybris flexible search queries and type introspection.
Uses the same HAC connection as the CLI tools (env vars: HYBRIS_HAC_URL, HYBRIS_USER, HYBRIS_PASSWORD).
"""

import json
import logging
import os
import subprocess
import sys
import time
import uuid

# Ensure the src directory is on the path so we can import existing modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp import FastMCP

import execute_flexible_search
from execute_flexible_search import ExecuteFlexibleSearchException
import execute_script
from execute_script import ScriptExecutionException
import import_impex
from import_impex import ImportImpexException

logging.getLogger("mcp").setLevel(logging.WARNING)

PROJECTS_DIR = os.environ.get('PROJECTS_DIR', '/media/sf_Projects')
SHOW_ITEM_DIRECT_PATH = os.path.join(PROJECTS_DIR, 'hybristools', 'flexible', 'ShowItemDirect')
SHOW_ITEM_GROOVY_PATH = os.path.join(PROJECTS_DIR, 'hybristools', 'groovy', 'showItem.groovy')

# Separator used for showItem.groovy output parsing (ASCII Record Separator)
HSI_SEPARATOR = '\x1e'

# sid columns and their full names for JSON output
SID_BOOLEAN_COLUMNS = {'U', 'L', 'E', 'D', 'J', 'O', 'R', 'PO'}
SID_COLUMN_RENAMES = {
    'firstType': 'definedInType',
    'qualifier': 'qualifier',
    'fieldType40': 'fieldType',
    'extension': 'extension',
    'U': 'unique',
    'L': 'localized',
    'E': 'editable',
    'D': 'dynamic',
    'J': 'jalo',
    'O': 'optional',
    'R': 'relation',
    'C': 'cardinality',
    'AH30': 'attributeHandler',
    'PO': 'partOf',
}

APPROVALS_DIR = os.path.join(os.path.expanduser('~'), '.hybristools', 'approvals')
DEFAULT_APPROVAL_TIMEOUT = 120

mcp = FastMCP("hybristools")


def _get_connection_params():
    address = os.environ.get('HYBRIS_HAC_URL', 'https://localhost:9002/hac')
    user = os.environ.get('HYBRIS_USER', 'admin')
    password = os.environ.get('HYBRIS_PASSWORD', 'nimda')
    return address, user, password


def _read_query_file(path):
    with open(path) as f:
        return f.read()


def _convert_sid_row(row):
    """Convert a sid result row to a cleaner JSON-friendly dict."""
    result = {}
    for old_key, new_key in SID_COLUMN_RENAMES.items():
        value = row.get(old_key)
        if old_key in SID_BOOLEAN_COLUMNS:
            result[new_key] = value == '1'
        elif old_key == 'C':
            result[new_key] = 'many' if value == '*' else 'one'
        else:
            result[new_key] = value
    return result


@mcp.tool()
def show_item_direct(type_name: str) -> str:
    """Show all fields/attributes directly accessible on a given SAP Commerce type.

    Returns structured information about each attribute: its defining type, qualifier name,
    field type, extension, and modifiers (unique, localized, editable, dynamic, jalo, optional,
    relation, cardinality, attributeHandler, partOf).

    Args:
        type_name: The SAP Commerce type name, e.g. 'Product', 'Media', 'Order', 'Customer'.
    """
    address, user, password = _get_connection_params()
    query = _read_query_file(SHOW_ITEM_DIRECT_PATH)

    try:
        rows = execute_flexible_search.execute_flexible_search_as_dicts(
            address, user, password, query, max_count=99999, parameters=[type_name]
        )
    except ExecuteFlexibleSearchException as e:
        return json.dumps({"error": str(e)})

    # Drop the PK column and rename/convert columns for clarity
    converted = [_convert_sid_row(row) for row in rows]
    return json.dumps(converted, indent=2)


@mcp.tool()
def execute_flexible_search_query(query: str, parameters: list[str] | None = None,
                                  max_results: int = 100) -> str:
    """Execute a flexible search query on SAP Commerce and return results as JSON.

    Flexible search is the SAP Commerce query language similar to SQL but using type system
    notation with curly braces, e.g. 'select * from {Product}'.

    The query can also be a path to a file containing the query. Use $1, $2 etc. as
    placeholders when providing parameters.

    Args:
        query: Flexible search query string or path to a file containing it.
            Examples:
            - "select * from {Product}"
            - "select * from {Order} where {code} = '$1'"
            - "select {code}, {name} from {Product} where {code} like '$1'"
        parameters: Optional list of values to substitute for $1, $2, etc. in the query.
        max_results: Maximum number of results to return. Defaults to 100.
    """
    address, user, password = _get_connection_params()

    # If query looks like a file path, read it
    if os.path.exists(query):
        query = _read_query_file(query)

    try:
        rows = execute_flexible_search.execute_flexible_search_as_dicts(
            address, user, password, query, max_count=max_results, parameters=parameters
        )
    except ExecuteFlexibleSearchException as e:
        return json.dumps({"error": str(e)})

    return json.dumps(rows, indent=2)


def _parse_show_item_output(output_text):
    """Parse the showItem.groovy output into a list of item dicts.

    The groovy script outputs lines in the format:
        fieldName<separator>value
        fieldName[locale]<separator>value
    Multiple items are separated by:
        ----------<separator>----------
    Lines starting with WARN:/DEBUG:/INFO:/ERROR: are skipped.
    Lines matching JSON objects (e.g. {}) are skipped (groovy artifacts).
    """
    import re

    items = []
    current_item = {}

    for line in output_text.split('\n'):
        line = line.rstrip()
        if not line:
            continue

        # Skip log lines
        if re.match(r'^(DEBUG|INFO|WARN|ERROR):', line):
            continue

        # Skip bare JSON-like lines (groovy execution artifacts)
        if re.match(r'^\{.*\}$', line):
            continue

        # Item separator
        if line.startswith('----------') and HSI_SEPARATOR in line:
            if current_item:
                items.append(current_item)
                current_item = {}
            continue

        if HSI_SEPARATOR not in line:
            continue

        field_name, _, value = line.partition(HSI_SEPARATOR)
        current_item[field_name] = value

    if current_item:
        items.append(current_item)

    return items


@mcp.tool()
def execute_groovy_script(script: str, parameters: list[str] | None = None,
                          rollback: bool = True) -> str:
    """Execute a Groovy script on SAP Commerce HAC and return the output.

    The script is executed in the HAC Scripting Console (Console -> Scripting Languages).
    Can be an inline script string or a path to a .groovy file.

    Args:
        script: Groovy script code or path to a .groovy file.
            Use $1, $2 etc. as placeholders when providing parameters.
        parameters: Optional list of values to substitute for $1, $2, etc.
        rollback: If true (default), execute in rollback mode. If false, changes are committed.
    """
    address, user, password = _get_connection_params()

    if os.path.exists(script):
        with open(script) as f:
            script = f.read()

    try:
        output = execute_script.execute_script_as_text(
            address, user, password, script, script_type='groovy',
            rollback=rollback, parameters=parameters
        )
    except ScriptExecutionException as e:
        return json.dumps({"error": str(e)})

    return output


@mcp.tool()
def show_item(type_name: str, qualifier: str, value: str) -> str:
    """Show all field values of a specific SAP Commerce item instance.

    Looks up an item by type, qualifier (field name), and value, then returns all its
    field values as JSON. This is the programmatic equivalent of the `hsi` command.

    For example, to see all fields of a Product with code 'myProduct':
        show_item("Product", "code", "myProduct")
    To look up any item by PK:
        show_item("Item", "PK", "8796093054980")

    Args:
        type_name: The SAP Commerce type, e.g. 'Product', 'Order', 'Media', 'Customer', 'Item'.
        qualifier: The field name to search by, e.g. 'code', 'uid', 'PK'.
        value: The value to match against the qualifier.
    """
    address, user, password = _get_connection_params()
    groovy_script = _read_query_file(SHOW_ITEM_GROOVY_PATH)

    try:
        output = execute_script.execute_script_as_text(
            address, user, password, groovy_script, script_type='groovy',
            rollback=True, parameters=[type_name, qualifier, value, HSI_SEPARATOR]
        )
    except ScriptExecutionException as e:
        return json.dumps({"error": str(e)})

    items = _parse_show_item_output(output)
    if not items:
        return json.dumps({"error": f"Cannot find type {type_name} with {qualifier} = {value}"})

    return json.dumps(items[0] if len(items) == 1 else items, indent=2)


def _wait_for_approval(content, description, approval_timeout=DEFAULT_APPROVAL_TIMEOUT, file_extension='.txt'):
    """Write content to a review file, create a marker file, send notification, and poll for approval.

    Generic approval gate for any destructive operation. The caller provides the content
    to review (e.g. impex, groovy script, update config) and a short description of the action.

    Returns (approved: bool, error_message: str | None).
    The marker file must be deleted by the user to approve.
    Writing 'no', 'reject', '0', 'denied', or 'deny' into the marker file rejects immediately.
    If the timeout expires, the action is rejected.
    """
    os.makedirs(APPROVALS_DIR, exist_ok=True)
    approval_id = uuid.uuid4().hex[:12]

    # Write content for human review
    review_file = os.path.join(APPROVALS_DIR, f'pending_{approval_id}{file_extension}')
    with open(review_file, 'w') as f:
        f.write(content)

    # Create marker file — user deletes it to approve
    marker_file = os.path.join(APPROVALS_DIR, f'DELETE_TO_APPROVE_{approval_id}')
    with open(marker_file, 'w') as f:
        f.write(
            f'DELETE THIS FILE TO APPROVE: {description}\n'
            f'Or write "no" into this file to reject immediately.\n'
            f'\n'
            f'Review the content at:\n'
            f'  {review_file}\n'
            f'\n'
            f'Timeout: {approval_timeout} seconds\n'
        )

    # Send desktop notification (best-effort)
    try:
        subprocess.run(
            ['notify-send', '-u', 'critical',
             f'Approval Required: {description}',
             f'Review: {review_file}\nDelete to approve: {marker_file}'],
            timeout=5, capture_output=True,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    logging.info(f'Waiting for approval of "{description}" (timeout {approval_timeout}s). '
                 f'Review: {review_file} — Delete to approve: {marker_file}')

    # Poll for approval
    start_time = time.time()
    try:
        while time.time() - start_time < approval_timeout:
            if not os.path.exists(marker_file):
                # Marker deleted → approved
                _cleanup_file(review_file)
                return True, None

            # Check if user wrote a rejection into the marker file
            try:
                with open(marker_file) as f:
                    marker_content = f.read().strip().lower()
                if marker_content in ('no', 'reject', '0', 'rejected', 'deny', 'denied'):
                    _cleanup_file(marker_file)
                    _cleanup_file(review_file)
                    return False, f'{description} rejected by user'
            except OSError:
                # File disappeared during read → approved
                _cleanup_file(review_file)
                return True, None

            time.sleep(1)
    except KeyboardInterrupt:
        _cleanup_file(marker_file)
        _cleanup_file(review_file)
        return False, f'{description} approval interrupted'

    # Timeout
    _cleanup_file(marker_file)
    _cleanup_file(review_file)
    return False, f'{description} approval timed out after {approval_timeout} seconds'


def _cleanup_file(path):
    try:
        os.remove(path)
    except OSError:
        pass


@mcp.tool()
def import_impex(impex: str, approval_timeout: int = DEFAULT_APPROVAL_TIMEOUT) -> str:
    """Import ImpEx into SAP Commerce (destructive operation — requires manual approval).

    This tool writes the impex to a review file and creates a marker file on disk.
    A desktop notification is sent. To approve, DELETE the marker file. To reject,
    write "no" into it or wait for the timeout.

    File locations are printed in the tool output and in the notification.

    Args:
        impex: ImpEx script content to import.
        approval_timeout: Seconds to wait for approval before auto-rejecting (default 120).
    """
    approved, error = _wait_for_approval(impex, description='ImpEx Import',
                                         approval_timeout=approval_timeout, file_extension='.impex')
    if not approved:
        return json.dumps({"error": error})

    address, user, password = _get_connection_params()
    try:
        result = import_impex.import_impex_text(address, user, password, impex)
    except ImportImpexException as e:
        return json.dumps({"error": str(e)})

    return json.dumps({"result": result})


if __name__ == "__main__":
    mcp.run()
