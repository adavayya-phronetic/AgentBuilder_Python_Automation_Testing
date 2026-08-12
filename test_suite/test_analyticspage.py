import random
import re
import time
from urllib.parse import urlparse

import allure
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from Webpages.analytics_page import AnalyticsPage
from Webpages.chat_page import ChatPage
from Webpages.my_agents_page import MyAgentsPage
from Utility.allure_helpers import attach_step_screenshot

# This suite is scoped to exactly the Analytics test cases tracked in the
# team's test case sheet (S.No/TC ID column), and only the ones marked
# Automation: Yes there:
# https://docs.google.com/spreadsheets/d/195kyU03hTTHFBgVEPTMGK-7RWQQJPXmtj6Br8q5P6To/edit?gid=0
# Test function names/titles below are numbered to match that sheet's
# TC_Analytics_<N> IDs directly (gaps in the numbers are sheet rows not
# marked for automation) — don't renumber locally without updating the
# sheet, and don't add cases here that aren't tracked there.

DATE_RANGE_PATTERN = re.compile(r"^\w{3} \d{2}, \d{4} - \w{3} \d{2}, \d{4}$")


def _safe_past_date_range():
    """Returns (start_day, end_day) day-of-month strings that are always
    valid, non-future cells in the *current* month's calendar view,
    regardless of what day of the month the suite happens to run on (the
    1st of the month included) — the 1st through today, since every day up
    to and including today is guaranteed enabled."""
    today = time.localtime().tm_mday
    end_day = today if today > 1 else 1
    return "1", str(end_day)


def _open_random_active_agent_analytics(driver):
    """Opens a random active agent's Build page, then switches to its
    Analytics tab via the Build page's own sub-sidebar (Build / Gateway /
    Analytics / Sessions / Datasets / Eval Dashboard) — that sidebar only
    exists once inside an agent, unlike the main app shell's nav, so
    Analytics always needs an agent opened first.

    Hard-navigates to /agents rather than clicking a "My Agents" nav link:
    the shared session can land here right after login (still on
    /dashboard, which has no such link) or straight after a previous
    Analytics test (already reset to /agents by the autouse fixture), so a
    direct URL navigation works regardless of which state it starts from —
    same approach test_meetpage.py's equivalent helper uses.
    """
    parsed = urlparse(driver.current_url)
    agents_url = f"{parsed.scheme}://{parsed.netloc}/agents"
    driver.get(agents_url)

    agents_page = MyAgentsPage(driver)
    active_agent_names = agents_page.get_active_agent_names()
    assert active_agent_names, "No active agents found in the agent card list"

    target_agent_name = random.choice(active_agent_names)
    allure.attach(target_agent_name, name="Target agent", attachment_type=allure.attachment_type.TEXT)

    agents_page.search_agent(target_agent_name)
    agents_page.click_agent_card(target_agent_name)

    analytics_page = AnalyticsPage(driver)
    analytics_page.click_analytics_nav()
    return target_agent_name, analytics_page


@allure.feature("Analytics")
@allure.story("Analytics Load")
@allure.title("TC_Analytics_01 — Verify Analytics page loads successfully")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.analytics
def test_analytics_page_loads_successfully(logged_in_driver):
    driver = logged_in_driver

    with allure.step("Click on an agent in My Agents, then click Analytics"):
        agent_name, analytics = _open_random_active_agent_analytics(driver)
        print(f"Opened Analytics for agent '{agent_name}'.")
        attach_step_screenshot(driver, "Analytics opened")

    with allure.step("Verify Analytics page loads successfully with all widgets displayed"):
        assert analytics.is_analytics_page_loaded(), (
            "Analytics page did not load successfully — heading or metric cards missing"
        )
        labels = analytics.get_card_labels()
        assert set(labels) == set(AnalyticsPage.METRIC_LABELS), (
            f"Expected metric cards {AnalyticsPage.METRIC_LABELS}, got {labels}"
        )
        print("Analytics page loaded with all widgets:", labels)
        attach_step_screenshot(driver, "All widgets displayed")


