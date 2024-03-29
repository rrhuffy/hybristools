#!/usr/bin/env python3
import argparse
import logging
import re

import time

from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

from lib import helpers
from lib import hybris_argparse_helper
from lib import hybris_selenium_helper
from lib import logging_helper
from lib import selenium_helper

ACTIONS = ['update', 'initialize']
DEFAULT_SELECTED_CHECKBOXES = ['Update running system', 'Create essential data', 'Localize types']

parser = argparse.ArgumentParser('Script that executes update or initialize hybris server')
hybris_argparse_helper.add_hybris_hac_arguments(parser)
parser.add_argument('--pause', action='store_true', help='Pause before important steps')
parser.add_argument('--sleep', action='store_true', help='Add 10s sleep before clicking update/initialize')
parser.add_argument('--headless', action='store_true', help='Use headless browser')
parser.add_argument('action', help='Action to execute', choices=ACTIONS)
parser.add_argument('extensions', type=str, nargs='*',
                    help='extensions to toggle: '
                         '"," is extensions separator, '
                         '":" is option separator. '
                         'For example: "Update running system,Create essential data,Localize types" '
                         'or "ext1:key11:long val11:k12:val12,ext2,long ext3:k31:v31"')
logging_helper.add_logging_arguments_to_parser(parser)
args = parser.parse_args()
driver = selenium_helper.create_firefox_webdriver(args.headless)

logging.debug(f'Logging into {args.address} as {args.user}')
hybris_selenium_helper.log_into(driver, args.address, args.user, args.password)

target_url = ''
if args.action == 'update':
    target_url = f'{args.address}/platform/update'
elif args.action == 'initialize':
    target_url = f'{args.address}/platform/init'

logging.debug(f'Opening {target_url}')
driver.get(target_url)

print('Waiting until "Project data settings" is loaded (expecting at least "core" element loaded)')
WebDriverWait(driver, 15).until(expected_conditions.text_to_be_present_in_element(
    (By.XPATH, '//div[@id="projectData"]//label[text()="core"]'),
    'core'))

if args.extensions:
    logging.debug(f'Extensions to update: {" ".join(args.extensions)}')
    extensions_with_options = []
    for extension in ' '.join(args.extensions).split(','):
        extension_split = extension.split(':')
        extension_name = extension_split[0]
        key_val_pairs = zip(*[iter(extension_split[1:])] * 2)
        extensions_with_options.append([extension_name, key_val_pairs])

    for extension_name, extension_options in extensions_with_options:
        print(f'Toggling extension "{extension_name}"')
        if extension_name in DEFAULT_SELECTED_CHECKBOXES:
            # click on text, because we have multiple sibling inputs in div with id "requiredForInit"
            driver.find_element(By.XPATH, f'//label[text()="{extension_name}"]').click()
        else:
            # click on sibling input because clicking on text is not selecting them; we have div per each input+label
            try:
                element = driver.find_element(By.XPATH, f'//label[text()="{extension_name}"]/../input')
            except ElementClickInterceptedException:  # fallback for 2011
                element = driver.find_element(By.XPATH, f'//label[text()="{extension_name}"]')
            driver.execute_script("arguments[0].scrollIntoView(true);", element)
            element.click()
        for key, value in extension_options:
            print(f'Selecting "{key}" to "{value}"')
            driver.find_element(By.XPATH,
                                f'//label[text()="{extension_name}"]' +
                                f'/..//dt[text()="{key}"]' +
                                f'/following-sibling::*[1]//option[@value="{value}"]').click()

if args.pause:
    helpers.pause_with_enter_or_exit(f'After selecting extensions, before clicking {args.action} button',
                                     lambda: driver.quit())

if args.sleep:
    print(f'After selecting extensions, before clicking {args.action} button, starting 10s sleep...', end='',
          flush=True)
    time.sleep(10)
    print('done')

button_execute = driver.find_element(By.CLASS_NAME, 'buttonExecute')
selenium_helper.wait_until_element_is_displayed(button_execute)
button_execute.click()
if args.action == 'initialize':
    driver.switch_to.alert.accept()
status_element = driver.find_element(By.ID, 'inner')
last_text = ''

while True:
    current_text = status_element.text
    new_text = current_text.replace(last_text, '')  # remove old printed text from new text
    new_text_clean = re.sub(r'\n+', '\n', new_text).strip()  # remove duplicated \n and trim trailing and leading \s
    if new_text_clean != '':
        print(new_text_clean, flush=True)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    if 'FINISHED' in new_text_clean:
        break
    last_text = current_text
    time.sleep(0.5)

if args.pause:
    input(f'After {args.action}. Press enter to exit...')

driver.quit()
