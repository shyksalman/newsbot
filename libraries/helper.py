import os
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta
from selenium.webdriver.common.by import By

from resources.locators import Locators


def get_date_range(term):
    today = datetime.today()
    start_date = today.replace(day=1)
    end_date = (start_date - relativedelta(months=term - 1)).replace(day=1) if term > 1 else start_date
    end_date = end_date + relativedelta(months=1) - relativedelta(days=1)
    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')


def get_work_item():
    search_phrase = os.getenv('SEARCH_PHRASE', 'Imran Khan')
    news_category = os.getenv('NEWS_CATEGORY', 'Awards')
    months = int(os.getenv('MONTHS'))
    return search_phrase, news_category, months


def check_amount_phrase(item: dict):
    """
        Set the search phrase count and check if the article contains mentions of money.

        Args:
            item (dict): Dictionary containing news article data.
            :param item:
    """
    title_description = f'{item["title"]} {item["description"]}' if item.get("description") else item['title']
    _phrase = get_work_item()
    item["phrase"] = len(re.findall(_phrase[0], title_description, flags=re.IGNORECASE))

    amount_pattern = r'\$[0-9,]+(\.[0-9]+)?|\b[0-9]+ dollars\b|\b[0-9]+ USD\b'
    item["amount"] = 'Yes' if re.search(amount_pattern, title_description) else 'No'


def parse_date(date_text):
    for fmt in ('%B %d, %Y', '%b %d, %Y', '%b. %d, %Y'):
        try:
            return datetime.strptime(date_text, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Date format for '{date_text}' not recognized")


def extract_dates(elements):
    """
    Extracts text from a list of WebElement instances and returns a list of non-empty strings.

    Args:
        elements (list): List of WebElement instances.

    Returns:
        list: List of extracted date strings.
    """
    return [
        parse_date(element.find_element(by=By.XPATH, value=Locators.NewsArticle.DATE).text.strip())
        for element in elements
        if element.find_element(by=By.XPATH, value=Locators.NewsArticle.DATE).text.strip()
    ]
