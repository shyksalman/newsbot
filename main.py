import logging

from libraries.exceptions import GeneralException
from libraries.helper import get_work_item
from task.process import NewsBot

logging.basicConfig(level=logging.INFO)


def main():
    try:
        news = NewsBot()
        search_phrase, news_category, months = get_work_item()
        news.search_phrase(search_phrase)
        news.newest_sort_by()
        news.select_category(news_category)
        news.fetch_articles(months)
        news.browser.close_all_browsers()
    except Exception as e:
        logging.error(e)


if __name__ == "__main__":
    main()
