#!/usr/bin/env python3
import argparse

import time
from selenium.webdriver.support.ui import WebDriverWait

from lib import hybris_argparse_helper
from lib import hybris_selenium_helper
from lib import logging_helper
from lib import selenium_helper

parser = argparse.ArgumentParser('Script for importing IMPEX with media zip in HMC')
hybris_argparse_helper.add_hybris_hmc_arguments(parser)
logging_helper.add_logging_arguments_to_parser(parser)
parser.add_argument('impex', type=str, help='File with impex')
parser.add_argument('media', type=str, help='File with media')
parser.add_argument('--headless', action='store_true', help='Use headless browser')
args = parser.parse_args()

driver = selenium_helper.create_firefox_webdriver(args.headless, implicit_wait_time=5)
hybris_selenium_helper.log_into(driver, args.address, args.user, args.password)

# expand "System"
driver.find_element_by_xpath('//tr[@title="System"]').click()

# expand "Tools"
driver.find_element_by_xpath('//tr[@title="Tools"]').click()

# get current window handle
first_window_handle = driver.window_handles[0]
window_handles_len = len(driver.window_handles)

# click on "Import"
driver.find_element_by_xpath('//tr[@title="Import"]').click()

# wait for new window load
while window_handles_len == len(driver.window_handles):
    time.sleep(0.1)

# switch to new window
wizard_win_handle = [handle for handle in driver.window_handles if handle != first_window_handle][0]
driver.switch_to.window(wizard_win_handle)

# save currently opened windows
previously_opened_windows = driver.window_handles.copy()

driver.find_element_by_id('UploadToImpExMediaEditor[in Attribute[ImpExImportWizard.jobMedia]]_uploading').click()

create_multimedia_win_handle = [handle for handle in driver.window_handles if handle not in previously_opened_windows][
    0]
driver.switch_to.window(create_multimedia_win_handle)

xpath_for_impex_input = '//input[@class="modalMediaFileUploadChip"]'
driver.find_element_by_xpath(xpath_for_impex_input).send_keys(args.impex)

driver.find_element_by_xpath('//td[contains(text(), "Upload")]').click()
driver.switch_to.window(wizard_win_handle)

# save currently opened windows
previously_opened_windows = driver.window_handles.copy()

driver.find_element_by_xpath('//div[contains(text(), "Next")]').click()

driver.find_element_by_id('UploadToMediaEditor[in Attribute[ImpExImportWizard.mediasZip]]_uploading').click()

create_multimedia_win_handle = [handle for handle in driver.window_handles if handle not in previously_opened_windows][
    0]
driver.switch_to.window(create_multimedia_win_handle)

xpath_for_impex_input = '//input[@class="modalMediaFileUploadChip"]'
driver.find_element_by_xpath(xpath_for_impex_input).send_keys(args.media)

driver.find_element_by_xpath('//td[contains(text(), "Upload")]').click()
driver.switch_to.window(wizard_win_handle)

# save currently opened windows
previously_opened_windows = driver.window_handles.copy()

# start importing impex file
driver.find_element_by_xpath('//a[@title="Start"]').click()

# wait until importing is finished
result_text = WebDriverWait(driver, 60).until(
    lambda x: driver.find_element_by_id('ItemDisplay[FINISHED]_div').find_element_by_xpath(
        '..//following-sibling::td').text)

print(result_text)

driver.quit()
