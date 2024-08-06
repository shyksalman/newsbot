import logging

from libraries.exceptions import GeneralException
from libraries.helper import get_work_item
from task.process import LosAngelesNews, BaseScrapper

logging.basicConfig(level=logging.INFO)


def main():
    try:
        search_phrase, news_category, months = get_work_item()
        news = LosAngelesNews(phrase=search_phrase, news_category=news_category, months=months)

        news.search_phrase()
        news.newest_sort_by()
        news.select_category()
        news.fetch_articles()
        news.browser.close_all_browsers()
    except Exception as e:
        logging.error(e)


if __name__ == "__main__":
    main()
