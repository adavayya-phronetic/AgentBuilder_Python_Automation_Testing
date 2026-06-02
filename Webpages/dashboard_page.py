from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class DashboardPage:

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)

        self.logout_dropdown = (
            By.XPATH,
            "//span[contains(@title,'@')]"
        )

        self.logout_link = (
            By.XPATH,
            "//div[@role='menuitem' and contains(.,'Sign out')]"
        )

    def logout(self):

        self.wait.until(
            EC.element_to_be_clickable(self.logout_dropdown)
        ).click()

        self.wait.until(
            EC.element_to_be_clickable(self.logout_link)
        ).click()