import allure
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    TimeoutException,
)


class AnalyticsPage:
    """Page object for an agent's Analytics tab (/analytics/<agent_id>) —
    reached from the Build page's own sub-sidebar (Build / Gateway /
    Analytics / Sessions / Datasets / Eval Dashboard), not the main app
    shell's nav. Covers the period/date-range filters and the six metric
    cards (Latency, Task Completion, Engagement Time, Security Risks,
    CSAT Score, Cost)."""

    # The six metric card labels, in the order they render on the page.
    METRIC_LABELS = (
        "Latency", "Task Completion", "Engagement Time",
        "Security Risks", "CSAT Score", "Cost",
    )

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)

        # This sub-sidebar link only exists on an agent's Build page (and
        # its sibling tabs) — same shape as the "Back"/"Analytics" links
        # elsewhere in this suite that are shared between <a> and <button>
        # depending on which shell renders them.
        self.analytics_nav_link = (
            By.XPATH,
            "//*[self::a or self::button][normalize-space()='Analytics']"
        )

        self.page_heading = (
            By.XPATH,
            "//h1[normalize-space()='Analytics']"
        )

        self.page_subtitle = (
            By.XPATH,
            "//p[normalize-space()="
            "'Monitor agent performance, usage trends, and conversation metrics over time.']"
        )

        self.refresh_button = (
            By.XPATH,
            "//button[@aria-label='Refresh analytics']"
        )

        # Radix Select trigger for the Today/Yesterday/Last 7 Days/Last 30
        # Days preset — no stable id of its own, but it's the only
        # role='combobox' element on this page.
        self.period_dropdown_button = (
            By.XPATH,
            "//button[@role='combobox']"
        )

        self.period_option_xpath = (
            "//div[@role='option']//span[normalize-space()='{period}']"
        )

        # The "Pick a date" custom-range trigger carries a plain, stable
        # id="date" — confirmed live, the same id the Dashboard page's own
        # date/time filter trigger uses (see DashboardPage.date_time_filter_button).
        # Its visible text flips from 'Pick a date' to the picked range
        # (e.g. 'Aug 03, 2026 - Aug 06, 2026') once a range is applied, so
        # the id is used rather than any text match.
        self.date_range_button = (By.ID, "date")

        # react-day-picker calendar (opens as a Radix popover). Day cells
        # are <button name="day">; cells belonging to the adjacent
        # month (padding at the start/end of the grid) carry an extra
        # 'day-outside' class and are excluded so a day number is never
        # ambiguous between two visible months.
        self.calendar_day_button_xpath = (
            "//button[@name='day' and not(contains(@class,'day-outside')) "
            "and normalize-space()='{day}']"
        )

        self.calendar_previous_month_button = (By.XPATH, "//button[@name='previous-month']")
        self.calendar_next_month_button = (By.XPATH, "//button[@name='next-month']")

        self.calendar_apply_button = (By.XPATH, "//button[normalize-space()='Apply']")
        self.calendar_clear_button = (By.XPATH, "//button[normalize-space()='Clear']")

        # react-day-picker stamps each visible month's caption with an id
        # starting 'react-day-picker-' (e.g. 'react-day-picker-1'); the
        # calendar shows two months side by side, so this can match more
        # than one element — the first is always the earlier/current month.
        self.calendar_month_labels = (
            By.XPATH,
            "//*[starts-with(@id,'react-day-picker')]"
        )

        # The calendar icon inside the "Pick a date" button — confirmed
        # live it renders with CSS pointer-events:none (the button's own
        # '[&_svg]:pointer-events-none' rule), so a plain WebDriver .click()
        # on it always raises ElementClickInterceptedException (it reports
        # the underlying button as the real click target). A real mouse
        # click at the icon's on-screen position still opens the popover
        # though, since the browser's own hit-testing sees straight through
        # a pointer-events:none element to whatever sits beneath it — so
        # this is driven via ActionChains (low-level input events) rather
        # than the WebDriver click command (see click_date_range_calendar_icon).
        self.date_range_calendar_icon = (
            By.XPATH,
            "//button[@id='date']//*[local-name()='svg']"
        )

        # Every metric card shares the same rounded/shadow container; scope
        # from its own h2 title up to that container rather than assuming a
        # fixed position, since the same template drives all six cards.
        self._card_container_xpath = (
            "//h2[normalize-space()='{label}']"
            "/ancestor::div[contains(@class,'rounded-xl') and contains(@class,'shadow-md')][1]"
        )

        self._card_value_xpath = (
            self._card_container_xpath +
            "//div[contains(@class,'text-2xl') and contains(@class,'font-semibold')]"
        )

        # Only Latency and Engagement Time currently render a trend chip
        # (green/red, trending-up/down icon + percentage); Task Completion
        # has a bare value with no trend at all.
        self._card_trend_xpath = (
            self._card_container_xpath +
            "//div[contains(@class,'text-green-500') or contains(@class,'text-red-500')]/span"
        )

        # Security Risks / CSAT Score / Cost render an empty-state card
        # instead of a chart+value while their backing data isn't wired up
        # yet — confirmed live across every agent checked.
        self._card_warming_up_xpath = (
            self._card_container_xpath +
            "//*[normalize-space()='This Section is Warming Up']"
        )

        # Every populated card (Latency, Task Completion, Engagement Time)
        # renders its graph into a <canvas> — Chart.js draws entirely in
        # pixels with no chart-type-specific DOM markup, so a donut vs. a
        # line chart can't be told apart from markup alone; this only
        # confirms the chart area itself rendered.
        self._card_canvas_xpath = self._card_container_xpath + "//canvas"

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    @allure.step("Navigate to the Analytics tab")
    def click_analytics_nav(self):
        # Right after an agent card click, the Build page's own sidebar can
        # still be mid-mount — a click that lands on the "Analytics" link at
        # exactly that moment can fire on a node React is about to replace,
        # so the click silently does nothing and the URL never changes.
        # Retrying the whole locate+click a few times rides out that race
        # instead of failing on one unlucky attempt.
        last_error = None
        for _ in range(3):
            try:
                self.wait.until(
                    EC.element_to_be_clickable(self.analytics_nav_link)
                ).click()
                WebDriverWait(self.driver, 10).until(EC.url_contains("/analytics/"))
                self.is_analytics_page_loaded()
                return
            except TimeoutException as e:
                last_error = e
        raise last_error

    def is_analytics_page_loaded(self, timeout=20):
        """Confirms the heading, subtitle and the first (always-populated)
        metric card all rendered — the clearest signal Analytics (not just
        the URL) actually loaded."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.page_heading)
            )
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.page_subtitle)
            )
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(
                    (By.XPATH, self._card_value_xpath.format(label="Latency"))
                )
            )
            return True
        except TimeoutException:
            return False

    @allure.step("Click 'Refresh' on Analytics")
    def click_refresh(self):
        self.wait.until(
            EC.element_to_be_clickable(self.refresh_button)
        ).click()

    def get_card_labels(self, timeout=10):
        """Returns every metric card's h2 title currently on the page."""
        elements = WebDriverWait(self.driver, timeout).until(
            EC.presence_of_all_elements_located((By.XPATH, "//h2"))
        )
        return [e.text.strip() for e in elements if e.text.strip() in self.METRIC_LABELS]

    # ------------------------------------------------------------------
    # Period preset dropdown (Today / Yesterday / Last 7 Days / Last 30 Days)
    # ------------------------------------------------------------------

    @allure.step("Open the period dropdown")
    def open_period_dropdown(self):
        self.wait.until(
            EC.element_to_be_clickable(self.period_dropdown_button)
        ).click()

    @allure.step("Select period '{period}'")
    def select_period(self, period):
        self.open_period_dropdown()
        option_locator = (By.XPATH, self.period_option_xpath.format(period=period))
        self.wait.until(
            EC.element_to_be_clickable(option_locator)
        ).click()

    def get_selected_period_label(self, timeout=10):
        return WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located(self.period_dropdown_button)
        ).text.strip()

    # ------------------------------------------------------------------
    # Custom date-range picker
    # ------------------------------------------------------------------

    @allure.step("Open the date range picker")
    def open_date_range_picker(self):
        self.wait.until(
            EC.element_to_be_clickable(self.date_range_button)
        ).click()

    @allure.step("Click the calendar icon beside 'Pick a date'")
    def click_date_range_calendar_icon(self):
        icon = self.wait.until(
            EC.presence_of_element_located(self.date_range_calendar_icon)
        )
        ActionChains(self.driver).move_to_element(icon).click().perform()

    def get_visible_calendar_month_labels(self, timeout=10):
        """Returns the caption text of every month currently shown in the
        popover (e.g. ['August 2026', 'September 2026']) — the calendar
        renders two months side by side, in order, so index 0 is always the
        current/earlier one."""
        elements = WebDriverWait(self.driver, timeout).until(
            EC.presence_of_all_elements_located(self.calendar_month_labels)
        )
        return [e.text.strip() for e in elements if e.text.strip()]

    @allure.step("Go to previous month in the date picker")
    def click_previous_month(self):
        self.wait.until(
            EC.element_to_be_clickable(self.calendar_previous_month_button)
        ).click()

    @allure.step("Go to next month in the date picker")
    def click_next_month(self):
        self.wait.until(
            EC.element_to_be_clickable(self.calendar_next_month_button)
        ).click()

    @allure.step("Select day '{day}' in the date picker")
    def click_calendar_day(self, day):
        """Clicks a day-of-month cell (e.g. '5') in whichever month is
        currently visible. Callers picking a start/end pair within the same
        visible month can call this twice in a row — the calendar stays
        open between clicks until Apply/Clear is pressed."""
        locator = (By.XPATH, self.calendar_day_button_xpath.format(day=day))
        self.wait.until(
            EC.element_to_be_clickable(locator)
        ).click()

    @allure.step("Select date range from '{start_day}' to '{end_day}' in the current month")
    def select_date_range_in_current_month(self, start_day, end_day):
        self.open_date_range_picker()
        self.click_calendar_day(start_day)
        self.click_calendar_day(end_day)

    @allure.step("Select a single valid date '{day}' in the current month")
    def select_single_date_in_current_month(self, day):
        """Selects one specific day as both the start and end of the range.

        This calendar is a range picker: clicking a day once only sets a
        live preview (the trigger button's text updates immediately, before
        anything is actually applied) and leaves Apply disabled — confirmed
        live, a single click alone never enables it. Clicking the *same*
        day again completes a valid (zero-length) range and enables Apply,
        which is the only way to land on one specific applied date; the
        result reads as a same-day range (e.g. 'Aug 11, 2026 - Aug 11,
        2026') rather than a bare single date.
        """
        self.open_date_range_picker()
        self.click_calendar_day(day)
        self.click_calendar_day(day)

    def get_future_month_day_buttons(self, timeout=10):
        """Navigates the calendar one month forward (guaranteed to be
        entirely in the future relative to today, whatever today's date
        is) and returns every real (non-'day-outside') day button there —
        used to verify future dates are disabled without depending on
        which day of the current month the suite happens to run on."""
        self.click_next_month()
        locator = (
            By.XPATH,
            "//button[@name='day' and not(contains(@class,'day-outside'))]"
        )
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_all_elements_located(locator)
        )

    @staticmethod
    def is_day_button_disabled(day_button):
        return day_button.get_attribute("disabled") is not None

    def try_click_day_button(self, day_button):
        """Attempts a real click on a day cell WebElement and reports
        whether it was actually blocked. A disabled day-picker cell carries
        pointer-events:none, so WebDriver's own click command reports the
        click as intercepted by whatever sits beneath it rather than ever
        registering on the cell — that's the observable signal a disabled
        day can't be selected, since get_attribute('disabled') alone
        doesn't prove the UI actually rejects a real click.

        Returns True if the click was blocked (disabled), False if it went
        through normally.
        """
        try:
            day_button.click()
            return False
        except (ElementClickInterceptedException, ElementNotInteractableException):
            return True

    @allure.step("Apply the date range")
    def click_apply_date_range(self):
        self.wait.until(
            EC.element_to_be_clickable(self.calendar_apply_button)
        ).click()

    @allure.step("Clear the date range")
    def click_clear_date_range(self):
        self.open_date_range_picker()
        self.wait.until(
            EC.element_to_be_clickable(self.calendar_clear_button)
        ).click()

    def get_date_range_button_text(self, timeout=10):
        return WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located(self.date_range_button)
        ).text.strip()

    def is_calendar_open(self, timeout=5):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.calendar_apply_button)
            ).is_displayed()
        except TimeoutException:
            return False

    # ------------------------------------------------------------------
    # Metric cards
    # ------------------------------------------------------------------

    def get_metric_value(self, label, timeout=10):
        locator = (By.XPATH, self._card_value_xpath.format(label=label))
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(locator)
            ).text.strip()
        except TimeoutException:
            return ""

    def get_metric_trend(self, label, timeout=5):
        """Returns the trend percentage text (e.g. '0.00%') shown next to a
        metric's value, or '' for cards that don't render a trend chip
        (Task Completion) or are still in the warming-up empty state."""
        locator = (By.XPATH, self._card_trend_xpath.format(label=label))
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(locator)
            ).text.strip()
        except TimeoutException:
            return ""

    def is_metric_warming_up(self, label, timeout=5):
        locator = (By.XPATH, self._card_warming_up_xpath.format(label=label))
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(locator)
            ).is_displayed()
        except TimeoutException:
            return False

    def is_metric_chart_displayed(self, label, timeout=10):
        locator = (By.XPATH, self._card_canvas_xpath.format(label=label))
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(locator)
            ).is_displayed()
        except TimeoutException:
            return False
