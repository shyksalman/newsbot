from libraries.helper import get_work_item
from task.process import LosAngelesNews


def main():
    news = LosAngelesNews()
    search_phrase, news_category, months = get_work_item()
    news.search_phrase(search_phrase)
    news.newest_sort_by()
    news.select_category(news_category)
    news.fetch_and_process_articles(months)
    news.browser.close_all_browsers()


if __name__ == "__main__":
    main()