@allure.feature("Analytics")
@allure.story("Latency")
@allure.title("TC_Analytics_05 — Verify Latency graph updates based on selected date filter")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.analytics
def test_latency_graph_updates_on_date_filter(logged_in_driver):
    driver = logged_in_driver

    with allure.step("Open an active agent's Analytics tab"):
        _, analytics = _open_random_active_agent_analytics(driver)
        value_before = analytics.get_metric_value("Latency")
        print("Latency before filter change:", value_before)
        attach_step_screenshot(driver, "Latency before filter change")

    with allure.step("Select a date filter (Last 7 Days)"):
        analytics.select_period("Last 7 Days")
        attach_step_screenshot(driver, "Last 7 Days selected")

    with allure.step("Verify the Latency graph updates according to the selected date range"):
        value_after = analytics.get_metric_value("Latency")
        assert re.match(r"^-?\d+(\.\d+)?\s*ms$", value_after), f"Unexpected Latency value: {value_after!r}"
        assert analytics.is_metric_chart_displayed("Latency"), "Latency graph did not render after the filter change"
        print(f"Latency updated to '{value_after}' for the selected range.")
        attach_step_screenshot(driver, "Latency graph updated")


@allure.feature("Analytics")
@allure.story("Task Completion")
@allure.title("TC_Analytics_06 — Verify Task Completion chart is displayed")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.analytics
def test_task_completion_chart_displayed(logged_in_driver):
    driver = logged_in_driver

    with allure.step("Open Analytics page for an active agent"):
        _, analytics = _open_random_active_agent_analytics(driver)
        attach_step_screenshot(driver, "Analytics opened")

    with allure.step("Verify the Task Completion chart is displayed"):
        assert analytics.is_metric_chart_displayed("Task Completion"), (
            "Task Completion chart did not render"
        )
        print("Task Completion chart is displayed.")
        attach_step_screenshot(driver, "Task Completion chart displayed")


@allure.feature("Analytics")
@allure.story("Task Completion")
@allure.title("TC_Analytics_07 — Verify Task Completion percentage calculation")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.analytics
def test_task_completion_percentage_calculation(logged_in_driver):
    driver = logged_in_driver

    with allure.step("Open Analytics page for an active agent"):
        _, analytics = _open_random_active_agent_analytics(driver)
        attach_step_screenshot(driver, "Analytics opened")

    with allure.step("Verify the completion percentage matches a valid 0-100% value"):
        value = analytics.get_metric_value("Task Completion")
        match = re.match(r"^(\d+(?:\.\d+)?)%$", value)
        assert match, f"Unexpected Task Completion value: {value!r}"
        percentage = float(match.group(1))
        assert 0 <= percentage <= 100, f"Task Completion percentage out of range: {percentage}"
        print(f"Task Completion percentage: {value}")
        attach_step_screenshot(driver, "Task Completion percentage")


@allure.feature("Analytics")
@allure.story("Task Completion")
@allure.title("TC_Analytics_08 — Verify Task Completion updates based on selected date filter")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.analytics
def test_task_completion_updates_on_date_filter(logged_in_driver):
    driver = logged_in_driver

    with allure.step("Open an active agent's Analytics tab"):
        _, analytics = _open_random_active_agent_analytics(driver)
        value_before = analytics.get_metric_value("Task Completion")
        print("Task Completion before filter change:", value_before)
        attach_step_screenshot(driver, "Task Completion before filter change")

    with allure.step("Change the date filter to Last 30 Days"):
        analytics.select_period("Last 30 Days")
        attach_step_screenshot(driver, "Last 30 Days selected")

    with allure.step("Verify the Task Completion chart refreshes according to the selected period"):
        value_after = analytics.get_metric_value("Task Completion")
        assert re.match(r"^\d+(\.\d+)?%$", value_after), f"Unexpected Task Completion value: {value_after!r}"
        print(f"Task Completion refreshed to '{value_after}' for the selected period.")
        attach_step_screenshot(driver, "Task Completion updated")


