
from __future__ import annotations
from selenium import webdriver as webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from browser_utils import DriverContext
from pathlib import Path
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class PageConfigs:
    def __init__(self, scrape_url:str, page_ready:str, card_indicator:str):
        self.scrape_url=scrape_url
        self.page_ready=page_ready
        self.card_indicator=card_indicator

class GymPageLoader(PageConfigs):
    def __init__(self,ctx:DriverContext, page_cfg:PageConfigs,wait_strategy:str="presence"):
        self.ctx = ctx
        self.wait_strategy=wait_strategy
        self.scrape_url=page_cfg.scrape_url
        self.page_ready=page_cfg.page_ready
        self.card_indicator=page_cfg.card_indicator

    def wait(self):
        """Wait strategy accoridng to inputs"""
        condition = {
                "presence": EC.presence_of_element_located,
                "visibility": EC.visibility_of_element_located,
                "clickable": EC.element_to_be_clickable,
            }[self.wait_strategy]
        
        return self.ctx.wait.until(condition((By.CSS_SELECTOR, self.page_ready)))

    def load_page(self) -> None:
        """Load URL with associated wait strategy - e.g. until card elements is located"""
        self.ctx.driver.get(self.scrape_url)
        self.wait()
    
    def load_cards(self)->list[tuple[str:str]]:
        """Find Card elements containing Gym Names and Capacity fields - save as dict"""
        elements = self.ctx.driver.find_elements(By.CSS_SELECTOR, self.card_indicator)
        gym_cards = [e.text.split("\n") for e in elements]
        return gym_cards

    def load_pages_and_cards(self):
        """Execution of loading pages and cards"""
        #load page
        logger.info("Gym page loading started")
        try:
            self.load_page()
            #load cards
            cards=self.load_cards()
            logger.info(f"Gym page loaded. {len(cards)} Gym cards successfully extracted.")
            return cards
        except Exception:
            logger.exception(f"Gym page loading failed. \n {Exception}")
            raise

class GymCardsProcessor:
    @staticmethod
    def process_cards_as_df(cards:list[tuple[str:str]])->pd.DataFrame:
        """Process and clean data scrapped in dataframe"""
        cards_df = pd.DataFrame(cards, columns=["gym_name", "capacity"])
        cards_df["scrape_timestamp"] = datetime.now()

        str_to_remove = ["% full", "Closed"]
        for s in str_to_remove:
            cards_df["capacity"] = cards_df["capacity"].str.replace(s, "")
        return cards_df

    @staticmethod
    def save_cards_as_csv(cards_df:pd.DataFrame, file_path:Path|str)->None:
        """Save to data/ directory as csv for Postgres copy step"""
        cards_df.to_csv(file_path, index=False)

    def transform_and_export_cards(self,cards:list[tuple[str:str]], file_path:Path|str)->None:
        cards_df = self.process_cards_as_df(cards)
        self.save_cards_as_csv(cards_df, file_path)