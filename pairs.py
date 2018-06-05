import os
import re
import time
import signal

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
    __PAIRS_URL = 'https://pairs.lv'
    __LOGIN_URL = 'https://pairs.lv/#/login'
    __GENERAL_WAIT_TIME = 0.2

    @classmethod
    def __open_driver(cls, driver_path, headless):
        """
        :param driver_path: Chrome driver's path
        :type driver_path str
        :param headless: Enable headless mode
        :type headless bool
        :return WebDriver object
        :rtype object
        """
        options = Options()
        if headless:
            options.add_argument('--headless')
        options.add_argument('--user-data-dir=' + cls.__USER_DATA_PATH)
        driver = webdriver.Chrome(executable_path=driver_path, chrome_options=options)
        return driver

    @staticmethod
    def __set_wait_time(driver):

        wait_time = 0.5
        page_load_timeout = 20

        driver.implicitly_wait(wait_time)
        driver.set_page_load_timeout(page_load_timeout)

    def open(self):
        self.__driver.get(self.__PAIRS_URL)
        self.__wait_redirect(self.__driver)
        if self.__LOGIN_URL == self.__driver.current_url:
            self.__login(self.__driver, self.__config)

    @classmethod
    def __wait_redirect(cls, driver):
        interval = 0.5
        timeout = 10
        for current_time in cls.__count_up(interval):
            if cls.__PAIRS_URL != driver.current_url:
                return
            if current_time >= timeout:
                raise TimeoutError
            time.sleep(interval)

    @staticmethod
    def __count_up(interval):
        current_time = 0
        while True:
            current_time += interval
            yield current_time

    @classmethod
    def __login(cls, driver, config):

        # sms認証画面に移行
        link = driver.find_element_by_link_text('こちら')
        link.click()
        phone_number_element_name = 'phone_number'

        cls.__wait(driver, phone_number_element_name, By.NAME)
        phone_number_text_box = cls.__select_element(driver, phone_number_element_name, 'name')
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
        self.__config.read(setting_path)
        signal.signal(signal.SIGINT, self.__quit_driver)

        if headless is None:
            if self.__config['BROWSER']['HEADLESS'] in ['true', 'True']:
                self.__headless = True
            else:
                self.__headless = False
        else:
            self.__headless = headless

        self.__driver = self.__open_driver(driver_path, headless)
        self.__set_wait_time(self.__driver)

    def __quit_driver(self, signal, frame):
        self.__driver.quit()

    def quit(self):
        self.__driver.quit()

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

    def leave_footprints(self):
        total_number = self.__fetch_total_number(self.__driver)
        self.__ask_leave_footprints(total_number)
        person_url = 'https://pairs.lv/#/search/one/1'
        self.__driver.get(person_url)
        progress_string = '\r現在{}人に足跡を付けました'
        print(progress_string.format('1'), end='')
        for i in range(2, total_number + 1):
            self.__driver.find_element_by_xpath('//*[@id="pairs_search_page"]/div/div[3]/div[2]/ul/li[3]/a').click()
            time.sleep(self.__GENERAL_WAIT_TIME)
            print(progress_string.format(str(i)), end='')

        print('\n')
        print('終了しました')

    def leave_footprints_for_like(self):
        like_xpath = '/html/body/div[4]/div/div[1]/div/nav[1]/div[2]/ul/li[2]/a'
        person_xpath = '/html/body/div[4]/div/div[2]/div[1]/div/div/div[2]/div[2]/ol/li[{}]/div[2]/div[2]/div[1]/p[2]/a'
        next_page_xpath = '/html/body/div[4]/div/div[2]/div[1]/div/div/div[2]/div[2]/pager-nums-top/div/div/a[3]'
        self.__driver.find_element_by_xpath(like_xpath).click()
        time.sleep(1)

        while True:
            for i in range(0, 10):

                try:
                    self.__driver.find_element_by_xpath(person_xpath.format(str(i + 1))).click()
                    self.__wait(self.__driver, 'modal_close')
                    self.__driver.find_element_by_class_name('modal_close').click()
                    self.__wait(self.__driver, 'button_white_a')
                except (exceptions.NoSuchElementException, exceptions.UnexpectedAlertPresentException):
                    continue
            try:
                self.__driver.find_element_by_xpath(next_page_xpath).click()
                time.sleep(1)
            except exceptions.ElementNotVisibleException:
                break