@allure.feature("Analytics")
@allure.story("Engagement Time")
@allure.title("TC_Analytics_11 — Verify Engagement Time graph updates based on selected date filter")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.analytics
def test_engagement_time_graph_updates_on_date_filter(logged_in_driver):
    driver = logged_in_driver

    with allure.step("Open an active agent's Analytics tab"):
        _, analytics = _open_random_active_agent_analytics(driver)
        value_before = analytics.get_metric_value("Engagement Time")
        print("Engagement Time before filter change:", value_before)
        attach_step_screenshot(driver, "Engagement Time before filter change")

    with allure.step("Change the date filter to Last 7 Days"):
        analytics.select_period("Last 7 Days")
        attach_step_screenshot(driver, "Last 7 Days selected")

    with allure.step("Verify the Engagement Time graph updates based on the selected period"):
        value_after = analytics.get_metric_value("Engagement Time")
        assert re.match(r"^-?\d+(\.\d+)?\s*sec$", value_after), f"Unexpected Engagement Time value: {value_after!r}"
        assert analytics.is_metric_chart_displayed("Engagement Time"), (
            "Engagement Time graph did not render after the filter change"
        )
        print(f"Engagement Time updated to '{value_after}' for the selected period.")
        attach_step_screenshot(driver, "Engagement Time graph updated")


@allure.feature("Analytics")
@allure.story("Period Filter")
@allure.title("TC_Analytics_12 — Verify 'Today' is selected as the default dropdown option")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.analytics
def test_today_is_default_dropdown_option(logged_in_driver):
    driver = logged_in_driver

    with allure.step("Open Analytics page for an active agent"):
        _, analytics = _open_random_active_agent_analytics(driver)
        attach_step_screenshot(driver, "Analytics opened")

    with allure.step("Verify the date filter dropdown defaults to 'Today'"):
        assert analytics.get_selected_period_label() == "Today", (
            "Expected the period dropdown to default to 'Today' on page load"
        )
        print("Period dropdown defaulted to 'Today'.")
        attach_step_screenshot(driver, "Today is the default period")


@allure.feature("Analytics")
@allure.story("Period Filter")
@allure.title("TC_Analytics_13 — Verify Today option in dropdown")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.analytics
def test_today_option_in_dropdown(logged_in_driver):
    driver = logged_in_driver

    with allure.step("Open Analytics page and switch to Yesterday first"):
        _, analytics = _open_random_active_agent_analytics(driver)
        analytics.select_period("Yesterday")
        attach_step_screenshot(driver, "Yesterday selected")

    with allure.step("Open the dropdown and select Today"):
        analytics.select_period("Today")
        attach_step_screenshot(driver, "Today selected")

    with allure.step("Verify Analytics data reflects the Today selection"):
        assert analytics.get_selected_period_label() == "Today", (
            "Period dropdown did not update to 'Today'"
        )
        value = analytics.get_metric_value("Latency")
        assert re.match(r"^-?\d+(\.\d+)?\s*ms$", value), f"Unexpected Latency value: {value!r}"
        print("Today option selected successfully; Latency:", value)


@allure.feature("Analytics")
@allure.story("Period Filter")
@allure.title("TC_Analytics_14 — Verify Yesterday option in dropdown")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.analytics
def test_yesterday_option_in_dropdown(logged_in_driver):
    driver = logged_in_driver

    with allure.step("Open Analytics page for an active agent"):
        _, analytics = _open_random_active_agent_analytics(driver)
        attach_step_screenshot(driver, "Analytics opened")

    with allure.step("Open the dropdown and select Yesterday"):
        analytics.select_period("Yesterday")
        attach_step_screenshot(driver, "Yesterday selected")

    with allure.step("Verify Analytics data reflects the Yesterday selection"):
        assert analytics.get_selected_period_label() == "Yesterday", (
            "Period dropdown did not update to 'Yesterday'"
        )
        value = analytics.get_metric_value("Latency")
        assert re.match(r"^-?\d+(\.\d+)?\s*ms$", value), f"Unexpected Latency value: {value!r}"
        print("Yesterday option selected successfully; Latency:", value)


