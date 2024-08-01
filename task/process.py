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
from libraries.helper import get_date_range
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
        self.phrase = None
        self.browser = Selenium()
        self.http = HTTP()
        self.open_browser()

    def get_work_item(self):
        search_phrase = os.getenv('SEARCH_PHRASE', 'Imran Khan')
        news_category = os.getenv('NEWS_CATEGORY', 'Awards')
        months = int(os.getenv('MONTHS'))
        return search_phrase, news_category, months

    def open_browser(self) -> None:
        """
        Open a browser window and navigate to the given URL.
        """
        self.browser.open_available_browser(url="https://www.latimes.com/")
        self.browser.wait_until_page_contains_element(Locators.Search.BUTTON)

    def search_phrase(self, phrase: str):
        self.browser.click_button(Locators.Search.BUTTON)
        self.browser.wait_until_page_contains_element(Locators.Search.INPUT)
        self.browser.input_text_when_element_is_visible(Locators.Search.INPUT, phrase)
        self.browser.click_button(Locators.Search.SUBMIT)
        self.browser.wait_until_page_contains_element(Locators.Search.RESULTS_FOR_TEXT)
        self.browser.does_page_contain_element(Locators.Search.NO_RESULTS.format(phrase=phrase))
        self.phrase = phrase

    def newest_sort_by(self):
        self.browser.wait_until_element_is_visible(Locators.Sort.SELECT_OPTIONS, timeout=30)
        sorty = self.browser.find_element(Locators.Sort.SELECT_OPTIONS)
        sorty.find_element(By.XPATH, value=Locators.Sort.SELECT_OPTIONS_INPUT).click()

    def select_category(self, news_category: str) -> None:
        self.browser.wait_until_element_is_visible(Locators.Category.SEE_ALL, timeout=30)
        category = self.browser.find_element(Locators.Category.SEE_ALL)
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

    def check_amount_phrase(self, item: dict) -> None:
        """
        Set the search phrase count and check if the article contains mentions of money.

        Args:
            item (dict): Dictionary containing news article data.
            :param item:
            :param self:
        """
        title_description = f'{item["title"]} {item["description"]}' if item.get("description") else item['title']
        item["phrase"] = len(re.findall(self.phrase, title_description, flags=re.IGNORECASE))

        amount_pattern = r'\$[0-9,]+(\.[0-9]+)?|\b[0-9]+ dollars\b|\b[0-9]+ USD\b'
        item["amount"] = 'Yes' if re.search(amount_pattern, title_description) else 'No'

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
            self.check_amount_phrase(article_data_map)
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
        # articles = self.fetch_news()
        date_range = get_date_range(_range)
        start_month = datetime.strptime(date_range[0], '%Y-%m-%d').date()
        end_month = datetime.strptime(date_range[1], '%Y-%m-%d').date()
        dates = self.browser.find_elements(Locators.Search.RESULTS)
        valid_start_date_found = self.extract_dates(dates)

        if [date for date in valid_start_date_found if start_month >= date <= end_month]:
            self.download_news_data_excel()

        else:
            next_page_button = self.browser.find_element(Locators.Search.NEXT_PAGE)
            if next_page_button:
                next_page_button.click()
                self.fetch_and_process_articles(range)

    def parse_date(self, date_text):
        for fmt in ('%B %d, %Y', '%b %d, %Y', '%b. %d, %Y'):
            try:
                return datetime.strptime(date_text, fmt).date()
            except ValueError:
                continue
        raise ValueError(f"Date format for '{date_text}' not recognized")

    def extract_dates(self, ele):
        """
        Extracts text from a list of WebElement instances and returns a list of non-empty strings.

        Args:
            ele (list): List of WebElement instances.

        Returns:
            list: List of extracted date strings.
        """
        return [
            self.parse_date(element.find_element(by=By.XPATH, value=Locators.NewsArticle.DATE).text.strip())
            for element in ele
            if element.find_element(by=By.XPATH, value=Locators.NewsArticle.DATE).text.strip()
        ]
