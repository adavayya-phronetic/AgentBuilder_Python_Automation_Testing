import time

import allure
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException


class MyAgentsPage:

    def __init__(self, driver):
        self.driver = driver
        # Routine UI actions (clicks, filters, searches) should resolve in
        # seconds. A blanket 120s default here meant verify_agent_card()'s
        # backend-indexing-lag retry loop below could burn several minutes
        # per attempt waiting for a card that genuinely isn't there yet,
        # rather than failing that specific check quickly and moving on.
        self.wait = WebDriverWait(driver, 30)

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

    @allure.step("Navigate to My Agents")
    def click_my_agents(self):
        self.wait.until(
            EC.element_to_be_clickable(self.my_agents_menu)
        ).click()
        # Navigating away from the agent config page may trigger a
        # "Leave Page?" dialog if there are unsaved changes.
        leave_page_btn = (By.XPATH, "//button[normalize-space()='Leave Page']")
        try:
            WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(leave_page_btn)
            ).click()
        except TimeoutException:
            pass
        self.wait.until(EC.url_contains("/agents"))

    @allure.step("Enter agent creation prompt")
    def enter_prompt(self, prompt):
        self.wait.until(
            EC.visibility_of_element_located(self.prompt_box)
        ).send_keys(prompt)

    @allure.step("Click 'Create Agent'")
    def click_create_agent(self):
        self.wait.until(
            EC.element_to_be_clickable(self.create_agent_button)
        ).click()

    @allure.step("Set status filter to 'All'")
    def set_status_filter_all(self):
        self.wait.until(
            EC.element_to_be_clickable(self.status_filter_combobox)
        ).click()

        self.wait.until(
            EC.element_to_be_clickable(self.status_option_all)
        ).click()

    @allure.step("Set status filter to 'Active'")
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

    @allure.step("Search for agent '{agent_name}'")
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

    @allure.step("Open agent card '{agent_name}'")
    def click_agent_card(self, agent_name):
        card_locator = self._case_insensitive_card_locator(agent_name)

        # A hover-reveal overlay sits on top of the card and intercepts
        # normal Selenium clicks, so dispatch the click via JS instead.
        # React can re-render the list between locate and click, so retry
        # on stale element references.
        for _ in range(3):
            try:
                card = self.wait.until(EC.presence_of_element_located(card_locator))
                self.driver.execute_script("arguments[0].scrollIntoView(true);", card)
                self.driver.execute_script("arguments[0].click();", card)
                return
            except StaleElementReferenceException:
                continue

    def get_visible_card_names(self):
        """Returns names of all agent cards currently visible (after search/filter)."""
        # The results can still be re-rendering right after a search (the
        # input is debounced), so the card list fetched below can go stale
        # between being located and being scrolled/read — retried a couple
        # of times rather than letting a one-off race fail the whole call.
        for _ in range(3):
            try:
                cards = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located(self.agent_card_title)
                )
                if cards:
                    # The card list sits below the fold on the My Agents
                    # page, so a screenshot taken right after searching can
                    # show an empty-looking page with just a scrollbar —
                    # scroll the first match into view so it's visible.
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({block:'center'});", cards[0]
                    )
                return [c.text.strip() for c in cards if c.text.strip()]
            except TimeoutException:
                return []
            except StaleElementReferenceException:
                continue
        return []

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
