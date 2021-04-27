#!/usr/bin/python

from __future__ import division

import sys
import os
import traceback
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.alert import Alert

import login_details

import logging
from selenium.webdriver.remote.remote_connection import LOGGER

import lxml.html # for table parsing - much quicker than selenium (x20)
import lxml.etree

import pprint
pp = pprint.PrettyPrinter(indent=4)

HOME_URL = 'https://www2.trustnet.com/Tools/Portfolio/PortfolioHome.aspx' # initial page to start our web scrape journey :)

#HEADLESS = True
HEADLESS = False    # Headless is breaking the SAML login at present

user_agent = 'Mozilla/5.0 (X11; Linux x86_64)' + 'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.39 Safari/537.36'

# the size of the desktop /virtual window we want to use
# This is very IMPORTANT or you will get Element not visible errors
#   selenium.common.exceptions.ElementNotVisibleException: Message: element not visible
my_window = {
    'width': 1920,
    'height': 1080
}

# timeouts
PAGELOAD_TIMEOUT = 30

# save output to where ?
SOURCEOUTFILE = "/data/err_source.html"
BROWSER_LOG = "/data/chromedriver.log"
user_data_dir='/data/chrome-data'

#webdriver
driver = None

# where is the binary browser - store locally so we can update it manually v2.33 inuse
chrome_driver = '/usr/local/bin/chromedriver'



# dict of timing stats
timing_stats = {} # dict of lists

###################################################################################
def show_timing_stats():
    """ Print out the timing stats """
    print ("*** STATS ***")
    print ("\t", "function", "min", "avg", "max", "total")

    for ts in sorted(timing_stats):
        lst = timing_stats[ts]
        max_value = round(max(lst), 2)
        min_value = round(min(lst), 2)
        avg_value = round(sum(lst) / len(lst), 2)
        tot_value = round(sum(lst), 2)
        print ("\t", ts, min_value, avg_value, max_value, tot_value)

def timing(f):
    """ decorator to time function calls """
    def wrap(*args):
        """ wrapper """
        global timing_stats
        time1 = time.time()
        ret = f(*args)
        time2 = time.time()

        diff = (time2-time1)*1000.0
        func = f.__name__

        if f.__name__ not in timing_stats:
            timing_stats[func] = []

        timing_stats[func].append(diff)

        print ('%s function took %0.3f ms' % (func, diff))
        return ret
    return wrap

@timing
def webdriver_setup():
    """ Set up the webdriver """
    global driver

    options = webdriver.ChromeOptions()
    if HEADLESS:
        options.add_argument('headless') # this doesnt work as SAML sends a blank page
    options.add_argument('--start-maximized')
    options.add_argument('--window-size=' + str(my_window['width']) + ',' + str(my_window['height'])) # or the login a href is not found and throws error
    options.add_argument("--user-data-dir="+user_data_dir)
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-infobars')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-dev-shm-usage')
    #
    #options.add_argument('--no-sandbox')
    options.add_argument('--remote-debugging-port=9222')
    #
    #options.add_argument('--no-sandbox')
    #options.add_argument('--disable-setuid-sandbox')
    options.add_argument("--user-agent="+user_agent) # hide headless browser

    # disable images = 2 - quicker load # but breaks the table next image button (selenium cant see it)
    # if you mess with this, it will save to disk, so you need to overwrite with = 1 again to get images back
    prefs = {"profile.managed_default_content_settings.images":1}
    options.add_experimental_option("prefs", prefs)

    #
    # set up debug logging if required
    #
    LOGGER.setLevel(logging.DEBUG)
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    # initialize the chrome web driver
    driver = webdriver.Chrome(
        #executable_path=chrome_driver, # important to point to the driver exe
        options=options, # all the options we adjusted above
        #"--no-sandbox", "--disable-setuid-sandbox",
        service_args=["--verbose", "--whitelisted-ips=127.0.0.1", "--log-path="+BROWSER_LOG]
    )

    # this overrides all other waits !!!
    # https://github.com/SeleniumHQ/selenium/issues/718
    #driver.implicitly_wait(30) # max 30sec wait per action - SAML login takes ~10-26secs

    # this seems to be be the only way to set the XVFB + chrome window size - on a desktop this is not needed
    #driver.set_window_size(my_window['width'], my_window['height'])  # this is IMPORTANT must set windows size this way

    #driver.maximize_window() # errors with window set to 'normal'
    sz = driver.get_window_size()
    print ("** Window Size", sz) # our check
    if (sz['width'] < my_window['width'] - 1) or (sz['height'] < my_window['height'] - 1): # why is the reported view 1 pixel smaller?
        print ("Error: Window size is not optimal",sz['width'],'x',sz['height'])
        sys.exit(1)

def save_source(outfile=SOURCEOUTFILE):

    """ save current page to file """

    with open(outfile, 'w') as html_file:
        html_file.write(driver.page_source.encode('utf8'))
    html_file.close()

def exit_failed():

    """ general exit routine """

    save_source() # save page we errored on
    driver.quit()
    sys.exit(1)

###############################################################################
#
# wait for element functions
#
# https://selenium-python.readthedocs.io/waits.html

#@timing
def wait_for_alert(err_msg,accept=True):
    """ wait_for_alert """
    # https://www.guru99.com/alert-popup-handling-selenium.html

    try:
        WebDriverWait(driver, PAGELOAD_TIMEOUT).until(
            EC.alert_is_present()
        )
        alert = driver.switch_to.alert
        if accept:
            alert.accept()
        else:
            alert.dismiss()
    except Exception:
        print (err_msg)
        #exit_failed()

