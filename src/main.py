from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
from datetime import datetime
import os
import psycopg2
import logging                                                                         
from dotenv import load_dotenv

class ScrapeActiveSg:
    def __init__(self, current_timestamp):
        self.timestamp = current_timestamp
        self.driver = None
        self.raw_html = None
        self.gym_card_elements = None
        self.local_csv_path = None

    def _extract_html_and_elements(self):
        #extract to html
        self.raw_html = BeautifulSoup(self.driver.page_source, 'html.parser')

        #extract as list of gym card elements. EC wait until last gym card is loaded
        self.gym_card_elements = pd.DataFrame(
            [element.text.split('\n') for element in self.driver.find_elements(By.CSS_SELECTOR, "div.chakra-stack.css-11ehgu5")], 
            columns=['gym_name', 'capacity']
        ) 

        self.gym_card_elements['capacity'] = self.gym_card_elements['capacity'].str.replace("% full", "")
        self.gym_card_elements['capacity'] = self.gym_card_elements['capacity'].str.replace("Closed", "")
        self.gym_card_elements['timestamp'] = self.timestamp
        
        return self.raw_html, self.gym_card_elements

    def _save_to_csv(self):
        filename = "{}_gym_capacity.csv".format(self.timestamp.strftime('%Y%m%d_%H_%M'))
        self.local_csv_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),'data',filename)
        self.gym_card_elements.to_csv(self.local_csv_path,index=False)

        return self.local_csv_path
    
    def _initialise_chrome_options(self):

        chrome_options = Options()
        arg_for_chrome_options = ['--no-sandbox', '--headless=new', '--disable-dev-shm-usage', '--window-size=1920,1080', '--ignore-certificate-errors','--allow-running-insecure-content', 'user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36' ]
        for opt in arg_for_chrome_options:
            chrome_options.add_argument(opt)
        
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        
        return self.driver

    def _test_read_csv(self):
        print("---Reading csv---")
        print(pd.read_csv(self.local_csv_path))
        print("---End---")

    def scrape_data(self, url):
        try:
            self._initialise_chrome_options()
            self.driver.get(url)
            wait = WebDriverWait(self.driver, timeout=10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "p.chakra-text.css-1h5d4o4")))
            #self.driver.get_screenshot_as_file(r'C:\Users\Poe Wun\OneDrive\Documents\activesgScrapping\screenshot.png')
            self._extract_html_and_elements()
            self._save_to_csv()
            self._test_read_csv()
            self.driver.quit()
        except Exception as e:
            print(e)
        
        return self.local_csv_path

class DBUtility:
    def __init__(self, dbuser, dbpwd, dbhost, dbname, dbport):
        self.dbuser = dbuser
        self.dbpwd = dbpwd
        self.dbhost = dbhost
        self.dbname = dbname
        self.dbport = dbport
       
    def init_connect(self):
        try:
            conn  =psycopg2.connect(
                user=self.dbuser,
                password=self.dbpwd,
                host=self.dbhost,
                port=self.dbport,
                database=self.dbname
            )
            conn.autocommit=True
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

        except Exception as e:
            logging.error(e)
        
        return conn

    def insert_data(self, filepath):
        col_names='gym_name, capacity, scrape_timestamp'
        try:
            conn = self.init_connect()
            cursor = conn.cursor()
            cursor.copy_expert("COPY raw_scraped({}) FROM STDIN WITH DELIMITER ',' CSV HEADER".format(col_names), open(filepath, "r"))
        except Exception as e:
            logging.error(e)

if __name__== "__main__":

    #initialise env variables
    load_dotenv()
    db_host, db_user, db_pwd, db_name, db_port, scrape_url= \
        os.getenv("DB_HOST"), os.getenv("DB_USER"), os.getenv("DB_PWD"), os.getenv("DB_NAME"),os.getenv("DB_PORT"),os.getenv("SCRAPE_URL")

    #print(os.getenv("DB_HOST"))
    scrape = ScrapeActiveSg(datetime.now())
    DBUtility(db_user, db_pwd, db_host, db_name, db_port).insert_data(scrape.scrape_data(url=scrape_url))
    print(scrape.local_csv_path)