import os
import logging
from RPA.HTTP import HTTP
from RPA.Browser.Selenium import Selenium
from datetime import datetime
from typing import List, Any
from dotenv import load_dotenv
from openpyxl.workbook import Workbook
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from resources.locators import Locators
from libraries.models import ArticleModel
from libraries.helper import get_date_range, check_amount_phrase, parse_date
from libraries.exceptions import ElementNotFoundException, ErrorInDownloadException, ErrorInFetchingArticles

load_dotenv()


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
        self.articles_list = []

    def open_browser(self) -> None:
        """
        Open a browser window and navigate to the given URL.
        """
        try:
            self.browser.open_available_browser(url="https://www.latimes.com/", maximized=True)
        except ElementNotFoundException as e:
            logging.error(f"An error occurred in {self.__class__.__name__}.{self.open_browser.__name__}: {str(e)}")

    def search_phrase(self, phrase: str) -> None:
        """
        Search for the given phrase and navigate to the results.
        """
        try:
            self.browser.wait_until_page_contains_element(Locators.Search.BUTTON)
            self.browser.click_button(Locators.Search.BUTTON)
            self.browser.wait_until_element_is_visible(Locators.Search.INPUT, timeout=30)
            self.browser.input_text(Locators.Search.INPUT, phrase)
            self.browser.click_button(Locators.Search.SUBMIT)
            self.browser.wait_until_page_contains_element(Locators.Search.RESULTS_FOR_TEXT)
            self.browser.does_page_contain_element(Locators.Search.NO_RESULTS.format(phrase=phrase))
        except ElementNotFoundException as e:
            logging.error(f"An error occurred in {self.__class__.__name__}.{self.open_browser.__name__}: {str(e)}")

    def newest_sort_by(self) -> None:
        try:
            """Sort search results by latest."""
            self.browser.wait_until_element_is_visible(Locators.Sort.SELECT_OPTIONS, timeout=30)
            sorty = self.browser.find_element(Locators.Sort.SELECT_OPTIONS)
            sorty.find_element(By.XPATH, value=Locators.Sort.SELECT_OPTIONS_INPUT).click()
        except ElementNotFoundException as e:
            logging.error(f"An error occurred in {self.__class__.__name__}.{self.open_browser.__name__}: {str(e)}")

    def select_category(self, news_category: str) -> None:
        try:
            category = self.browser.find_element(Locators.Category.SEE_ALL)
            category.click()
            category = self.browser.find_element(Locators.Category.SELECT_CATEGORY.format(name=news_category))
            category.click()
        except ElementNotFoundException as e:
            logging.error(f"An error occurred in {self.__class__.__name__}.{self.open_browser.__name__}: {str(e)}")

    @staticmethod
    def get_field_data(element: WebElement, locator) -> str:
        """
        Get text data from a WebElement based on a locator.

        Args:
            element (WebElement): The WebElement to extract data from.
            locator: Locator to find the desired element.

        Returns:
            str: The text data found.
        """
        try:
            return element.find_element(by=By.XPATH, value=locator).text
        except ElementNotFoundException as e:
            logging.error(f"An error occurred in {self.__class__.__name__}.{self.open_browser.__name__}: {str(e)}")

    def download_images(self, element: WebElement, file_path) -> str:
        """
        Download the profile picture associated with a news article.

        Args:
            element (WebElement): The WebElement representing the news article.
            file_path (str): The path to save the downloaded profile picture.

        Returns:
            str: The file path where the profile picture is saved.
        """
        try:
            img = element.find_element(by=By.XPATH, value=Locators.NewsArticle.PROF_PIC)
            self.http.download(img.get_attribute('src'), file_path)
            return file_path
        except ElementNotFoundException as e:
            logging.error(f"An error occurred in {self.__class__.__name__}.{self.open_browser.__name__}: {str(e)}")

    def download_excel_file(self) -> None:

        """Download news article data into an Excel file."""
        try:
            workbook = Workbook()
            exception_sheet = workbook.active

            exception_sheet.title = "Articles"
            exception_sheet.append(
                ["Title", "Date", "Description", "ProfilePicture", "Phrase", "Amount"])

            for item in self.articles_list:
                validated_item = ArticleModel(**item)

                # Create a row with the validated data
                row = [
                    validated_item.title,
                    validated_item.date,
                    validated_item.description,
                    validated_item.profile_picture,
                    validated_item.phrase,
                    validated_item.amount
                ]
                exception_sheet.append(row)
            # to store images and xlsx file in same folder
            output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
            os.makedirs(output_dir, exist_ok=True)
            workbook.save(os.path.join(output_dir, 'los-angeles-times.xlsx'))
        except ErrorInDownloadException as e:
            logging.error(f"An error occurred in {self.__class__.__name__}.{self.open_browser.__name__}: {str(e)}")

    def fetch_articles(self, _range, num_of_page=1, max_pages=3) -> list[Any]:
        """
        Get news article data from the search results within a given date range.

        Returns:
            List[dict[str, str]]: A list of dictionaries representing the search results.
        """
        try:
            articles = []
            date_range = get_date_range(_range)
            start_date = datetime.strptime(date_range[0], '%Y-%m-%d').date()
            end_date = datetime.strptime(date_range[1], '%Y-%m-%d').date()

            # Lambda function to process articles and fetch the next page if within the limit
            fetch_page_articles = lambda page_num: (
                self.articles_list.extend(
                    self.process_page_articles(start_date, end_date, page_num)
                ),
                self.fetch_next_page(_range, page_num, max_pages)
            )

            # Process current page articles and decide whether to fetch the next page
            download = fetch_page_articles(num_of_page)
            if not download[0]:
                self.download_excel_file()
            return articles
        except ErrorInFetchingArticles as e:
            logging.error(f"An error occurred in {self.__class__.__name__}.{self.open_browser.__name__}: {str(e)}")

    def process_page_articles(self, start_date, end_date, page_num) -> list[dict[str, str]]:
        """
        Process articles on the current page.
        """
        try:
            article_elements = self.browser.find_elements(Locators.Search.RESULTS)
            articles = []

            for num, element in enumerate(article_elements, start=(page_num - 1) * len(article_elements) + 1):
                article_date_text = self.get_field_data(element, Locators.NewsArticle.DATE)
                article_date = parse_date(article_date_text)
                if start_date >= article_date >= end_date:
                    img_name = f"output/article_{num}.jpeg"
                    article_data_map = {
                        "title": self.get_field_data(element, Locators.NewsArticle.TITLE),
                        "date": article_date_text,
                        "description": self.get_field_data(element, Locators.NewsArticle.DESCRIPTION),
                        "profile_picture": self.download_images(element, img_name)
                    }
                    check_amount_phrase(article_data_map)
                    articles.append(article_data_map)

            return articles
        except ErrorInFetchingArticles as e:
            logging.error(f"An error occurred in {self.__class__.__name__}.{self.open_browser.__name__}: {str(e)}")

    def fetch_next_page(self, _range, current_page, max_pages) -> None:
        """
        Fetch the next page if within the limit and continue fetching articles.
        """
        if current_page < max_pages:
            try:
                next_page_button = self.browser.find_element(Locators.Search.NEXT_PAGE)
                if next_page_button:
                    next_page_button.click()
                    self.fetch_articles(_range, current_page + 1, max_pages)
            except ElementNotFoundException as e:
                logging.error(f"An error occurred in {self.__class__.__name__}.{self.open_browser.__name__}: {str(e)}")
