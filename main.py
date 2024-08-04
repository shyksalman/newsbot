import logging
from libraries.helper import get_work_item
from task.process import LosAngelesNews


def main():
    try:
        news = LosAngelesNews()
        logging.info("Initializing bot successfully.")
        search_phrase, news_category, months = get_work_item()
        logging.info(f"Extracting {search_phrase, news_category, months} from env file")
        news.search_phrase(search_phrase)
        logging.info("Search phrase entered successfully.")
        news.newest_sort_by()
        logging.info("Sorting news to the latest")
        news.select_category(news_category)
        logging.info(f"Category '{news_category}' selected.")
        news.fetch_articles(months)
        logging.info("Downloading Images and xlsx file successfully.")
        news.browser.close_all_browsers()
        logging.info("Closed all browser windows.")
    except Exception as e:
        logging.error(e)


if __name__ == "__main__":
    main()
