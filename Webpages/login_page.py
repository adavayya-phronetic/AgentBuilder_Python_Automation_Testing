import allure
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


class LoginPage:

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)

        self.username = (
            By.XPATH,
            "//input[@name='email']"
        )

        self.password = (
            By.XPATH,
            "//input[@name='password']"
        )

        self.login_button = (
            By.XPATH,
            "//button[@type='submit' and normalize-space()='Sign in']"
        )

        self.error_message = (
            By.XPATH,
            "//div[contains(@class,'text-destructive') and normalize-space()='Incorrect email or password']"
        )

        self.email_field_error = (
            By.XPATH,
            "//p[contains(@class,'text-destructive') and normalize-space()='Please enter a valid email']"
        )

        self.password_field_error = (
            By.XPATH,
            "//p[contains(@class,'text-destructive') and normalize-space()='Password is required']"
        )

    @allure.step("Submit login form as {user}")
    def login(self, user, pwd):
        print("Current URL:", self.driver.current_url)

        self.wait.until(
            EC.visibility_of_element_located(self.username)
        ).send_keys(user)

        self.wait.until(
            EC.visibility_of_element_located(self.password)
        ).send_keys(pwd)

        self.wait.until(
            EC.element_to_be_clickable(self.login_button)
        ).click()

    def is_on_login_page(self):
        return "/auth" in self.driver.current_url

    def get_login_error(self, timeout=10):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.error_message)
            ).text
        except TimeoutException:
            return None

    def get_email_field_error(self, timeout=5):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.email_field_error)
            ).text
        except TimeoutException:
            return None

    def get_password_field_error(self, timeout=5):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.password_field_error)
            ).text
        except TimeoutException:
            return None
