import logging
import os
import re
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from libraries.exceptions import NoMatchFoundError

def get_date_range(term):
    today = datetime.today()
    start_date = today.replace(day=1)
    end_date = (start_date - relativedelta(months=term - 1)).replace(day=1) if term > 1 else start_date
    end_date = end_date + relativedelta(months=1) - relativedelta(days=1)
    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')


def get_work_item():
    search_phrase = os.getenv('SEARCH_PHRASE', 'Imran Khan')
    news_category = os.getenv('CATEGORY', 'Awards')
    months = int(os.getenv('RANGE'))
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


def parse_date(date_text: str) -> date:
    try:
        # Check if the date_text contains 'hours ago'
        if 'hour' in date_text:
            return datetime.now().date()

        # Dynamically standardize month abbreviations
        month_map = {
            'Jan.': 'Jan', 'Feb.': 'Feb', 'Mar.': 'Mar', 'Apr.': 'Apr',
            'Jun.': 'Jun', 'Jul.': 'Jul', 'Aug.': 'Aug', 'Sept.': 'Sep',
            'Oct.': 'Oct', 'Nov.': 'Nov', 'Dec.': 'Dec'
        }

        # Replace any variations with standard abbreviations
        for long_month, short_month in month_map.items():
            if long_month in date_text:
                date_text = date_text.replace(long_month, short_month)
                break

        # Try parsing absolute date formats
        formats = [
            '%B %d, %Y',
            '%b %d, %Y',
            '%b. %d, %Y',
            '%d %b %Y',
            '%d %B %Y'
        ]

        # Attempt to parse date with each format
        for fmt in formats:
            try:
                return datetime.strptime(date_text, fmt).date()
            except ValueError:
                continue

        # If none of the formats match, raise an error
        raise NoMatchFoundError(f"Date format for {date_text} is not recognized")
    except NoMatchFoundError as e:
        logging.error(f"An error occurred while parsing date {date_text}: {e}")