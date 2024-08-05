class Locators:
    class Search:
        BUTTON = "//button[@data-element='search-button']"
        INPUT = "//input[@data-element='search-form-input']"
        SUBMIT = "//button[@data-element='search-submit-button']"
        NO_RESULTS = """//div[contains(text(),'There are not any results that match "{phrase}".')]"""
        RESULTS_FOR_TEXT = "//h1[text()='Search results for']"
        RESULTS = '//ul[@class="search-results-module-results-menu"]//li'
        NEXT_PAGE = "//div[@class='search-results-module-next-page']"

    class Category:
        SEE_ALL = "(//button[@class='button see-all-button'])[1]"
        SELECT_CATEGORY = "//span[text()='{name}']"

    class Sort:
        SELECT_OPTIONS = "//select[@class='select-input']"
        SELECT_OPTIONS_INPUT = "//option[@value=1]"

    class NewsArticle:
        TITLE = ".//h3//a[@class='link']"
        DATE = ".//p[@class='promo-timestamp']"
        DESCRIPTION = ".//p[@class='promo-description']"
        PROF_PIC = ".//img"
