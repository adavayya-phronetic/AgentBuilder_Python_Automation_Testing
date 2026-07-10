import allure
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class LandingPage:

    GET_STARTED_BUTTON = (
        By.XPATH,
        "//a[normalize-space()='Get Started']"
    )

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)

    @allure.step("Open agent-builder landing page")
    def open_page(self):
        self.driver.get("https://agent-builder.phronetic.ai")

    @allure.step("Click 'Get Started' and wait for auth page")
    def click_get_started(self):
        self.wait.until(
            EC.element_to_be_clickable(self.GET_STARTED_BUTTON)
        ).click()

        self.wait.until(
            EC.url_contains("/auth")
        )