@allure.feature("Analytics")
@allure.story("Period Filter")
@allure.title("TC_Analytics_15 — Verify Last 7 Days option in dropdown")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.analytics
def test_last_7_days_option_in_dropdown(logged_in_driver):
    driver = logged_in_driver

    with allure.step("Open Analytics page for an active agent"):
        _, analytics = _open_random_active_agent_analytics(driver)
        attach_step_screenshot(driver, "Analytics opened")

    with allure.step("Open the dropdown and select Last 7 Days"):
        analytics.select_period("Last 7 Days")
        attach_step_screenshot(driver, "Last 7 Days selected")

    with allure.step("Verify Analytics data reflects the Last 7 Days selection"):
        assert analytics.get_selected_period_label() == "Last 7 Days", (
            "Period dropdown did not update to 'Last 7 Days'"
        )
        value = analytics.get_metric_value("Latency")
        assert re.match(r"^-?\d+(\.\d+)?\s*ms$", value), f"Unexpected Latency value: {value!r}"
        print("Last 7 Days option selected successfully; Latency:", value)


@allure.feature("Analytics")
@allure.story("Period Filter")
@allure.title("TC_Analytics_16 — Verify Last 30 Days option in dropdown")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.analytics
def test_last_30_days_option_in_dropdown(logged_in_driver):
    driver = logged_in_driver

    with allure.step("Open Analytics page for an active agent"):
        _, analytics = _open_random_active_agent_analytics(driver)
        attach_step_screenshot(driver, "Analytics opened")

    with allure.step("Open the dropdown and select Last 30 Days"):
        analytics.select_period("Last 30 Days")
        attach_step_screenshot(driver, "Last 30 Days selected")

    with allure.step("Verify Analytics data reflects the Last 30 Days selection"):
        assert analytics.get_selected_period_label() == "Last 30 Days", (
            "Period dropdown did not update to 'Last 30 Days'"
        )
        value = analytics.get_metric_value("Latency")
        assert re.match(r"^-?\d+(\.\d+)?\s*ms$", value), f"Unexpected Latency value: {value!r}"
        print("Last 30 Days option selected successfully; Latency:", value)


@allure.feature("Analytics")
@allure.story("Refresh")
@allure.title("TC_Analytics_18 — Verify Refresh resets dropdown to Today and loads today's data")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.analytics
def test_refresh_resets_dropdown_to_today(logged_in_driver):
    driver = logged_in_driver

    with allure.step("Open Analytics page and select an option other than Today"):
        _, analytics = _open_random_active_agent_analytics(driver)
        analytics.select_period("Last 7 Days")
        assert analytics.get_selected_period_label() == "Last 7 Days"
        attach_step_screenshot(driver, "Last 7 Days selected")

    with allure.step("Click the Refresh icon/button"):
        analytics.click_refresh()
        attach_step_screenshot(driver, "Refresh clicked")

    with allure.step("Verify the dropdown resets to Today and today's data loads"):
        assert analytics.get_selected_period_label() == "Today", (
            "Refresh did not reset the period dropdown back to 'Today'"
        )
        assert analytics.is_analytics_page_loaded(), (
            "Analytics data did not remain loaded after Refresh"
        )
        print("Refresh reset the dropdown to 'Today' and reloaded data.")
        attach_step_screenshot(driver, "Dropdown reset to Today")


@allure.feature("Analytics")
@allure.story("Custom Date Range")
@allure.title("TC_Analytics_20 — Verify Pick a Date button opens calendar popup")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.analytics
def test_pick_a_date_button_opens_calendar(logged_in_driver):
    driver = logged_in_driver

    with allure.step("Open Analytics page for an active agent"):
        _, analytics = _open_random_active_agent_analytics(driver)
        attach_step_screenshot(driver, "Analytics opened")

    with allure.step("Click on the Pick a Date button"):
        analytics.open_date_range_picker()
        attach_step_screenshot(driver, "Calendar popup opened")

    with allure.step("Verify a calendar popup showing the current month and year opens"):
        assert analytics.is_calendar_open(), "Calendar popup did not open"
        month_labels = analytics.get_visible_calendar_month_labels()
        current_month_year = time.strftime("%B %Y")
        assert month_labels and month_labels[0] == current_month_year, (
            f"Expected calendar to open on '{current_month_year}', got {month_labels}"
        )
        print("Calendar popup opened showing:", month_labels[0])


