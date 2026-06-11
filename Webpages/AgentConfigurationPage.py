from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException


class AgentConfigurationPage:

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 180)

        self.status_badge = (
            By.XPATH,
            "//div[contains(@class,'tracking-wider')]"
        )

        self.agent_name = (
            By.XPATH,
            "//p[contains(@class,'font-semibold') and contains(@class,'truncate')]"
        )

        self.save_button = (
            By.XPATH,
            "//button[normalize-space()='Save']"
        )

        self.back_button = (
            By.XPATH,
            "//*[self::a or self::button][normalize-space()='Back']"
        )

        self.agent_exists_error = (
            By.XPATH,
            "//*[contains(text(),'Agent with this name already exists')]"
        )

        self.error_toast = (
            By.XPATH,
            "//div[contains(@class,'Toastify__toast--error')]"
        )

        self.leave_page_button = (
            By.XPATH,
            "//button[normalize-space()='Leave Page']"
        )

    def wait_for_agent_creation(self):
        self.wait.until(
            EC.url_contains("/build-agent/configure")
        )

    def verify_agent_configuration_page(self):
        return "/build-agent/configure" in self.driver.current_url

    def get_current_url(self):
        return self.driver.current_url

    def get_agent_name(self):
        return self.wait.until(
            EC.visibility_of_element_located(self.agent_name)
        ).text

    def wait_for_error_toast_to_clear(self, timeout=10):
        try:
            WebDriverWait(self.driver, timeout).until_not(
                EC.visibility_of_element_located(self.error_toast)
            )
        except TimeoutException:
            pass

    def click_save(self):
        save_btn = self.wait.until(
            EC.element_to_be_clickable(self.save_button)
        )

        try:
            save_btn.click()
        except ElementClickInterceptedException:
            self.wait_for_error_toast_to_clear()
            self.driver.execute_script("arguments[0].click();", save_btn)

    def wait_for_agent_name_update(self):

        long_wait = WebDriverWait(self.driver, 300)

        long_wait.until(
            lambda d: d.find_element(*self.agent_name).text.strip() != "Untitled Agent"
        )

        return self.driver.find_element(*self.agent_name).text.strip()

    def go_back_to_agents(self):
        self.wait.until(
            EC.element_to_be_clickable(self.back_button)
        ).click()

        self.handle_unsaved_changes_dialog()

        self.wait.until(
            EC.url_contains("/agents")
        )

    def handle_unsaved_changes_dialog(self, timeout=5):
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable(self.leave_page_button)
            ).click()
        except TimeoutException:
            pass

    def get_status(self):
        return self.wait.until(
            EC.visibility_of_element_located(self.status_badge)
        ).text.strip().lower()

    def is_duplicate_name_error_present(self):
        try:
            WebDriverWait(self.driver, 5).until(
                EC.visibility_of_element_located(self.agent_exists_error)
            )
            return True

        except TimeoutException:
            return False

    def get_creation_error(self):
        try:
            return WebDriverWait(self.driver, 5).until(
                EC.visibility_of_element_located(self.agent_exists_error)
            ).text

        except TimeoutException:
            return None
