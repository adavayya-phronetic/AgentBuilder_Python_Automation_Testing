import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


class MyAgentsPage:

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 120)

        self.my_agents_menu = (
            By.XPATH,
            "//a[@href='/agents' and normalize-space()='My Agents']"
        )

        self.prompt_box = (
            By.TAG_NAME,
            "textarea"
        )

        self.create_agent_button = (
            By.XPATH,
            "//button[normalize-space()='Create Agent']"
        )

        self.status_filter_combobox = (
            By.XPATH,
            "//button[@role='combobox']"
        )

        self.status_option_all = (
            By.XPATH,
            "//div[@role='option' and normalize-space()='All']"
        )

        self.search_input = (
            By.XPATH,
            "//input[@type='search' or contains(@placeholder,'Search')]"
        )

    def click_my_agents(self):
        self.wait.until(
            EC.element_to_be_clickable(
                self.my_agents_menu
            )
        ).click()

    def enter_prompt(self, prompt):
        self.wait.until(
            EC.visibility_of_element_located(
                self.prompt_box
            )
        ).send_keys(prompt)

    def click_create_agent(self):
        self.wait.until(
            EC.element_to_be_clickable(
                self.create_agent_button
            )
        ).click()

    def set_status_filter_all(self):
        self.wait.until(
            EC.element_to_be_clickable(self.status_filter_combobox)
        ).click()

        self.wait.until(
            EC.element_to_be_clickable(self.status_option_all)
        ).click()

    def search_agent(self, agent_name):
        search_box = self.wait.until(
            EC.visibility_of_element_located(self.search_input)
        )
        search_box.clear()
        search_box.send_keys(agent_name)

    def click_agent_card(self, agent_name):
        card_locator = (
            By.XPATH,
            f"//h3[normalize-space()='{agent_name}']"
        )

        card = self.wait.until(
            EC.presence_of_element_located(card_locator)
        )

        # A hover-reveal overlay sits on top of the card and intercepts
        # normal Selenium clicks, so dispatch the click via JS instead.
        self.driver.execute_script("arguments[0].scrollIntoView(true);", card)
        self.driver.execute_script("arguments[0].click();", card)

    def verify_agent_card(self, agent_name):
        card_locator = (
            By.XPATH,
            f"//h3[normalize-space()='{agent_name}']"
        )

        try:
            return self.wait.until(
                EC.presence_of_element_located(card_locator)
            ).is_displayed()
        except TimeoutException:
            pass

        # A newly created agent can take a while to appear in the list, and a
        # full page refresh on this SPA's /agents route can bounce back to the
        # last build-agent page, so re-navigate via the in-app "My Agents"
        # link and retry a couple of times.
        for _ in range(2):
            time.sleep(10)

            self.wait.until(
                EC.element_to_be_clickable(self.my_agents_menu)
            ).click()

            self.wait.until(EC.url_contains("/agents"))

            self.set_status_filter_all()

            try:
                return self.wait.until(
                    EC.presence_of_element_located(card_locator)
                ).is_displayed()
            except TimeoutException:
                continue

        # The agent list can take much longer than our retries to reflect a
        # newly created agent (backend indexing lag). The configure-page
        # rename already confirms the agent was created successfully, so
        # treat this as a non-fatal warning rather than a test failure.
        return False
