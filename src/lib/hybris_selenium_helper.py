from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


def log_into(driver, address, login, password):
    print(f'Opening login page ({address})...', end='', flush=True)
    driver.get(address)
    assert 'Error report' not in driver.title
    print('Done, entering login credentials...', end='', flush=True)
    xpath_for_login_field = '//input[@type="text" and (@name="j_username" or contains(@name, "login"))]'
    print('Waiting until visibility_of_element_located')
    username_field = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.XPATH, xpath_for_login_field)))
    print('Done, now trying to clear username field')
    username_field.clear()
    username_field.send_keys(login)
    xpath_for_password_field = '//input[@type="password" and contains(@name, "password")]'
    password_field = driver.find_element(By.XPATH, xpath_for_password_field)
    password_field.clear()
    password_field.send_keys(password)

    # change language to english in backoffice
    if address.endswith(('backoffice', 'backoffice/')):
        language_select = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.TAG_NAME, 'select')))
        if language_select:
            print('changing language to English')
            language_select.find_element(By.XPATH, 'option[text()="English"]').click()

    print('clicking login button...', end='', flush=True)
    xpath_for_login_button = '//button|//a|//span[@title="Login"]'

    if address.endswith(('backoffice', 'backoffice/')):
        WebDriverWait(driver, 5).until(EC.text_to_be_present_in_element((By.XPATH, xpath_for_login_button), 'Login'))
    driver.find_element(By.XPATH, xpath_for_login_button).click()

    print('logged in')
