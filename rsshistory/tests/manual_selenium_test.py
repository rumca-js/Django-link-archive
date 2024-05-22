"""
This is manual test. Should be run manually.

I am using poetry, so should you.

In case of doubts copy even more code from web tools.
"""

import json
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def get_selenium_status_code(logs):
    """
    https://stackoverflow.com/questions/5799228/how-to-get-status-code-by-using-selenium-py-python-code
    """
    last_status_code = 200
    for log in logs:
        if log["message"]:
            d = json.loads(log["message"])

            content_type = ""
            try:
                content_type = d["message"]["params"]["response"]["headers"]["content-type"]
            except Exception as E:
                pass
            try:
                content_type = d["message"]["params"]["response"]["headers"]["Content-Type"]
            except Exception as E:
                pass

            try:
                response_received = (
                    d["message"]["method"] == "Network.responseReceived"
                )
                if content_type.find("text/html") >= 0 and response_received:
                    last_status_code = d["message"]["params"]["response"]["status"]
            except Exception as E:
                #print("Exception: {}".format(str(E)))
                pass

    return last_status_code


def selenium_headless(url, timeout = 10):
    service = Service(executable_path="/usr/bin/chromedriver")
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    # add 10 seconds for start of browser, etc.
    selenium_timeout = timeout + 10

    driver = webdriver.Chrome(service=service, options=options)
    
    driver.set_page_load_timeout(selenium_timeout)
    
    driver.get(url)

    status_code = 200
    try:
        logs = driver.get_log("performance")
        status_code2 = get_selenium_status_code(logs)
        if status_code2:
            status_code = status_code2
    except Exception as E:
        print("Chrome webdrider error:{}".format(str(E)))

    # if self.options.link_redirect:
    #    WebDriverWait(driver, selenium_timeout).until(EC.url_changes(driver.current_url))

    html_content = driver.page_source

    if url != driver.current_url:
        url = driver.current_url

    #print(html_content)
    print(status_code)

    driver.quit()

    return html_content


def selenium_full(url, timeout = 10):
    import os
    #from pyvirtualdisplay import Display

    #display = Display(visible=0, size=(800, 600))
    #display.start()

    os.environ["DISPLAY"] = ":10.0"

    service = Service(executable_path="/usr/bin/chromedriver")

    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage") 

    #options.add_argument("--disable-setuid-sandbox") 
    #options.add_argument("--remote-debugging-port=9222")  # this
    #options.add_argument("--disable-extensions") 
    #options.add_argument("--disable-gpu") 
    #options.add_argument("start-maximized") 
    #options.add_argument("disable-infobars")
    #options.add_argument(r"user-data-dir=\home\rumpel\cookies\\")

    #options.add_argument("--disable-dev-shm-usage")
    # options.add_argument('--remote-debugging-pipe')
    # options.add_argument('--remote-debugging-port=9222')
    # options.add_argument('--user-data-dir=~/.config/google-chrome')

    # options to enable performance log, to read status code
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

    # if not BasePage.ssl_verify:
    #    options.add_argument('ignore-certificate-errors')

    driver = webdriver.Chrome(service=service, options=options)

    # add 10 seconds for start of browser, etc.
    selenium_timeout = timeout + 20

    driver.set_page_load_timeout(selenium_timeout)

    driver.get(url)

    status_code = 200
    try:
        logs = driver.get_log("performance")
        status_code2 = get_selenium_status_code(logs)
        if status_code2:
            status_code = status_code2
    except Exception as E:
        print("Chrome webdrider error:{}".format(str(E)))

    WebDriverWait(driver, selenium_timeout)
    import time
    time.sleep(10);

    ## if self.options.link_redirect:
    #WebDriverWait(driver, selenium_timeout).until(
    #    EC.url_changes(driver.current_url)
    #)
    """
    TODO - if webpage changes link, it should also update it in this object
    """

    page_source = driver.page_source

    if url != driver.current_url:
        url = driver.current_url

    print(page_source)

    driver.quit()


def selenium_undetected(url, timeout = 10):
    service = Service(executable_path="/usr/bin/chromedriver")
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    #
    #options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    # add 10 seconds for start of browser, etc.
    selenium_timeout = timeout + 10

    driver = webdriver.Chrome(service=service, options=options)
    
    driver.set_page_load_timeout(selenium_timeout)
    
    driver.get(url)
    time.sleep(timeout+7)

    status_code = 200

    # if self.options.link_redirect:
    #    WebDriverWait(driver, selenium_timeout).until(EC.url_changes(driver.current_url))

    html_content = driver.page_source

    if url != driver.current_url:
        url = driver.current_url

    print(html_content)
    print(status_code)

    driver.quit()

    return html_content


def selenium_full(url, timeout = 10):
    import os
    #from pyvirtualdisplay import Display

    #display = Display(visible=0, size=(800, 600))
    #display.start()

    os.environ["DISPLAY"] = ":10.0"

    service = Service(executable_path="/usr/bin/chromedriver")

    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage") 

    #options.add_argument("--disable-setuid-sandbox") 
    #options.add_argument("--remote-debugging-port=9222")  # this
    #options.add_argument("--disable-extensions") 
    #options.add_argument("--disable-gpu") 
    #options.add_argument("start-maximized") 
    #options.add_argument("disable-infobars")
    #options.add_argument(r"user-data-dir=\home\rumpel\cookies\\")

    #options.add_argument("--disable-dev-shm-usage")
    # options.add_argument('--remote-debugging-pipe')
    # options.add_argument('--remote-debugging-port=9222')
    # options.add_argument('--user-data-dir=~/.config/google-chrome')

    # options to enable performance log, to read status code
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

    # if not BasePage.ssl_verify:
    #    options.add_argument('ignore-certificate-errors')

    driver = webdriver.Chrome(service=service, options=options)

    # add 10 seconds for start of browser, etc.
    selenium_timeout = timeout + 20

    driver.set_page_load_timeout(selenium_timeout)

    driver.get(url)

    status_code = 200
    try:
        logs = driver.get_log("performance")
        status_code2 = get_selenium_status_code(logs)
        if status_code2:
            status_code = status_code2
    except Exception as E:
        print("Chrome webdrider error:{}".format(str(E)))

    WebDriverWait(driver, selenium_timeout)
    import time
    time.sleep(10);

    ## if self.options.link_redirect:
    #WebDriverWait(driver, selenium_timeout).until(
    #    EC.url_changes(driver.current_url)
    #)
    """
    TODO - if webpage changes link, it should also update it in this object
    """

    page_source = driver.page_source

    if url != driver.current_url:
        url = driver.current_url

    print(page_source)

    driver.quit()


def main():
    #selenium_full("https://www.warhammer-community.com/en-us/feed")
    #selenium_headless("https://www.warhammer-community.com/")
    #selenium_headless("https://www.google.com/")
    selenium_undetected("https://www.warhammer-community.com/feed")

main()
