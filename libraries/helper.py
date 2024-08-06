import os
import re
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from selenium.common.exceptions import (
    NoSuchElementException, TimeoutException, ElementNotVisibleException,
    StaleElementReferenceException, ElementClickInterceptedException,
    InvalidElementStateException
)

from functools import wraps
import logging
from libraries.exceptions import ParserError
from dateutil import parser

logging.basicConfig(level=logging.ERROR)

def get_date_range(term):
    today = datetime.today()
    start_date = today.replace(day=1)
    end_date = (start_date - relativedelta(months=term - 1)).replace(day=1) if term > 1 else start_date
    end_date = end_date + relativedelta(months=1) - relativedelta(days=1)
    return end_date.strftime('%Y-%m-%d')


def get_work_item():
    search_phrase = os.getenv('SEARCH_PHRASE', 'Imran Khan')
    news_category = os.getenv('CATEGORY', 'Awards')
    months = int(os.getenv('RANGE'))
    return search_phrase, news_category, months


def check_amount_phrase(title: str, desc: str) -> dict:
    """
        Set the search phrase count and check if the article contains mentions of money.

        Args:
            title (str): Title of the news article data.
            desc (str): Description of the news article data.
            :param title, desc:
    """
    title_description = f'{title} {desc}' if desc else title
    search_phrase = get_work_item()
    phrase = len(re.findall(search_phrase[0], title_description, flags=re.IGNORECASE))

    amount_pattern = r'\$[0-9,]+(\.[0-9]+)?|\b[0-9]+ dollars\b|\b[0-9]+ USD\b'
    amount = 'Yes' if re.search(amount_pattern, title_description) else 'No'
    return {"amount": amount, "phrase": phrase}


def parse_date(date_text: str) -> date | None:
    try:
        # Check if the date_text contains 'hours ago'
        if 'hour' in date_text:
            return datetime.now().date()
        elif 'min' in date_text:
            return datetime.now().date()
        else:
            return parser.parse(date_text).date()
    except ParserError as e:
        logging.error(f"An error occurred while parsing date {date_text}: {e}")
        return None


def base_exception():
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(self, *args, **kwargs):
            try:
                return view_func(self, *args, **kwargs)
            except (NoSuchElementException, TimeoutException, Exception,
                    ElementNotVisibleException, StaleElementReferenceException,
                    ElementClickInterceptedException, InvalidElementStateException) as e:
                logging.error(f"An error occurred in {self.__class__.__name__}.{view_func.__name__}: {str(e)}")
            return
        return _wrapped_view

    return decorator
