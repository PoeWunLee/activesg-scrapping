import os
import sys
from dotenv import load_dotenv

#path resolution for imports
CURRENT_FILE_DIR = os.path.dirname(os.path.abspath(__file__))
EXPORT_FILE_PATH = os.path.join(CURRENT_FILE_DIR, "data", "extract.csv")
sys.path.append(os.path.join(CURRENT_FILE_DIR,'utils'))

#utils imports
from utils.browser_utils import initialise_browser_options, get_browser, managed_browser
from utils.page_utils import PageConfigs,GymPageLoader, GymCardsProcessor
from utils.db_utils import QueryExecutor

#import env
load_dotenv(os.path.join(CURRENT_FILE_DIR,".env"))
BROWSER=os.getenv("BROWSER")
BROWSER_OPTIONS=os.getenv("BROWSER_OPTIONS")
SCRAPE_URL=os.getenv("SCRAPE_URL")
PAGE_READY=os.getenv("PAGE_READY")
CARD_INDICATOR=os.getenv("CARD_INDICATOR")
DB_HOST=os.getenv("DB_HOST")
DB_PORT=os.getenv("DB_PORT")
DB_USER=os.getenv("DB_USER")
DB_PWD=os.getenv("DB_PWD")
DB_NAME=os.getenv("DB_NAME")

def main():

    # 1. Initialise browser & browser options
    opt = initialise_browser_options(BROWSER_OPTIONS)
    browser = get_browser(BROWSER)

    # 2. Scrape and export
    page_cfg=PageConfigs(
        scrape_url=SCRAPE_URL,page_ready=PAGE_READY,card_indicator=CARD_INDICATOR
    )
    with managed_browser(browser,opt) as ctx:
        gym_page = GymPageLoader(ctx, page_cfg,wait_strategy="presence")
        card_elements = gym_page.load_pages_and_cards()

        gym_card_processor = GymCardsProcessor()
        gym_card_processor.transform_and_export_cards(card_elements, EXPORT_FILE_PATH)

    # 3. Copy to Postgres
    cur = QueryExecutor(db_user=DB_USER, db_pwd=DB_PWD, db_host=DB_HOST, db_port=DB_PORT, db_name=DB_NAME)
    cur.copy_data(EXPORT_FILE_PATH)

if __name__ == "__main__":
    main()

