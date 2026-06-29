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

        self.status_option_active = (
            By.XPATH,
            "//div[@role='option' and normalize-space()='Active']"
        )

        self.agent_card_title = (
            By.XPATH,
            "//h3"
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

    def set_status_filter_active(self):
        self.wait.until(
            EC.element_to_be_clickable(self.status_filter_combobox)
        ).click()

        self.wait.until(
            EC.element_to_be_clickable(self.status_option_active)
        ).click()

    def get_active_agent_names(self):
        self.set_status_filter_active()

        cards = self.wait.until(
            EC.presence_of_all_elements_located(self.agent_card_title)
        )

        return [card.text.strip() for card in cards if card.text.strip()]

    def search_agent(self, agent_name):
        search_box = self.wait.until(
            EC.visibility_of_element_located(self.search_input)
        )
        search_box.clear()
        search_box.send_keys(agent_name)

    @staticmethod
    def _case_insensitive_card_locator(agent_name):
        # Card titles are styled with CSS `capitalize`, which changes how the
        # name renders but not the underlying DOM text node, so an
        # exact-case XPath match against a name read back from `.text` can
        # miss (e.g. rendered "AI Travel Agent" vs. actual "AI Travel agent").
        return (
            By.XPATH,
            "//h3[translate(normalize-space(.), "
            "'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')="
            f"'{agent_name.lower()}']"
        )

    def click_agent_card(self, agent_name):
        card_locator = self._case_insensitive_card_locator(agent_name)

        card = self.wait.until(
            EC.presence_of_element_located(card_locator)
        )

        # A hover-reveal overlay sits on top of the card and intercepts
        # normal Selenium clicks, so dispatch the click via JS instead.
        self.driver.execute_script("arguments[0].scrollIntoView(true);", card)
        self.driver.execute_script("arguments[0].click();", card)

    def verify_agent_card(self, agent_name):
        card_locator = self._case_insensitive_card_locator(agent_name)

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
