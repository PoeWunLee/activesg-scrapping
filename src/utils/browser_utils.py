from __future__ import annotations
from selenium import webdriver as webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from abc import ABC, abstractmethod
from typing import Iterator
from contextlib import contextmanager
from selenium.webdriver.support.wait import WebDriverWait
import logging

#Browser Factory
class BrowserFactory(ABC):
    """Factory template for create_browser"""
    @abstractmethod
    def create_browser(self, options: Options) -> webdriver:
        pass

class SeleniumChromeFactory(BrowserFactory):
    """Concrete Factory for Selenium Chrome Browser"""
    #initialise browser
    def create_browser(self,options:Options) -> webdriver:
        #retrieve chromedriver path
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), 
            options=options
        )
        return driver

#Context managers
class DriverContext:
    """Driver context to set timeout and other settings once initialised"""
    def __init__(self, driver: webdriver, timeout: int = 10):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)

@contextmanager
def managed_browser(factory:BrowserFactory, options:Options) -> Iterator[DriverContext]:
    driver = factory.create_browser(options=options)
    """Context manager for driver object. Ensure cleanup of resources cleanly."""
    ctx = DriverContext(driver)
    try:
       yield ctx
    except Exception as err:
        logging.exception("Browser session failed")
        raise
    finally:
        if driver is not None:
            driver.quit()

#Main client entry point for configure settings/options
def initialise_browser_options(options:str)->Options: 
    """Instantiate selenium options class"""
    chrome_options=Options()
    chrome_options.add_argument(options)
    return chrome_options

def get_browser(browser:str="chrome")->BrowserFactory:
    """Client function to retrieve browser type"""
    browser_mapping={
        "chrome": SeleniumChromeFactory()
    }
    if browser not in browser_mapping.keys():
        print("Select a valid browser type: {}".format(browser_mapping.keys()))
    return browser_mapping[browser]