#@timing
def wait_for_element_by_name(el_name, err_msg):
    """ wait_for_element_by_name """
    try:
        element = WebDriverWait(driver, PAGELOAD_TIMEOUT).until(
            EC.presence_of_element_located((By.NAME, el_name))
        )
        return element
    except Exception:
        print (err_msg)
        exit_failed()

#@timing
def wait_for_element_by_class(cl_name, err_msg):
    """ wait_for_element_by_class """
    try:
        element = WebDriverWait(driver, PAGELOAD_TIMEOUT).until(
            EC.presence_of_element_located((By.CLASS_NAME, cl_name))
        )
        return element
    except Exception:
        print (err_msg)
        exit_failed()

#@timing
def wait_for_element_by_xpath(x_path, err_msg):
    """ wait_for_element_by_xpath """
    try:
        element = WebDriverWait(driver, PAGELOAD_TIMEOUT).until(
            EC.presence_of_element_located((By.XPATH, x_path))
        )
        return element
    except Exception:
        print (err_msg)
        print (traceback.format_exc())
        exit_failed()

#@timing
def wait_for_element_by_css(css, err_msg):
    """ wait_for_element_by_css """
    try:
        element = WebDriverWait(driver, PAGELOAD_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css))
        )
        return element
    except Exception:
        print (err_msg)
        print (traceback.format_exc())
        exit_failed()

#@timing
def wait_for_element_by_id(elid, err_msg):
    """ wait_for_element_by_id """
    try:
        element = WebDriverWait(driver, PAGELOAD_TIMEOUT).until(
            EC.presence_of_element_located((By.ID, elid))
        )
        return element
    except Exception:
        print (err_msg)
        print (traceback.format_exc())
        exit_failed()

###############################################################################
#
# Data gathering and output functions
#

#@timing
# def write_simple_csv():

#     """ save to file as a simple csv """

#     with open(OUTFILE, 'w') as outfile:
#         counter = 0
#         for fields in all_data:
#             counter = counter + 1
#             outfile.write(','.join(fields))
#             outfile.write('\n') # add a new line
#     outfile.close()
#     print ("Wrote", counter, "rows")

###############################################################################
#
# page access functions
#

# we split these up so we can time how long each page takes to load and access

@timing
def open_homepage():

    """ open the initial page """
    print ("Getting " + HOME_URL)
    driver.set_page_load_timeout(120)
    driver.get(HOME_URL)
    print ("Got home page")

@timing
def select_login():

    """ find and click the login button/link """
    wait_for_element_by_id("next", "Died waiting for login button")
    login_button = driver.find_element(By.ID, "next")

    # scroll page to the button (if page is wider than view) - does not work with xvfb
    loc = login_button.location_once_scrolled_into_view
    time.sleep(5)

    login_button.click()
    #print "Clicked open login page button"

@timing
def already_logged_in():

    """ check if already logged in """

    print ("Are we already logged in")
    css = "div.Portfolio"
    try:
        LOGGEDIN_TIMEOUT=3
        element = WebDriverWait(driver, LOGGEDIN_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css))
        )
        return True
    except Exception:
        return False


@timing
def wait_for_login():

    """ wait for login fields to appear """

    print ("Waiting for login fields to appear")
    wait_for_element_by_id("password", "Died waiting for password")

@timing
def fill_in_login():

    """ fill-in login page details """

    username = driver.find_element_by_css_selector('input#logonIdentifier')
    password = driver.find_element_by_css_selector('input#password')

    username.send_keys(login_details.USERNAME)
    password.send_keys(login_details.PASSWORD)
    print ("Sendkeys login details")

@timing
def submit_login():
    """ submit the login form """

    submit_button = driver.find_element_by_css_selector('button#next')
    submit_button.click()
    print ("Submitted login details")

@timing
def submit_logout():
    """ click the logout link """

    logout_button = driver.find_element_by_css_selector('a.icon_logout')
    logout_button.click()
    print ("clicked logout")

@timing
def wait_for_portfolio():
    """ wait for the portfolio page to fully load """

    wait_for_element_by_css("div.Portfolio", "Died waiting for portfolio page")

###################################################################################
#
##### MAIN #####
#

DISPLAY = os.getenv('DISPLAY')
if DISPLAY == None:
    print ("no DISPLAY env var")
    sys.exit(1)
else:
    print("DISPLAY =", DISPLAY)

#
# the actual work - done in functions so that they can be timed
#

webdriver_setup()
open_homepage()

if not already_logged_in():
    # not already logged in so log in
    print ("Not logged in")
    wait_for_login()
    fill_in_login()
    submit_login()

    wait_for_portfolio()

print ("Logged in")

# check results table for only 1 result
root = lxml.html.fromstring(driver.page_source)
rows = root.xpath('.//table[contains(@class, "format")]/tbody/tr')
if len(rows) == 0:
    print ("FAILED, portfolio not found")
    exit_failed()
else:
    print ("portfolio found")

# get current displayed data
cells = rows[2].xpath('.//td/text()')

# print("cells")
# pp.pprint(cells)
# print("cells")

total = cells[3].strip()

# ignore first char which is the currency
print ("##TOTAL## "+total[1:].replace(',',''))

#submit_logout() # dont worry about this

driver.quit()
# clean exit
sys.exit(0)

