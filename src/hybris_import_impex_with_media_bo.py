#!/usr/bin/env python3
# TODO: logging instead of print
import argparse
import re

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from lib import hybris_argparse_helper
from lib import hybris_selenium_helper
from lib import logging_helper
from lib import selenium_helper

parser = argparse.ArgumentParser('Script for importing IMPEX with media zip in BO')
hybris_argparse_helper.add_hybris_bo_arguments(parser)
logging_helper.add_logging_arguments_to_parser(parser)
parser.add_argument('impex', type=str, help='File with impex')
parser.add_argument('media', type=str, help='File with media')
parser.add_argument('--headless', action='store_true', help='Use headless browser')
args = parser.parse_args()

driver = selenium_helper.create_firefox_webdriver(args.headless, implicit_wait_time=5)
hybris_selenium_helper.log_into(driver, args.address, args.user, args.password)

# logging into backoffice may take some time if we are just after a server restart, what's why we will wait a bit here
WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, '//tr[@title="System"]')))

# expand "System"
WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, '//tr[@title="System"]'))).click()

# expand "Tools"
WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, '//tr[@title="Tools"]'))).click()

# click on "Import"
WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, '//tr[@title="Import"]'))).click()

xpath_for_impex_input = '//button[text()="upload"]/following-sibling::span//input'
driver.find_element_by_xpath(xpath_for_impex_input).send_keys(args.impex)
WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, '//button[text()="create"]'))).click()

WebDriverWait(driver, 5).until(
    lambda x: driver.find_element_by_xpath('//span[text()="Choose media:"]/following-sibling::div').text)

xpath_for_next_button = '//button[text()="Next"]'
next_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, xpath_for_next_button)))
next_button.click()

WebDriverWait(driver, 5).until(
    lambda x: not driver.find_element_by_xpath('//span[text()="Media-Zip:"]/following-sibling::div').text)

xpath_for_media_button = '//button[text()="upload"]'
media_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, xpath_for_media_button)))
xpath_for_media_input = 'following-sibling::span//input'
media_input = media_button.find_element_by_xpath(xpath_for_media_input)
media_input.send_keys(args.media)

# when using remote backoffice uploading can take some time
WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, '//button[text()="create"]'))).click()

WebDriverWait(driver, 5).until(
    lambda x: driver.find_element_by_xpath('//span[text()="Media-Zip:"]/following-sibling::div').text)

xpath_for_start_button = '//button[text()="Start"]'
WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, xpath_for_start_button))).click()

cron_job_text = WebDriverWait(driver, 5).until(
    lambda x: driver.find_element_by_xpath('//span[text()="Cron Job:"]/following-sibling::div').text)
cron_job_code = re.search(r'(ImpEx-Import : )([^ ]+)', cron_job_text).group(2)

print(f'Started ImpEx import cron job with code: {cron_job_code}')

driver.quit()
