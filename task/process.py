import os
import logging
from RPA.HTTP import HTTP
from RPA.Browser.Selenium import Selenium
from datetime import datetime, date
from typing import List, Any
from dotenv import load_dotenv
from openpyxl.workbook import Workbook
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from resources.locators import Locators
from libraries.models import ArticleModel
from libraries.helper import get_date_range, check_amount_phrase, parse_date
from libraries.exceptions import ErrorInDownloadException, ErrorInFetchingArticles
from selenium.common.exceptions import NoSuchElementException, ElementNotVisibleException, \
    StaleElementReferenceException, TimeoutException, ElementClickInterceptedException, InvalidElementStateException

load_dotenv()

logging.basicConfig(level=logging.INFO)


class LosAngelesNews:
    """A class to interact with the Los Angeles News website."""

    def __init__(self):
        """
        Initialize LATimes instance and open a browser window.

        Args:
            url (str): The URL to navigate to.
            headless (bool, optional): Whether to run the browser in headless mode. Defaults to False.
            maximized (bool, optional): Whether to maximize the browser window. Defaults to True.
        """
        self.browser = Selenium()
        self.http = HTTP()
        self.open_browser()

    def open_browser(self) -> None:
        """
        Open a browser window and navigate to the given URL.
        """
        logging.info("Initializing bot...")
        logging.info("Opening web browser https://www.latimes.com/")
        self.browser.open_available_browser(url="https://www.latimes.com/", maximized=True)


