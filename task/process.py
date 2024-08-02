import os
import re
import time
from datetime import datetime
from typing import List
from RPA.Browser.Selenium import Selenium
from RPA.HTTP import HTTP
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from openpyxl import Workbook
from libraries.helper import get_date_range, extract_dates, check_amount_phrase
from resources.locators import Locators

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

    def open_browser(self) -> None:
        """
        Open a browser window and navigate to the given URL.
        """
        self.browser.open_available_browser(url="https://www.latimes.com/")

    def search_phrase(self, phrase: str):
        self.browser.wait_until_page_contains_element(Locators.Search.BUTTON)
        self.browser.click_button(Locators.Search.BUTTON)
        # self.browser.wait_until_page_contains_element(Locators.Search.INPUT)
        # self.browser.input_text_when_element_is_visible(Locators.Search.INPUT, phrase)
        self.browser.wait_until_element_is_visible(Locators.Search.INPUT, timeout=30)
        self.browser.input_text(Locators.Search.INPUT, phrase)
        self.browser.click_button(Locators.Search.SUBMIT)
        self.browser.wait_until_page_contains_element(Locators.Search.RESULTS_FOR_TEXT)
        self.browser.does_page_contain_element(Locators.Search.NO_RESULTS.format(phrase=phrase))

    def newest_sort_by(self):
        self.browser.wait_until_element_is_visible(Locators.Sort.SELECT_OPTIONS, timeout=30)
        sorty = self.browser.find_element(Locators.Sort.SELECT_OPTIONS)
        sorty.find_element(By.XPATH, value=Locators.Sort.SELECT_OPTIONS_INPUT).click()

    def select_category(self, news_category: str) -> None:
        # self.browser.wait_until_element_is_visible(Locators.Category.SEE_ALL, timeout=60)
        # category = self.browser.find_element(Locators.Category.SEE_ALL)
        # category.click()
        category = self.browser.wait_until_element_is_visible(Locators.Category.SEE_ALL, timeout=60)
        category = category.find_element(Locators.Category.SEE_ALL)
        category.click()
        category = self.browser.find_element(Locators.Category.SELECT_CATEGORY.format(news_category))
        category.click()

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
        except Exception:
            return ''

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
        except Exception:
            return ''

    def fetch_news(self) -> list[dict[str, str]]:
        """
        Get news article data from the search results.

        Returns:
            List[dict[str, str]]: A list of dictionaries representing the search results.
        """
        time.sleep(5)
        article_elements = self.browser.find_elements(Locators.Search.RESULTS)
        articles = []
        for num, element in enumerate(article_elements, start=1):
            img_name = f"output/article_{num}.jpeg"
            article_data_map = {
                "title": self.get_field_data(element, Locators.NewsArticle.TITLE),
                "date": self.get_field_data(element, Locators.NewsArticle.DATE),
                "description": self.get_field_data(element, Locators.NewsArticle.DESCRIPTION),
                "profile_picture": self.download_images(element, img_name)
            }
            check_amount_phrase(article_data_map)
            articles.append(article_data_map)
        return articles

    def download_news_data_excel(self) -> None:
        """Download news article data into an Excel file."""
        workbook = Workbook()
        exception_sheet = workbook.active

        exception_sheet.title = "Articles"
        exception_sheet.append(
            ["Title", "Date", "Description", "ProfilePicture", "Phrase", "Amount"])

        for item in self.fetch_news():
            row = [
                item.get("title", ""),
                item.get("date", ""),
                item.get("description", ""),
                item.get("profile_picture", ""),
                item.get("phrase", ""),
                item.get("amount", "")
            ]
            exception_sheet.append(row)

        output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
        os.makedirs(output_dir, exist_ok=True)
        workbook.save(os.path.join(output_dir, 'news_data.xlsx'))

    def fetch_and_process_articles(self, _range):
        """Fetch articles, process them, and recursively fetch more if needed."""
        date_range = get_date_range(_range)
        start_month = datetime.strptime(date_range[0], '%Y-%m-%d').date()
        end_month = datetime.strptime(date_range[1], '%Y-%m-%d').date()
        dates = self.browser.find_elements(Locators.Search.RESULTS)
        valid_start_date_found = extract_dates(dates)

        if [date for date in valid_start_date_found if start_month >= date <= end_month]:
            self.download_news_data_excel()

        else:
            next_page_button = self.browser.find_element(Locators.Search.NEXT_PAGE)
            if next_page_button:
                next_page_button.click()
                self.fetch_and_process_articles(range)

