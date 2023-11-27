import logging
import time

from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from utils import InvalidResponseError, retries_on

YANDEX_N_RETRIES = 5
YANDEX_PAUSE_DURATION_SECONDS = 2


class YaMarketParser(object):

    def __init__(self):

        self.display = None
        self.driver = None

    def init_chrome(self):
        self.display = Display(visible=False, size=(1600, 900))
        self.display.start()

        chrome_options = Options()

        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--no-sandbox')

        self.driver = webdriver.Chrome(options=chrome_options)

        self.driver.implicitly_wait(5)

        logging.info('Virtual chrome was successfully initialized')

    def quit_chrome(self):
        self.driver.close()
        self.display.stop()
        self.display = None
        self.driver = None

        logging.info('Virtual chrome was shut down')

    def prepare(self):
        try:
            self.init_chrome()
            return True
        except Exception as e:
            logging.error('error during chrome setup', str(e))
            return False

    def quit(self):
        try:
            self.quit_chrome()
            logging.info('Chrome has been closed')
            return True
        except Exception as e:
            logging.error('error during chrome quit', str(e))
            return False

    @retries_on(num=YANDEX_N_RETRIES, sleep_time_seconds=YANDEX_PAUSE_DURATION_SECONDS)
    def parse_yamarket_page(self, link, link_field):
        logging.info(f"Get link for Virtual Chrome to process: {link}")
        self.driver.get(link)
        try:
            submit_button = self.driver.find_element(By.XPATH,
                                                     '/html/body/div[17]/div/div[2]/div/div/div/div/div[1]/button')
            submit_button.click()
        except NoSuchElementException:
            pass

        names = self.driver.find_elements(By.CLASS_NAME, '_2TxqA')
        values = self.driver.find_elements(By.CLASS_NAME, '_3PnEm')

        if len(names) == 0 or len(values) == 0 or len(names) > len(values):
            raise InvalidResponseError(f'Empty or broken response from selenium during parsing link {link}')

        specs = {link_field.lower(): link}

        for i in range(len(names)):
            specs[names[i].text.lower()] = values[i].text

        logging.info(f'Link has been processed by Virtual Chrome, link: {link}')
        time.sleep(YANDEX_PAUSE_DURATION_SECONDS)

        return specs
