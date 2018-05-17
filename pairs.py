import os
import re
import time

from optparse import OptionParser
import configparser

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common import exceptions


class Pairs(object):

    __USER_DATA_PATH = os.path.dirname(os.path.abspath(__file__)) + '/profile'
    __LOGIN_URL = 'https://pairs.lv/#/login'
    __SMS_LOGIN_URL = ('https://www.accountkit.com/v1.0/basic/dialog/sms_login/?app_id=358202260919932&country_code=81'
                       '&redirect=https%3A%2F%2Fpairs.lv%2F&state=8013c3f046e994a5dfa7156829be1c2bcc516ce0f26f476a01c7'
                       '11c8023948e4&fbAppEventsEnabled=true&debug=true'
                       )

    @classmethod
    def login_url(cls):
        return cls.__LOGIN_URL

    @classmethod
    def __open_driver(cls, driver_path, headless):
        options = Options()
        if headless:
            options.add_argument('--headless')
        options.add_argument('--user-data-dir=' + cls.__USER_DATA_PATH)

        driver = webdriver.Chrome(executable_path=driver_path, chrome_options=options)
        return driver

    @staticmethod
    def __set_wait_time(driver):
        wait_time = 0.5
        page_load_timeout = 30

        driver.implicitly_wait(wait_time)
        driver.set_page_load_timeout(page_load_timeout)

    def open(self):
        self.__driver.get(self.__LOGIN_URL)
        if self.__LOGIN_URL in self.__driver.current_url:
            self.__login(self.__driver, self.__config)

    @classmethod
    def __login(cls, driver, config):
        driver.get(cls.__SMS_LOGIN_URL)
        phone_number_element_name = 'phone_number'

        cls.__wait(driver, phone_number_element_name, By.NAME)
        phone_number_text_box = cls.__select_element(driver)
        phone_number = config['DEFAULT']['PHONE_NUMBER']
        cls.__send_key(phone_number, phone_number_text_box)

        code_element_name = 'confirmation_code'
        cls.__wait(driver, code_element_name, By.NAME)
        prompt = '認証コードを入力してください:'
        code = input(prompt)
        code_text_box = cls.__select_element(driver, code_element_name, 'name')
        cls.__send_key(code, code_text_box)

    def __init__(self, driver_path='chromedriver', headless=None, setting_path='setting.ini'):
        self.__driver_path = driver_path
        self.__config = configparser.ConfigParser()
        if headless is None:
            if self.__config['BROWSER']['HEADLESS'] in ['true', 'True']:
                self.__headless = True
            else:
                self.__headless = False
        else:
            self.__headless = headless

        self.__config.read(setting_path)
        self.__driver = self.__open_driver(driver_path, headless)
        self.__set_wait_time(self.__driver)

    @classmethod
    def __send_key(cls, value, element):
        element.send_keys(value)
        element.send_keys(Keys.ENTER)

    @staticmethod
    def __select_element(driver, value, by='id'):
        if by == 'id':
            return driver.find_element_by_id(value)
        elif by == 'name':
            return driver.find_element_by_name(value)
        elif by == 'class_name':
            return driver.find_element_by_class_name(value)
        else:
            raise ValueError

    @staticmethod
    def __wait(driver, name, by=By.CLASS_NAME, wait_time=30):

        element_condition = EC.presence_of_element_located((by, name))
        WebDriverWait(driver, wait_time).until(element_condition)

    @classmethod
    def __fetch_total_number(cls, driver):
        number = cls.__select_element(driver, 'search_result_count', 'class_name').text
        return int(re.findall('(.+?)人', number)[0].replace(',', ''))

    @staticmethod
    def __ask_leave_footprints(total_number):
        print(str(total_number) + '人に足跡を付けます(y/n)')
        while True:
            answer = input('>>')
            if answer == 'y':
                break
            elif answer == 'n':
                print('終了します')
                quit()
            else:
                print('入力が不正です\nもう一度入力してください')

    def __open_person_page(self, person_url):
        try:
            self.__driver.get(person_url)
            self.__wait(self.__driver, 'search_result_count')
            time.sleep(1)
        except (exceptions.WebDriverException, exceptions.TimeoutException) as err:
            print(err)
            self.__driver.quit()
            self.__driver = self.__open_driver(self.__driver_path, self.__headless)
            self.__set_wait_time(self.__driver)

    def leave_footprints(self):
        total_number = self.__fetch_total_number(self.__driver)
        self.__ask_leave_footprints(total_number)
        person_url = 'https://pairs.lv/#/search/one/'
        progress_string = '現在{}人に足跡を付けました\r'
        for i in range(1, total_number + 1):
            self.__open_person_page(person_url + str(i))
            print(progress_string.format(str(i)), end='')
        print('\n')
        print('終了しました')

