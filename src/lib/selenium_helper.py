import os
import time

from lib import logging_helper
from selenium import webdriver


def create_firefox_webdriver(headless=False, implicit_wait_time=None):
    options = None
    if headless:
        options = webdriver.FirefoxOptions()
        options.headless = True
        # above command was working, but in firefox 84.0.2 it suddenly stopped working
        # for at least 84.0.2 there must be MOZ_HEADLESS environment variable set to 1
        os.environ['MOZ_HEADLESS'] = '1'

    try:  # try automatized version if available
        from webdriver_manager.firefox import GeckoDriverManager
        driver = webdriver.Firefox(executable_path=GeckoDriverManager().install(), firefox_options=options)
    except ImportError:  # default version
        driver = webdriver.Firefox(firefox_options=options)

    _common_create_webdriver(driver, implicit_wait_time)

    return driver


def create_chrome_webdriver(headless=False, implicit_wait_time=15):
    options = None
    if headless:
        options = webdriver.ChromeOptions()
        options.add_argument('headless')

    try:  # try automatized version if available
        from webdriver_manager.chrome import ChromeDriverManager
        driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=options)
    except ImportError:  # default version
        driver = webdriver.Chrome(chrome_options=options)

    _common_create_webdriver(driver, implicit_wait_time)

    return driver


def _common_create_webdriver(driver, implicit_wait_time):
    if implicit_wait_time is not None:
        driver.implicitly_wait(implicit_wait_time)

    def cleanup_after_exception_handler():
        if driver.service.process:
            driver.get_screenshot_as_file('selenium_error.png')
        import sys
        sys.stderr.flush()
        print('Post exception handler running...')
        print('Running pdb - after debugging just execute "exit" in pdb')
        import pdb
        pdb.pm()
        print('Quitting...')
        driver.quit()

    logging_helper.install_cleanup_exception_hook(cleanup_after_exception_handler)


def wait_until_element_is_displayed(element, wait_time=0.1, print_once=True):
    print('DEPRECATED: wait_until_element_is_displayed invoked, consider change into selenium wait')
    # TODO: http://selenium-python.readthedocs.io/waits.html
    # TODO: http://selenium-python.readthedocs.io/locating-elements.html
    print_count = 0
    element_class = '#'.join(element.get_attribute('class').split(' '))
    element_id = element.get_attribute('id')
    text_to_print = f'waiting {wait_time}s, because $(".{element_id}") $("#{element_class}") is not displayed yet'
    while not element.is_displayed():
        if print_once:
            if print_count == 0:
                print(text_to_print, end='', flush=True)
            elif print_count < 4:
                print(f'...and another {wait_time}s', end='', flush=True)
            elif print_count < 10:
                print(f',{wait_time}s', end='', flush=True)
            else:
                print('.', end='', flush=True)
            print_count += 1
        else:
            print(text_to_print)
        time.sleep(wait_time)
    if print_once and print_count != 0:
        print()  # print endline
