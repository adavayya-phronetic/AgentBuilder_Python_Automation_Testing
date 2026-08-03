import time

import allure
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException


class MyAgentsPage:
    """Page object for the My Agents listing/creation page (/agents): the
    'Describe the agent you want to build' prompt box (character count,
    templates, Enter/Shift+Enter), the All/Private/Published filter tabs,
    the status dropdown, search, and the agent card grid (hover reveal,
    click-through, Edit/Share)."""

    def __init__(self, driver):
        self.driver = driver
        # A blanket 120s default here once meant verify_agent_card()'s
        # backend-indexing-lag retry loop could burn several minutes per
        # attempt waiting for a card that genuinely isn't there yet, rather
        # than failing that specific check quickly and moving on.
        self.wait = WebDriverWait(driver, 30)

        self.my_agents_menu = (
            By.XPATH,
            "//a[@href='/agents' and normalize-space()='My Agents']"
        )

        self.leave_page_button = (
            By.XPATH,
            "//button[normalize-space()='Leave Page']"
        )

        self.page_heading = (
            By.XPATH,
            "//h1[normalize-space()='Describe the agent you want to build']"
        )

        self.description_textarea = (
            By.TAG_NAME,
            "textarea"
        )

        # The counter div wraps only the sparkle icon + "N / 5000 characters"
        # text; excluding ancestors with a button descendant keeps this from
        # also matching the outer row that also contains the Create Agent button.
        self.character_counter = (
            By.XPATH,
            "//div[contains(., '/ 5000 characters') and not(.//button)]"
        )

        self.create_agent_button = (
            By.XPATH,
            "//button[normalize-space()='Create Agent']"
        )

        self.shift_enter_hint = (
            By.XPATH,
            "//button[normalize-space()='Shift + Return to add a new line']"
        )

        self.template_scroll_container = (
            By.XPATH,
            "//div[contains(@class,'md:max-w-[80%]')]"
            "//div[contains(@class,'overflow-x-auto') and contains(@class,'scroll-smooth')]"
        )

        # The two round arrow buttons flanking the template chip row; index 0
        # is the left (previous) arrow, -1 is the right (next) arrow.
        self.template_arrow_buttons = (
            By.XPATH,
            "//div[contains(@class,'md:max-w-[80%]')]"
            "//button[contains(@class,'rounded-full') and contains(@class,'p-2')]"
        )

        self.filter_tab_all = (By.XPATH, "//button[@role='tab' and normalize-space()='All']")
        self.filter_tab_private = (By.XPATH, "//button[@role='tab' and normalize-space()='Private']")
        self.filter_tab_published = (By.XPATH, "//button[@role='tab' and normalize-space()='Published']")

        self.status_combobox = (
            By.XPATH,
            "//button[@role='combobox']"
        )

        self.status_options = (
            By.XPATH,
            "//div[@role='option']"
        )

        # Matches both a native <input type="search"> and the app's actual
        # placeholder-based search box, so this keeps working regardless of
        # which markup a given view uses.
        self.search_input = (
            By.XPATH,
            "//input[@type='search' or contains(@placeholder,'Search')]"
        )

        self.agent_card_title = (
            By.XPATH,
            "//h3"
        )

        self.no_results_heading = (
            By.XPATH,
            "//*[normalize-space()='No agents found']"
        )

        self.share_dialog = (
            By.XPATH,
            "//div[@role='dialog']"
        )

        self.share_dialog_close = (
            By.XPATH,
            "//div[@role='dialog']//button[normalize-space()='Close']"
        )

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    @allure.step("Navigate to My Agents")
    def navigate_to_my_agents(self):
        self.wait.until(
            EC.element_to_be_clickable(self.my_agents_menu)
        ).click()
        # Navigating away from an agent build/edit page can trigger a
        # "Leave Page?" dialog if there are unsaved changes.
        try:
            WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(self.leave_page_button)
            ).click()
        except TimeoutException:
            pass
        self.wait.until(EC.url_contains("/agents"))

    def click_my_agents(self):
        """Alias for navigate_to_my_agents() — kept for callers written
        against the older MyAgentsPage API."""
        self.navigate_to_my_agents()

    def is_page_loaded(self):
        """True when the core My Agents UI (heading, description box, Create
        Agent button, filter tabs, status dropdown, search box) is present."""
        checks = [
            self.page_heading,
            self.description_textarea,
            self.create_agent_button,
            self.filter_tab_all,
            self.filter_tab_private,
            self.filter_tab_published,
            self.status_combobox,
            self.search_input,
        ]
        return all(self.driver.find_elements(*locator) for locator in checks)

    # ------------------------------------------------------------------
    # Description box / Create Agent button
    # ------------------------------------------------------------------

    def is_description_box_visible(self):
        return self.wait.until(
            EC.visibility_of_element_located(self.description_textarea)
        ).is_displayed()

    def is_create_button_visible(self):
        return self.wait.until(
            EC.visibility_of_element_located(self.create_agent_button)
        ).is_displayed()

    def is_create_button_disabled(self):
        button = self.driver.find_element(*self.create_agent_button)
        return button.get_attribute("disabled") is not None

    @allure.step("Enter agent description '{text}'")
    def enter_description(self, text):
        field = self.wait.until(
            EC.visibility_of_element_located(self.description_textarea)
        )
        field.send_keys(Keys.CONTROL, "a")
        field.send_keys(Keys.DELETE)
        if text:
            field.send_keys(text)
        return field

    @allure.step("Enter agent creation prompt")
    def enter_prompt(self, prompt):
        """Alias for enter_description() — kept for callers written against
        the older MyAgentsPage API. Clearing first is harmless on the
        always-empty box this was originally used against."""
        return self.enter_description(prompt)

    def set_description_via_js(self, text):
        """Sets the textarea value directly through the native setter and fires
        a real 'input' event, bypassing send_keys — used for very long strings
        (thousands of characters) where per-keystroke typing would be slow and
        isn't needed to exercise the app's own change handling."""
        field = self.wait.until(
            EC.visibility_of_element_located(self.description_textarea)
        )
        self.driver.execute_script(
            """
            const el = arguments[0]; const val = arguments[1];
            const nativeSetter = Object.getOwnPropertyDescriptor(
                window.HTMLTextAreaElement.prototype, 'value'
            ).set;
            nativeSetter.call(el, val);
            el.dispatchEvent(new Event('input', { bubbles: true }));
            """,
            field, text
        )
        return field

    def get_description_value(self):
        field = self.driver.find_element(*self.description_textarea)
        return self.driver.execute_script("return arguments[0].value;", field)

    def get_character_count_text(self):
        return self.driver.find_element(*self.character_counter).text.strip()

    def get_character_count(self):
        """Parses the leading number out of 'N / 5000 characters'."""
        text = self.get_character_count_text()
        return int(text.split("/")[0].strip())

    @allure.step("Add a new line via Shift+Enter")
    def send_shift_enter(self):
        field = self.driver.find_element(*self.description_textarea)
        field.send_keys(Keys.SHIFT, Keys.ENTER)

    @allure.step("Press Enter in the description box")
    def press_enter(self):
        field = self.driver.find_element(*self.description_textarea)
        field.send_keys(Keys.ENTER)

    @allure.step("Click 'Create Agent'")
    def click_create_agent(self):
        self.wait.until(
            EC.element_to_be_clickable(self.create_agent_button)
        ).click()

    # ------------------------------------------------------------------
    # Templates carousel
    # ------------------------------------------------------------------

    @allure.step("Click template '{template_name}'")
    def click_template(self, template_name):
        locator = (By.XPATH, f"//div[normalize-space()='{template_name}']/ancestor::button[1]")
        self.wait.until(EC.element_to_be_clickable(locator)).click()

    def get_template_scroll_left(self):
        # The carousel scrolls with a CSS 'scroll-smooth' transition, so the
        # container element itself can be swapped/re-rendered by React right
        # after a click — retry once on a stale reference rather than fail.
        for _ in range(3):
            try:
                container = self.driver.find_element(*self.template_scroll_container)
                return self.driver.execute_script("return arguments[0].scrollLeft;", container)
            except StaleElementReferenceException:
                continue
        raise StaleElementReferenceException("Template scroll container stayed stale after retries")

    def _wait_for_scroll_to_settle(self, timeout=3, poll=0.2):
        # 'scroll-smooth' animates the scrollLeft change over time, so a value
        # read immediately after the click is a mid-animation snapshot, not
        # the arrow's actual destination — wait until it stops moving.
        last = self.get_template_scroll_left()
        end_time = time.monotonic() + timeout
        while time.monotonic() < end_time:
            time.sleep(poll)
            current = self.get_template_scroll_left()
            if current == last:
                return current
            last = current
        return last

    @allure.step("Click template carousel right arrow")
    def click_template_right_arrow(self):
        for _ in range(3):
            try:
                buttons = self.driver.find_elements(*self.template_arrow_buttons)
                buttons[-1].click()
                self._wait_for_scroll_to_settle()
                return
            except StaleElementReferenceException:
                continue

    @allure.step("Click template carousel left arrow")
    def click_template_left_arrow(self):
        for _ in range(3):
            try:
                buttons = self.driver.find_elements(*self.template_arrow_buttons)
                buttons[0].click()
                self._wait_for_scroll_to_settle()
                return
            except StaleElementReferenceException:
                continue

    # ------------------------------------------------------------------
    # Filter tabs / status dropdown
    # ------------------------------------------------------------------

    @allure.step("Click '{tab_name}' filter tab")
    def click_filter_tab(self, tab_name):
        locator = (By.XPATH, f"//button[@role='tab' and normalize-space()='{tab_name}']")
        self.wait.until(EC.element_to_be_clickable(locator)).click()

    def is_filter_tab_selected(self, tab_name):
        locator = (By.XPATH, f"//button[@role='tab' and normalize-space()='{tab_name}']")
        return self.driver.find_element(*locator).get_attribute("aria-selected") == "true"

    @allure.step("Open status dropdown")
    def open_status_dropdown(self):
        self.wait.until(
            EC.element_to_be_clickable(self.status_combobox)
        ).click()

    def get_status_dropdown_options(self):
        self.open_status_dropdown()
        options = self.wait.until(
            EC.presence_of_all_elements_located(self.status_options)
        )
        names = [o.text.strip() for o in options if o.text.strip()]
        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
        return names

    @allure.step("Select status filter '{status_name}'")
    def select_status_filter(self, status_name):
        self.open_status_dropdown()
        option_locator = (By.XPATH, f"//div[@role='option' and normalize-space()='{status_name}']")
        self.wait.until(EC.element_to_be_clickable(option_locator)).click()

    def set_status_filter_all(self):
        """Alias for select_status_filter('All') — kept for callers written
        against the older MyAgentsPage API."""
        self.select_status_filter("All")

    def set_status_filter_active(self):
        """Alias for select_status_filter('Active') — kept for callers
        written against the older MyAgentsPage API."""
        self.select_status_filter("Active")

    # ------------------------------------------------------------------
    # Search / card grid
    # ------------------------------------------------------------------

    @allure.step("Search for agent '{text}'")
    def search_agent(self, text):
        search_box = self.wait.until(
            EC.visibility_of_element_located(self.search_input)
        )
        search_box.send_keys(Keys.CONTROL, "a")
        search_box.send_keys(Keys.DELETE)
        if text:
            search_box.send_keys(text)

    def get_card_names(self, timeout=10):
        # A search/filter change debounces then re-renders the card grid, so
        # the elements located here can go stale between being found and
        # having .text read off them — retry a couple of times rather than
        # let that one-off race fail the whole call.
        for _ in range(3):
            try:
                cards = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_all_elements_located(self.agent_card_title)
                )
                return [c.text.strip() for c in cards if c.text.strip()]
            except TimeoutException:
                return []
            except StaleElementReferenceException:
                continue
        return []

    def get_visible_card_names(self, timeout=10):
        """Same as get_card_names(), but also scrolls the first result (or
        the 'No agents found' message) into view — used right after a
        search/filter change so a screenshot taken immediately after doesn't
        show an empty-looking page with just the creation prompt box."""
        names = self.get_card_names(timeout=timeout)
        self.scroll_cards_into_view()
        return names

    @allure.step("Get active agent names")
    def get_active_agent_names(self):
        """Switches the status filter to 'Active' and returns the resulting
        card names."""
        self.set_status_filter_active()
        return self.get_card_names()

    def is_no_results_message_displayed(self):
        try:
            return WebDriverWait(self.driver, 5).until(
                EC.visibility_of_element_located(self.no_results_heading)
            ).is_displayed()
        except TimeoutException:
            return False

    def scroll_cards_into_view(self):
        """Scrolls the first agent card into view, or the 'No agents found'
        message if there are none (e.g. the Published tab on an account with
        no published agents — a legitimate empty result, not a failure). The
        results area sits below the fold on the My Agents page, so a
        screenshot taken right after get_card_names() — without this —
        shows the creation prompt box and an empty-looking page instead of
        whatever the test actually asserted on."""
        cards = self.driver.find_elements(*self.agent_card_title)
        if cards:
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", cards[0])
        else:
            self.scroll_no_results_message_into_view()

    def scroll_no_results_message_into_view(self):
        try:
            heading = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(self.no_results_heading)
            )
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", heading)
        except TimeoutException:
            pass

    @staticmethod
    def _case_insensitive_card_locator(agent_name):
        # Card titles render with CSS `capitalize`, which Selenium's .text
        # reflects (the rendered text), so an exact-case XPath match against
        # a name read back from `.text` can miss on mixed-case source names.
        return (
            By.XPATH,
            "//h3[translate(normalize-space(.), "
            "'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')="
            f"'{agent_name.lower()}']"
        )

    def _get_card_container(self, agent_name, timeout=10):
        card_locator = self._case_insensitive_card_locator(agent_name)
        card_title = WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(card_locator)
        )
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", card_title)
        return card_title.find_element(By.XPATH, "./ancestor::div[contains(@class,'cursor-pointer')][1]")

    @allure.step("Click agent card '{agent_name}'")
    def click_card(self, agent_name):
        for _ in range(3):
            try:
                card = self._get_card_container(agent_name)
                self.driver.execute_script("arguments[0].click();", card)
                return
            except StaleElementReferenceException:
                continue

    def click_agent_card(self, agent_name):
        """Alias for click_card() — kept for callers written against the
        older MyAgentsPage API."""
        self.click_card(agent_name)

    @allure.step("Hover over agent card '{agent_name}'")
    def hover_over_card(self, agent_name):
        card = self._get_card_container(agent_name)
        ActionChains(self.driver).move_to_element(card).perform()

    def move_mouse_away_from_cards(self):
        self.driver.execute_script("window.scrollTo(0,0);")
        ActionChains(self.driver).move_to_element(
            self.driver.find_element(By.TAG_NAME, "body")
        ).move_by_offset(0, 0).perform()

    def _get_action_wrapper_opacity(self, agent_name, span_text):
        card = self._get_card_container(agent_name)
        span = card.find_element(By.XPATH, f".//span[normalize-space()='{span_text}']")
        wrapper = span.find_element(By.XPATH, "./ancestor::div[contains(@class,'opacity-0')][1]")
        return float(self.driver.execute_script("return getComputedStyle(arguments[0]).opacity;", wrapper))

    def get_edit_share_opacity(self, agent_name):
        """Returns the computed opacity of the card's Edit/Share button wrapper
        (0 = hidden, 1 = fully visible) — these are CSS opacity-on-hover
        controlled, not display:none, so is_displayed() alone can't tell
        hidden-by-default apart from hovered-and-visible."""
        return self._get_action_wrapper_opacity(agent_name, "EDIT")

    @allure.step("Click Edit on agent card '{agent_name}'")
    def click_card_edit(self, agent_name):
        card = self._get_card_container(agent_name)
        edit_btn = card.find_element(By.XPATH, ".//span[normalize-space()='EDIT']/ancestor::button[1]")
        self.driver.execute_script("arguments[0].click();", edit_btn)

    @allure.step("Click Share on agent card '{agent_name}'")
    def click_card_share(self, agent_name):
        card = self._get_card_container(agent_name)
        share_btn = card.find_element(By.XPATH, ".//span[normalize-space()='SHARE']/ancestor::button[1]")
        self.driver.execute_script("arguments[0].click();", share_btn)

    def get_share_dialog_text(self, timeout=10):
        dialog = WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located(self.share_dialog)
        )
        # The dialog's own CSS (opacity, transform, background-color) all
        # already read as fully settled the instant it mounts — verified live,
        # computed opacity is "1" from t=0 — yet a screenshot taken right here
        # still shows a translucent, ghosted dialog bleeding into the page
        # behind it for roughly the first ~300-400ms. That's a paint/compositor
        # lag independent of any CSS value, so no property-polling loop can
        # detect it; a short fixed wait is the only thing that reliably closes
        # the gap (confirmed live: 500ms was already enough, 1s for margin).
        time.sleep(1)
        return dialog.text

    @allure.step("Close Share dialog")
    def close_share_dialog(self):
        self.wait.until(
            EC.element_to_be_clickable(self.share_dialog_close)
        ).click()
        try:
            WebDriverWait(self.driver, 5).until(
                EC.invisibility_of_element_located(self.share_dialog)
            )
        except TimeoutException:
            pass
        # Same paint/compositor lag as the open transition (see
        # get_share_dialog_text) applies in reverse here: the dialog can
        # still be mid fade-out when conftest's end-of-test teardown
        # screenshot fires immediately after this call returns, showing a
        # ghosted dialog over the page even though it's already gone from
        # the DOM/CSS state.
        time.sleep(1)

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

            self.navigate_to_my_agents()
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
