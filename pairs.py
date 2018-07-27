import os
import re
import time
import signal

from argparse import ArgumentParser
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
        page_load_timeout = 10

        driver.implicitly_wait(wait_time)
        driver.set_page_load_timeout(page_load_timeout)

    def open(self):
        try:
            self.__driver.get(self.__PAIRS_URL)
        except exceptions.TimeoutException:
            pass
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

        cls.__click_login_link
        cls.__send_phone_number(driver, config)
        cls.__send_auth_code(driver)

    @classmethod
    def __click_login_link(cls, driver):
        link = driver.find_element_by_link_text('こちら')
        link.send_keys(Keys.ENTER)

    @classmethod
    def __send_phone_number(cls, driver, config):
        phone_number_element_name = 'phone_number'

        cls.__wait(driver, phone_number_element_name, By.NAME)
        phone_number_text_box = cls.__select_element(driver, phone_number_element_name, 'name')
        phone_number = config['DEFAULT']['PHONE_NUMBER']
        cls.__send_key(phone_number, phone_number_text_box)

    @classmethod
    def __send_auth_code(cls, driver):
        code_element_name = 'confirmation_code'
        cls.__wait(driver, code_element_name, By.NAME)
        prompt = '認証コードを入力してください:'
        code = input(prompt)
        code_text_box = cls.__select_element(driver, code_element_name, 'name')
        try:
            cls.__send_key(code, code_text_box)
        except exceptions.TimeoutException:
            pass

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
        self.__driver.close()
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
        next_button_xpath = '//*[@id="pairs_search_page"]/div/div[3]/div[2]/ul/li[3]/a'
        self.__wait(self.__driver, next_button_xpath, By.XPATH)
        progress_string = '\r現在{}人に足跡を付けました'
        print(progress_string.format('1'), end='')
        next_button = self.__driver.find_element_by_xpath(next_button_xpath)

        for i in range(2, total_number + 1):
            try:
                next_button.send_keys(Keys.ENTER)
            except (exceptions.ElementNotVisibleException, exceptions.WebDriverException) as e:
                if self.__driver.current_url.startswith(self.__LOGIN_URL):
                    print('ログイン状態が切れました')
                    print('終了します')
                    quit(1)
                print(e)
                continue
            self.__wait(self.__driver, 'button_white_a')
            print(progress_string.format(str(i)), end='')
            time.sleep(self.__GENERAL_WAIT_TIME)

        print('\n')
        print('終了しました')

    def leave_footprints_for_like(self):
        person_xpath = '/html/body/div[2]/div/div[2]/div[1]/div/div/div[2]/div[2]/ol/li[{}]/div[2]/div[1]/ul/li/img'
        page = 1
        list_url = 'https://pairs.lv/#/like/from_me/'

        while True:
            self.__driver.get(list_url + str(page))
            page = page + 1
            time.sleep(1)

            for i in range(0, 10):

                try:
                    formatted_xpath = person_xpath.format(str(i+1))
                    self.__driver.find_element_by_xpath(formatted_xpath).click()
                    self.__wait(self.__driver, 'modal_close')
                    time.sleep(1)
                    self.__driver.find_element_by_class_name('modal_close').click()
                    time.sleep(1)
                except exceptions.UnexpectedAlertPresentException:
                    continue
                except exceptions.NoSuchElementException:
                    return


def __main():
    def main():
        options = parse_option()
        pairs = Pairs(chromedriver=options.chromedirver, headless=options.headless, setting_path='')
        select_mode(pairs, options)

    def parse_option():
        parser = ArgumentParser()
        parser.add_argument('-t', '--timeout', action='store', default=5)
        parser.add_argument('-p', '--profile', action='store', default='profile')
        parser.add_argument('-d', '--chrome_driver', action='store', default='chromedriver')
        parser.add_argument('-h', '--headless', action='store_true', default=None)
        mode = parser.add_mutually_exclusive_group()
        mode.add_argument('-s', '--search', action='store_true', dest='search')
        mode.add_argument('-l', '--like_from_me', action='store_true')
        return parser.parse_args()

    def select_mode(pairs, options):
        if options.like_form_me:
            pass

    main()


if __name__ == '__main__':
    __main()
