import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


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

        self.back_button = (
            By.XPATH,
            "//*[self::a or self::button][normalize-space()='Back']"
        )

        self.agent_exists_error = (
            By.XPATH,
            "//*[contains(text(),'Agent with this name already exists')]"
        )

        self.leave_page_button = (
            By.XPATH,
            "//button[normalize-space()='Leave Page']"
        )

        self.tool_search_error = (
            By.XPATH,
            "//*[contains(text(),'I encountered an issue while searching for supporting tools')]"
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

    def is_tool_search_error_present(self):
        try:
            return self.driver.find_element(*self.tool_search_error).is_displayed()
        except Exception:
            return False

    def _wait_for_name_to_stabilize(self, current_name, timeout=30, poll=1, stable_checks=3):
        # The agent name can still be streaming in when first detected,
        # so wait until it stops changing before treating it as final.
        end_time = time.monotonic() + timeout
        stable_count = 0

        while time.monotonic() < end_time:
            time.sleep(poll)
            latest_name = self.driver.find_element(*self.agent_name).text.strip()

            if latest_name == current_name:
                stable_count += 1
                if stable_count >= stable_checks:
                    return latest_name
            else:
                current_name = latest_name
                stable_count = 0

        return current_name

    def wait_for_agent_name_update(self):

        def name_updated_or_tool_error(d):
            name = d.find_element(*self.agent_name).text.strip()
            if name != "Untitled Agent":
                return True
            return self.is_tool_search_error_present()

        try:
            WebDriverWait(self.driver, 480).until(name_updated_or_tool_error)
        except TimeoutException:
            pass

        agent_name = self.driver.find_element(*self.agent_name).text.strip()

        if agent_name != "Untitled Agent":
            agent_name = self._wait_for_name_to_stabilize(agent_name)

        if agent_name == "Untitled Agent":
            # The chat can finish and rename the agent on the backend without
            # the page header re-rendering. Reload once to re-sync state.
            self.driver.refresh()

            try:
                WebDriverWait(self.driver, 120).until(
                    lambda d: d.find_element(*self.agent_name).text.strip() != "Untitled Agent"
                )
            except TimeoutException:
                raise AssertionError(
                    "Agent creation failed: the agent remained 'Untitled Agent' "
                    "even after the chat finished and the page was refreshed."
                )

            agent_name = self.driver.find_element(*self.agent_name).text.strip()
            agent_name = self._wait_for_name_to_stabilize(agent_name)

        return agent_name

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
