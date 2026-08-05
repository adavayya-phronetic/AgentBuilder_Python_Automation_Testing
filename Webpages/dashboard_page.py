from urllib.parse import urlparse

import allure
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


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

        # Sign out redirects off the dashboard entirely, to the public
        # marketing site (www.phronetic.ai) rather than a fixed in-app URL.
        # That page is a heavier animated/hydrating SPA, so document.readyState
        # turns "complete" well before it actually paints — waiting for a
        # concrete visible element is what actually confirms the render, and
        # avoids a screenshot landing mid-navigation and coming back blank.
        self.marketing_site_get_started = (
            By.XPATH,
            "//*[normalize-space()='Get Started']"
        )

        self.create_agent_button = (
            By.XPATH,
            "//button[contains(normalize-space(.),'Create Agent')]"
        )

        self.greeting_heading = (
            By.XPATH,
            "//*[starts-with(normalize-space(.),'Good morning,') or "
            "starts-with(normalize-space(.),'Good afternoon,') or "
            "starts-with(normalize-space(.),'Good evening,')]"
        )

        # The 5 summary cards. Each card's own icon button carries a
        # distinct, descriptive title attribute — a far more stable
        # locator than the card's visual position or styling classes.
        self.agents_card_icon = (By.XPATH, "//button[@title='View all Agents']")
        self.tools_created_card_icon = (By.XPATH, "//button[@title='View all Tools Created']")
        self.unique_users_card_icon = (By.XPATH, "//button[@title='View Unique Users sources']")
        self.active_gateways_card_icon = (By.XPATH, "//button[@title='View Active Gateways sources']")

        # Every summary card follows the same template: an icon, then a
        # `text-2xl font-bold` count in its own wrapper div, then a
        # `text-[11px] text-gray-500` label in the following wrapper div.
        # The 'Sessions' label text alone is ambiguous — the Top Agents
        # table below has its own unrelated "Sessions" column header — so
        # the label locator is anchored on that exact small/gray class to
        # only ever match the summary card, never the table header.
        self._card_count_template = (
            "//p[normalize-space()='{label}' and contains(@class,'text-[11px]')]"
            "/parent::div/preceding-sibling::div[1]/p"
        )

        self.agents_count = (By.XPATH, self._card_count_template.format(label="Agents"))
        self.tools_created_count = (By.XPATH, self._card_count_template.format(label="Tools Created"))
        self.sessions_count = (By.XPATH, self._card_count_template.format(label="Sessions"))
        self.unique_users_count = (By.XPATH, self._card_count_template.format(label="Unique Users"))
        self.active_gateways_count = (By.XPATH, self._card_count_template.format(label="Active Gateways"))

        # --- Unique Users popup ---
        self.unique_users_popup_heading = (
            By.XPATH,
            "//div[@role='dialog']//*[normalize-space()='Unique Users']"
        )

        self.unique_users_search_input = (
            By.XPATH,
            "//input[@placeholder='Search users by name or email']"
        )

        self.unique_users_popup_close_button = (
            By.XPATH,
            "//div[@role='dialog']//button[normalize-space()='Close']"
        )

        # Targets the element whose own direct text is the email address,
        # rather than a wrapping row container — confirmed the wrapper-based
        # version double-matched (an outer and an inner container both
        # satisfying "descendant text contains '@'" for the same one user).
        self.unique_users_result_rows = (
            By.XPATH,
            "//div[@role='dialog']//*[contains(text(),'@')]"
        )

        # --- Active Gateways popup ---
        self.active_gateways_popup_heading = (
            By.XPATH,
            "//div[@role='dialog']//*[normalize-space()='Active Gateways']"
        )

        self.active_gateways_empty_message = (
            By.XPATH,
            "//div[@role='dialog']//*[contains(text(),'No active gateways available')]"
        )

        self.active_gateways_popup_close_button = (
            By.XPATH,
            "//div[@role='dialog']//button[normalize-space()='Close']"
        )

        # --- Performance & Usage: date/time filter ---
        self.date_time_filter_button = (
            By.XPATH,
            "//button[contains(.,'Pick a date') or contains(.,'date')]"
        )

        self.date_filter_start_input = (
            By.XPATH,
            "//label[normalize-space()='Start']/following::input[@type='date'][1]"
        )

        self.date_filter_end_input = (
            By.XPATH,
            "//label[normalize-space()='End']/following::input[@type='date'][1]"
        )

        self.date_filter_apply_button = (By.XPATH, "//button[normalize-space()='Apply']")
        self.date_filter_clear_button = (By.XPATH, "//button[normalize-space()='Clear']")

        self.session_performance_heading = (
            By.XPATH,
            "//*[normalize-space()='Session Performance']"
        )

        # The heading and its count+unit live in sibling divs within one
        # shared row container — targeting the bold count span directly,
        # rather than the row's combined text, avoids also picking up the
        # unit label ('sessions'/'credits') or the heading text itself.
        self.session_performance_count = (
            By.XPATH,
            "//p[normalize-space()='Session Performance']/ancestor::div[contains(@class,'justify-between')][1]"
            "//span[contains(@class,'font-bold')]"
        )

        self.credit_usage_heading = (
            By.XPATH,
            "//*[normalize-space()='Credit Usage']"
        )

        # Confirmed: Credit Usage's DOM structure changes between its
        # has-data state (value in a <span>, label separate) and its
        # empty/zero state (value and label as sibling <p> tags) — a
        # locator tied to one specific structure breaks in the other.
        # This instead scopes to the shared card containing both graphs
        # (identified by its stable layout classes) and takes the first
        # span/p containing a rupee sign, which holds in both states and
        # excludes the chart's own SVG axis labels (<tspan>, not
        # span/p) and the unrelated Wallet balance in the left sidebar.
        self.credit_usage_amount = (
            By.XPATH,
            "(//div[contains(@class,'xl:flex-row') and contains(@class,'overflow-hidden')]"
            "//*[(self::span or self::p) and contains(text(),'₹')])[1]"
        )

        # --- Agents & Activity: "View All" link ---
        self.agents_activity_view_all_link = (
            By.XPATH,
            "//span[normalize-space()='View All']/ancestor::*[self::a or self::button][1]"
        )

    @allure.step("Click 'Create Agent'")
    def click_create_agent(self):
        self.wait.until(
            EC.element_to_be_clickable(self.create_agent_button)
        ).click()
        # Navigates straight to the My Agents prompt page (/agents).
        self.wait.until(EC.url_contains("/agents"))

    @allure.step("Log out via user menu")
    def logout(self):
        self.wait.until(
            EC.element_to_be_clickable(self.logout_dropdown)
        ).click()

        self.wait.until(
            EC.element_to_be_clickable(self.logout_link)
        ).click()

        WebDriverWait(self.driver, 30).until(
            EC.visibility_of_element_located(self.marketing_site_get_started)
        )

    @allure.step("Navigate to Dashboard")
    def navigate_to_dashboard(self):
        # A hard navigation rather than clicking a sidebar nav link — this
        # suite's shared-session tests can leave the browser on any page,
        # and a nav link that isn't present in every context (confirmed
        # elsewhere in this suite: a Build page's own sidebar lacks links
        # the main app shell has) is a real, previously-hit failure mode.
        parsed = urlparse(self.driver.current_url)
        dashboard_url = f"{parsed.scheme}://{parsed.netloc}/dashboard"
        self.driver.get(dashboard_url)
        self.is_dashboard_loaded()

    @allure.step("Click 'Refresh Dashboard'")
    def click_refresh_dashboard(self):
        self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[@title='Refresh Dashboard']"))
        ).click()

    def is_dashboard_loaded(self, timeout=15):
        """Confirms the greeting heading and all 5 summary cards rendered —
        the clearest signal the Dashboard itself (not just the URL) loaded."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.greeting_heading)
            )
            for locator in (
                self.agents_count, self.tools_created_count, self.sessions_count,
                self.unique_users_count, self.active_gateways_count,
            ):
                WebDriverWait(self.driver, timeout).until(
                    EC.visibility_of_element_located(locator)
                )
            return True
        except TimeoutException:
            return False

    def get_card_count(self, locator, timeout=10):
        return int(WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located(locator)
        ).text.strip())

    @allure.step("Click the Agents card icon")
    def click_agents_card_icon(self):
        self.wait.until(EC.element_to_be_clickable(self.agents_card_icon)).click()

    @allure.step("Click the Tools Created card icon")
    def click_tools_created_card_icon(self):
        self.wait.until(EC.element_to_be_clickable(self.tools_created_card_icon)).click()

    @allure.step("Click the Unique Users card icon")
    def click_unique_users_card_icon(self):
        self.wait.until(EC.element_to_be_clickable(self.unique_users_card_icon)).click()

    @allure.step("Click the Active Gateways card icon")
    def click_active_gateways_card_icon(self):
        self.wait.until(EC.element_to_be_clickable(self.active_gateways_card_icon)).click()

    def is_unique_users_popup_open(self, timeout=10):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.unique_users_popup_heading)
            ).is_displayed()
        except TimeoutException:
            return False

    @allure.step("Search Unique Users for '{query}'")
    def search_unique_users(self, query):
        field = self.wait.until(
            EC.element_to_be_clickable(self.unique_users_search_input)
        )
        field.clear()
        field.send_keys(query)

    def get_unique_users_result_texts(self, timeout=10):
        try:
            rows = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_all_elements_located(self.unique_users_result_rows)
            )
            return [r.text.strip() for r in rows if r.text.strip()]
        except TimeoutException:
            return []

    @allure.step("Close the Unique Users popup")
    def close_unique_users_popup(self):
        self.wait.until(
            EC.element_to_be_clickable(self.unique_users_popup_close_button)
        ).click()

    def is_active_gateways_popup_open(self, timeout=10):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.active_gateways_popup_heading)
            ).is_displayed()
        except TimeoutException:
            return False

    def is_active_gateways_empty_message_shown(self, timeout=10):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.active_gateways_empty_message)
            ).is_displayed()
        except TimeoutException:
            return False

    @allure.step("Close the Active Gateways popup")
    def close_active_gateways_popup(self):
        self.wait.until(
            EC.element_to_be_clickable(self.active_gateways_popup_close_button)
        ).click()

    @allure.step("Open the date & time filter")
    def open_date_time_filter(self):
        self.wait.until(
            EC.element_to_be_clickable(self.date_time_filter_button)
        ).click()

    @allure.step("Set date range {start} to {end}")
    def set_date_range(self, start, end):
        """start/end are 'YYYY-MM-DD' strings. These are React-controlled
        inputs — assigning .value directly and firing a plain Event
        doesn't register with React's own change tracking (confirmed: the
        raw input visually updated but the graphs never re-rendered), so
        this goes through the native input value setter instead, the
        standard workaround for driving React-controlled inputs directly.
        """
        set_react_value = """
            const input = arguments[0];
            const value = arguments[1];
            const nativeSetter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value'
            ).set;
            nativeSetter.call(input, value);
            input.dispatchEvent(new Event('input', {bubbles: true}));
            input.dispatchEvent(new Event('change', {bubbles: true}));
        """
        start_field = self.wait.until(EC.presence_of_element_located(self.date_filter_start_input))
        end_field = self.wait.until(EC.presence_of_element_located(self.date_filter_end_input))
        self.driver.execute_script(set_react_value, start_field, start)
        self.driver.execute_script(set_react_value, end_field, end)

    @allure.step("Apply the date filter")
    def click_apply_date_filter(self):
        self.wait.until(
            EC.element_to_be_clickable(self.date_filter_apply_button)
        ).click()

    @allure.step("Clear the date filter")
    def click_clear_date_filter(self):
        self.wait.until(
            EC.element_to_be_clickable(self.date_filter_clear_button)
        ).click()

    def get_session_performance_count(self, timeout=10):
        return self.get_card_count(self.session_performance_count, timeout)

    def get_credit_usage_amount_text(self, timeout=10):
        return WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located(self.credit_usage_amount)
        ).text.strip()

    @allure.step("Click 'View All' in Agents & Activity")
    def click_agents_activity_view_all(self):
        self.wait.until(
            EC.element_to_be_clickable(self.agents_activity_view_all_link)
        ).click()
