from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


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