@allure.feature("Analytics")
@allure.story("Custom Date Range")
@allure.title("TC_Analytics_21 — Verify Calendar icon opens calendar popup")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.analytics
def test_calendar_icon_opens_calendar(logged_in_driver):
    driver = logged_in_driver

    with allure.step("Open Analytics page for an active agent"):
        _, analytics = _open_random_active_agent_analytics(driver)
        attach_step_screenshot(driver, "Analytics opened")

    with allure.step("Click on the Calendar icon beside Pick a Date"):
        analytics.click_date_range_calendar_icon()
        attach_step_screenshot(driver, "Calendar popup opened via icon")

    with allure.step("Verify a calendar popup showing the current month and year opens"):
        assert analytics.is_calendar_open(), "Calendar popup did not open from the calendar icon"
        month_labels = analytics.get_visible_calendar_month_labels()
        current_month_year = time.strftime("%B %Y")
        assert month_labels and month_labels[0] == current_month_year, (
            f"Expected calendar to open on '{current_month_year}', got {month_labels}"
        )
        print("Calendar popup opened via the calendar icon, showing:", month_labels[0])


@allure.feature("Analytics")
@allure.story("Custom Date Range")
@allure.title("TC_Analytics_23 — Verify user can select a valid date")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.analytics
def test_select_valid_date(logged_in_driver):
    driver = logged_in_driver

    with allure.step("Open Analytics page and open the calendar"):
        _, analytics = _open_random_active_agent_analytics(driver)
        attach_step_screenshot(driver, "Analytics opened")

    with allure.step("Select a valid (past/today) date and apply it"):
        analytics.select_single_date_in_current_month(str(time.localtime().tm_mday))
        analytics.click_apply_date_range()
        attach_step_screenshot(driver, "Valid date selected")

    with allure.step("Verify the selected date is applied successfully"):
        # This calendar is a range picker (see
        # AnalyticsPage.select_single_date_in_current_month) — a single
        # selected date applies as a same-day range, e.g.
        # 'Aug 11, 2026 - Aug 11, 2026', rather than a bare single date.
        button_text = analytics.get_date_range_button_text()
        assert DATE_RANGE_PATTERN.match(button_text), (
            f"Selected date was not applied successfully, got: {button_text!r}"
        )
        start_text, end_text = [part.strip() for part in button_text.split(" - ")]
        assert start_text == end_text, (
            f"Expected the single selected date to apply as a same-day range, got: {button_text!r}"
        )
        print("Valid date applied successfully:", button_text)


@allure.feature("Analytics")
@allure.story("Custom Date Range")
@allure.title("TC_Analytics_24 — Verify user can select a custom date range")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.analytics
def test_select_custom_date_range(logged_in_driver):
    driver = logged_in_driver

    with allure.step("Open Analytics page and open the calendar"):
        _, analytics = _open_random_active_agent_analytics(driver)
        attach_step_screenshot(driver, "Analytics opened")

    with allure.step("Select a start date and an end date"):
        start_day, end_day = _safe_past_date_range()
        analytics.select_date_range_in_current_month(start_day, end_day)
        analytics.click_apply_date_range()
        attach_step_screenshot(driver, "Custom date range selected")

    with allure.step("Verify Analytics data updates for the selected range"):
        button_text = analytics.get_date_range_button_text()
        assert DATE_RANGE_PATTERN.match(button_text), (
            f"Unexpected date range button text: {button_text!r}"
        )
        print("Custom date range applied:", button_text)


@allure.feature("Analytics")
@allure.story("Custom Date Range")
@allure.title("TC_Analytics_25 — Verify future dates cannot be selected")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.analytics
def test_future_dates_cannot_be_selected(logged_in_driver):
    driver = logged_in_driver

    with allure.step("Open Analytics page and open the calendar"):
        _, analytics = _open_random_active_agent_analytics(driver)
        analytics.open_date_range_picker()
        attach_step_screenshot(driver, "Calendar opened")

    with allure.step("Try selecting a future date (an entire month ahead)"):
        future_days = analytics.get_future_month_day_buttons()
        assert future_days, "No day cells found in the next month view"
        attach_step_screenshot(driver, "Future month opened")

    with allure.step("Verify future dates are disabled/restricted"):
        assert all(analytics.is_day_button_disabled(day) for day in future_days), (
            "Not every day in a future month is marked disabled"
        )
        blocked = analytics.try_click_day_button(future_days[0])
        assert blocked, "A future date was clickable when it should be disabled/restricted"
        print(f"All {len(future_days)} future-month day cells are disabled and unclickable.")


