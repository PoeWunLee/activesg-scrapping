
from __future__ import annotations
from selenium import webdriver as webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from browser_utils import DriverContext
from pathlib import Path
import os
import pandas as pd
from datetime import datetime

SCRAPE_URL="https://activesg.gov.sg/gym-capacity"
PAGE_READY="p.chakra-text.css-1h5d4o4"
CARD_INDICATOR="div.chakra-stack.css-11ehgu5"

class PageConfigs:
    scrape_url:str
    page_ready:str
    card_indicator:str

class GymPageLoader:
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
    
    def load_cards(self)->dict[str:str]:
        """Find Card elements containing Gym Names and Capacity fields - save as dict"""
        elements = self.ctx.driver.find_elements(By.CSS_SELECTOR, self.card_indicator)
        gym_cards = {}
        for e in elements:
            gym_name, gym_capacity = e.text.split("\n")
            gym_cards[gym_name] = gym_capacity

        return gym_cards

    def save_cards_as_csv(self,cards:dict[str:str], file_path:Path|str)->None:
        """Save to data/ directory as csv for Postgres copy step"""
        cards_df = pd.DataFrame(cards, columns=["gym_name", "capacity"])
        cards_df["scrape_timestamp"] = datetime.now()
        cards_df.to_csv(file_path)