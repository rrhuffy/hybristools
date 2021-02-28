#!/usr/bin/env python3
import argparse
import logging
import re

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

from lib import argparse_helper
from lib import helpers
from lib import logging_helper
from lib import selenium_helper

parser = argparse.ArgumentParser('Script that executes update hybris server')
argparse_helper.add_hybris_hac_arguments(parser)
parser.add_argument('--pause', action='store_true', help='Pause before important steps')
parser.add_argument('--sleep', action='store_true', help='Add 10s sleep before clicking update')
parser.add_argument('--headless', action='store_true', help='Use headless browser')
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
selenium_helper.log_into(driver, args.address, args.user, args.password)

logging.debug(f'Opening {args.address}/platform/update')
driver.get(args.address + '/platform/update')

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
        driver.find_element_by_xpath(f'//label[text()="{extension_name}"]').click()
        for key, value in extension_options:
            print(f'Selecting "{key}" to "{value}"')
            driver.find_element_by_xpath(
                f'//label[text()="{extension_name}"]' +
                f'/..//dt[text()="{key}"]' +
                f'/following-sibling::*[1]//option[@value="{value}"]').click()

if args.pause:
    helpers.pause_with_enter_or_exit('After selecting extensions, before clicking update button', lambda: driver.quit())

if args.sleep:
    print('After selecting extensions, before clicking update button, starting 10s sleep...', end='', flush=True)
    time.sleep(10)
    print('done', flush=True)

button_execute = driver.find_element_by_class_name('buttonExecute')
selenium_helper.wait_until_element_is_displayed(button_execute)
# TODO: scroll to button to avoid problems when using browser during 10s pause:
# selenium.common.exceptions.WebDriverException: Message:
# unknown error: Element <button class="buttonExecute">...</button> is not clickable at point (84, 9).
# Other element would receive the click: <label for="initMethod">...</label>
button_execute.click()
status_element = driver.find_element_by_id('inner')
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
    input('After update. Press enter to exit...')

driver.quit()