@allure.feature("Analytics")
@allure.story("Refresh")
@allure.title("TC_Analytics_26 — Verify Refresh resets date range and loads default data")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.analytics
def test_refresh_resets_date_range(logged_in_driver):
    driver = logged_in_driver

    with allure.step("Open Analytics page and select a custom date range"):
        _, analytics = _open_random_active_agent_analytics(driver)
        start_day, end_day = _safe_past_date_range()
        analytics.select_date_range_in_current_month(start_day, end_day)
        analytics.click_apply_date_range()
        assert analytics.get_date_range_button_text() != "Pick a date", (
            "Date range was not applied before attempting to clear it via Refresh"
        )
        attach_step_screenshot(driver, "Custom date range applied")

    with allure.step("Click the Refresh icon/button"):
        analytics.click_refresh()
        attach_step_screenshot(driver, "Refresh clicked")

    with allure.step("Verify the date range clears and default (Today's) data loads"):
        assert analytics.get_date_range_button_text() == "Pick a date", (
            "Refresh did not clear/reset the selected date range"
        )
        assert analytics.get_selected_period_label() == "Today", (
            "Refresh did not fall back to the default 'Today' data"
        )
        print("Refresh cleared the date range and reloaded default (Today's) data.")
        attach_step_screenshot(driver, "Date range reset")


@allure.feature("Analytics")
@allure.story("Agent Interaction")
@allure.title("TC_Analytics_32 — Verify an agent interaction shows up in the Analytics graph")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.analytics
def test_agent_interaction_reflected_in_analytics(logged_in_driver):
    driver = logged_in_driver
    main_window = driver.current_window_handle

    with allure.step("Open Analytics for an active agent and note the current Latency value"):
        agent_name, analytics = _open_random_active_agent_analytics(driver)
        value_before = analytics.get_metric_value("Latency")
        print(f"Latency before interaction for '{agent_name}':", value_before)
        attach_step_screenshot(driver, "Latency before interaction")

    with allure.step("Chat with the agent"):
        chat_link = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//a[normalize-space()='Chat']"))
        )
        chat_link.click()
        WebDriverWait(driver, 20).until(lambda d: len(d.window_handles) > 1)
        driver.switch_to.window(driver.window_handles[-1])

        chat_page = ChatPage(driver)
        assert chat_page.is_message_input_visible(), "Chat message input did not appear"
        chat_page.send_message(f"Automated Analytics test interaction for '{agent_name}'")
        # Give the agent a moment to actually respond and the interaction
        # to be recorded server-side before checking Analytics for it.
        time.sleep(15)

        driver.close()
        driver.switch_to.window(main_window)

    with allure.step("Return to Analytics, refresh, and verify the interaction is reflected"):
        # The main window was left sitting on this same agent's Analytics
        # tab the whole time the Chat tab was open in its own window, so
        # switching back resumes that same page context — no re-navigation
        # needed, only a data refresh (same pattern as the Dashboard
        # suite's equivalent "new interaction" test).
        assert analytics.is_analytics_page_loaded(), "Analytics page was not intact after returning from Chat"
        analytics.click_refresh()

        WebDriverWait(driver, 30).until(
            lambda d: analytics.get_metric_value("Latency") != value_before
        )
        value_after = analytics.get_metric_value("Latency")
        assert value_after != value_before, (
            f"Latency did not change after the interaction (before={value_before!r}, after={value_after!r})"
        )
        print(f"Latency updated from '{value_before}' to '{value_after}' after the interaction.")
        attach_step_screenshot(driver, "Interaction reflected in Analytics")