class NewsBot(LosAngelesNews):
    """
    This class interacts with the website latimes and extracts the images, data and stores it in xlsx file
    """

    def __init__(self):
        super().__init__()
        self.articles_list = []

    def search_phrase(self, phrase: str) -> None:
        """
        Search for the given phrase and navigate to the results.
        """
        logging.info(f"Searching for the phrase: {phrase}")
        try:
            self.browser.wait_until_page_contains_element(Locators.Search.BUTTON)
            self.browser.click_button(Locators.Search.BUTTON)
            logging.info("Clicked on search button.")

            self.browser.wait_until_element_is_visible(Locators.Search.INPUT, timeout=30)
            self.browser.input_text(Locators.Search.INPUT, phrase)
            logging.info(f"Entered phrase '{phrase}' in search input.")

            self.browser.click_button(Locators.Search.SUBMIT)
            logging.info("Clicked on submit button.")

            self.browser.wait_until_page_contains_element(Locators.Search.RESULTS_FOR_TEXT)
            # self.browser.does_page_contain_element(Locators.Search.NO_RESULTS.format(phrase=phrase))
            logging.info(f"Searched results for phrase: {phrase}")
        except (NoSuchElementException, TimeoutException,
                ElementNotVisibleException, StaleElementReferenceException,
                ElementClickInterceptedException, InvalidElementStateException) as e:
            logging.error(f"An error occurred in {self.__class__.__name__}.{self.search_phrase.__name__}: {str(e)}")

    def newest_sort_by(self) -> None:
        """
        Sort search results by latest.
        """
        logging.info("Sorting search results by latest.")
        try:
            self.browser.wait_until_element_is_visible(Locators.Sort.SELECT_OPTIONS, timeout=30)
            sorty = self.browser.find_element(Locators.Sort.SELECT_OPTIONS)
            sorty.find_element(By.XPATH, value=Locators.Sort.SELECT_OPTIONS_INPUT).click()
            logging.info("Sorted search results by latest.")
        except (NoSuchElementException, TimeoutException, StaleElementReferenceException) as e:
            logging.error(f"An error occurred in {self.__class__.__name__}.{self.newest_sort_by.__name__}: {str(e)}")

    def select_category(self, news_category: str) -> None:
        logging.info(f"Selecting news category: {news_category}")
        try:
            self.browser.find_element(Locators.Category.SEE_ALL).click()
            self.browser.find_element(Locators.Category.SELECT_CATEGORY.format(name=news_category)).click()
            logging.info(f"Selected news category: {news_category}")
        except (NoSuchElementException, TimeoutException, StaleElementReferenceException) as e:
            logging.error(f"An error occurred in {self.__class__.__name__}.{self.select_category.__name__}: {str(e)}")

    def get_field_data(self, element: WebElement, locator) -> str | None:
        """
        Get text data from a WebElement based on a locator.

        Args:
            element (WebElement): The WebElement to extract data from.
            locator: Locator to find the desired element.

        Returns:
            str: The text data found.
        """
        logging.info(f"Getting field data using locator: {locator}")
        try:
            data = element.find_element(by=By.XPATH, value=locator).text
            logging.info(f"Retrieved data: {data}")
            return data
        except (NoSuchElementException, TimeoutException, StaleElementReferenceException) as e:
            logging.error(f"An error occurred in {self.__class__.__name__}.{self.get_field_data.__name__}: {str(e)}")
            return None

    def download_images(self, element: WebElement, file_path) -> str | None:
        """
        Download the profile picture associated with a news article.

        Args:
            element (WebElement): The WebElement representing the news article.
            file_path (str): The path to save the downloaded profile picture.

        Returns:
            str: The file path where the profile picture is saved.
        """
        logging.info(f"Downloading image to {file_path}")
        try:
            img = element.find_element(by=By.XPATH, value=Locators.NewsArticle.PROF_PIC)
            self.http.download(img.get_attribute('src'), file_path)
            logging.info(f"Image downloaded to {file_path}")
            return file_path
        except (NoSuchElementException, TimeoutException, StaleElementReferenceException) as e:
            logging.error(f"An error occurred in {self.__class__.__name__}.{self.download_images.__name__}: {str(e)}")
            return None

    def download_excel_file(self) -> None:
        """Download news article data into an Excel file."""
        logging.info("Downloading news articles data into an Excel file.")
        try:
            workbook = Workbook()
            exception_sheet = workbook.active
            exception_sheet.title = "Articles"
            exception_sheet.append(
                ["Title", "Date", "Description", "ProfilePicture", "Phrase", "Amount"])

            for item in self.articles_list:
                validated_item = ArticleModel(**item)
                row = [
                    validated_item.title,
                    validated_item.date,
                    validated_item.description,
                    validated_item.profile_picture,
                    validated_item.phrase,
                    validated_item.amount
                ]
                exception_sheet.append(row)

            output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
            os.makedirs(output_dir, exist_ok=True)
            workbook.save(os.path.join(output_dir, 'los-angeles-times.xlsx'))
            logging.info("News articles data saved to Excel file.")
        except ErrorInDownloadException as e:
            logging.error(
                f"An error occurred in {self.__class__.__name__}.{self.download_excel_file.__name__}: {str(e)}")

    def fetch_articles(self, _range, num_of_page=1, max_pages=3) -> list[Any]:
        """
        Get news article data from the search results within a given date range.

        Returns:
            List[dict[str, str]]: A list of dictionaries representing the search results.
        """
        logging.info(f"Fetching articles within date range {_range}.")
        try:
            articles = []
            date_range = get_date_range(_range)
            till_date = datetime.strptime(date_range, '%Y-%m-%d').date()

            fetch_page_articles = lambda page_num: (
                self.articles_list.extend(
                    self.process_page_articles(till_date, page_num)
                ),
                self.fetch_next_page(_range, page_num, max_pages)
            )

            fetch_page_articles(num_of_page)
            if num_of_page == max_pages:
                self.download_excel_file()
            logging.info("Articles fetched and processed.")
            return articles
        except ErrorInFetchingArticles as e:
            logging.error(f"An error occurred in {self.__class__.__name__}.{self.fetch_articles.__name__}: {str(e)}")
            return []

    def process_page_articles(self, till_date, page_num) -> list[dict[str, str]]:
        """
        Process articles on the current page.
        """
        logging.info(f"Processing articles on page {page_num}.")
        try:
            article_elements = self.browser.find_elements(Locators.Search.RESULTS)
            articles = []

            for num, element in enumerate(article_elements, start=(page_num - 1) * len(article_elements) + 1):
                # article_date_text = self.get_field_data(element, Locators.NewsArticle.DATE)
                if not (article_date_text := self.get_field_data(element, Locators.NewsArticle.DATE)):
                    continue
                article_date = parse_date(article_date_text)
                if till_date <= article_date:
                    img_name = f"output/article_{num}.jpeg"
                    title = self.get_field_data(element, Locators.NewsArticle.TITLE)
                    description = self.get_field_data(element, Locators.NewsArticle.DESCRIPTION)
                    article_data_map = {
                        "title": title,
                        "date": article_date_text,
                        "description": description,
                        "profile_picture": self.download_images(element, img_name),
                        **check_amount_phrase(title, description)
                    }
                    articles.append(article_data_map)

            logging.info(f"Processed {len(articles)} articles on page {page_num}.")
            return articles
        except ErrorInFetchingArticles as e:
            logging.error(
                f"An error occurred in {self.__class__.__name__}.{self.process_page_articles.__name__}: {str(e)}")
            return []

    def fetch_next_page(self, _range, current_page, max_pages) -> None:
        """
        Fetch the next page if within the limit and continue fetching articles.
        """
        if current_page < max_pages:
            logging.info(f"Fetching next page: {current_page + 1}")
            try:
                next_page_button = self.browser.find_element(Locators.Search.NEXT_PAGE)
                if next_page_button:
                    next_page_button.click()
                    self.fetch_articles(_range, current_page + 1, max_pages)
                    logging.info(f"Next page {current_page + 1} fetched.")
            except NoSuchElementException as e:
                logging.error(
                    f"An error occurred in {self.__class__.__name__}.{self.fetch_next_page.__name__}: {str(e)}")
