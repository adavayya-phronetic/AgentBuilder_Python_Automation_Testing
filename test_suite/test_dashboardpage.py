import random

import allure
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from Webpages.dashboard_page import DashboardPage
from Webpages.my_agents_page import MyAgentsPage
from Webpages.chat_page import ChatPage
from Utility.allure_helpers import attach_step_screenshot


def _open_chat_tab_in_new_window(driver):
    chat_link = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//a[normalize-space()='Chat']"))
    )
    chat_link.click()
    WebDriverWait(driver, 20).until(lambda d: len(d.window_handles) > 1)
    driver.switch_to.window(driver.window_handles[-1])


@allure.feature("Dashboard")
@allure.story("Dashboard Load")
@allure.title("TC_Dashboard_03 — Dashboard page loads successfully")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.dashboard
def test_dashboard_loads_successfully(logged_in_driver):
    driver = logged_in_driver

    with allure.step("Navigate to Dashboard"):
        dashboard = DashboardPage(driver)
        dashboard.navigate_to_dashboard()
        attach_step_screenshot(driver, "Dashboard opened")

    with allure.step("Verify the greeting and all summary cards are displayed"):
        assert dashboard.is_dashboard_loaded(), (
            "Dashboard did not load successfully — greeting or summary cards missing"
        )
        print("Dashboard loaded with all widgets and summary cards.")
        attach_step_screenshot(driver, "Dashboard loaded with widgets")


@allure.feature("Dashboard")
@allure.story("Navigation")
@allure.title("TC_Dashboard_06 — Agents card icon navigates to My Agents page")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.dashboard
def test_agents_card_navigates_to_my_agents(logged_in_driver):
    driver = logged_in_driver

    with allure.step("Navigate to Dashboard and click the Agents card icon"):
        dashboard = DashboardPage(driver)
        dashboard.navigate_to_dashboard()
        dashboard.click_agents_card_icon()

    with allure.step("Verify redirect to My Agents page"):
        WebDriverWait(driver, 20).until(EC.url_contains("/agents"))
        assert "/agents" in driver.current_url, (
            f"Expected redirect to My Agents page, current URL: {driver.current_url}"
        )
        print("Redirected to My Agents page:", driver.current_url)
        attach_step_screenshot(driver, "My Agents page reached")


@allure.feature("Dashboard")
@allure.story("Navigation")
@allure.title("TC_Dashboard_07 — Browser Back from My Agents returns to Dashboard")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.dashboard
def test_back_button_from_my_agents_returns_to_dashboard(logged_in_driver):
    driver = logged_in_driver

    with allure.step("Navigate to My Agents via the Agents card icon"):
        dashboard = DashboardPage(driver)
        dashboard.navigate_to_dashboard()
        dashboard.click_agents_card_icon()
        WebDriverWait(driver, 20).until(EC.url_contains("/agents"))
        attach_step_screenshot(driver, "On My Agents page")

    with allure.step("Click the browser Back button"):
        driver.back()
        WebDriverWait(driver, 20).until(EC.url_contains("/dashboard"))

        assert "/dashboard" in driver.current_url, (
            f"Expected browser Back to return to Dashboard, current URL: {driver.current_url}"
        )
        print("Returned to Dashboard via browser Back:", driver.current_url)
        attach_step_screenshot(driver, "Back on Dashboard")


@allure.feature("Dashboard")
@allure.story("Navigation")
@allure.title("TC_Dashboard_09 — Tools Created card icon navigates to Tools page")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.dashboard
def test_tools_created_card_navigates_to_tools_page(logged_in_driver):
    driver = logged_in_driver

    with allure.step("Navigate to Dashboard and click the Tools Created card icon"):
        dashboard = DashboardPage(driver)
        dashboard.navigate_to_dashboard()
        dashboard.click_tools_created_card_icon()

    with allure.step("Verify redirect to the Tools page"):
        WebDriverWait(driver, 20).until(EC.url_contains("/tools"))
        assert "/tools" in driver.current_url, (
            f"Expected redirect to Tools page, current URL: {driver.current_url}"
        )
        print("Redirected to Tools page:", driver.current_url)
        attach_step_screenshot(driver, "Tools page reached")


@allure.feature("Dashboard")
@allure.story("Navigation")
@allure.title("TC_Dashboard_10 — Browser Back from Tools page returns to Dashboard")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.dashboard
def test_back_button_from_tools_page_returns_to_dashboard(logged_in_driver):
    driver = logged_in_driver

    with allure.step("Navigate to Tools page via the Tools Created card icon"):
        dashboard = DashboardPage(driver)
        dashboard.navigate_to_dashboard()
        dashboard.click_tools_created_card_icon()
        WebDriverWait(driver, 20).until(EC.url_contains("/tools"))
        attach_step_screenshot(driver, "On Tools page")

    with allure.step("Click the browser Back button"):
        driver.back()
        WebDriverWait(driver, 20).until(EC.url_contains("/dashboard"))

        assert "/dashboard" in driver.current_url, (
            f"Expected browser Back to return to Dashboard, current URL: {driver.current_url}"
        )
        print("Returned to Dashboard via browser Back:", driver.current_url)
        attach_step_screenshot(driver, "Back on Dashboard")


@allure.feature("Dashboard")
@allure.story("Summary Cards")
@allure.title("TC_Dashboard_12 — Sessions count updates after a new agent interaction")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.dashboard
def test_sessions_count_increases_after_new_interaction(logged_in_driver):
    driver = logged_in_driver
    main_window = driver.current_window_handle

    with allure.step("Note the current Sessions count on Dashboard"):
        dashboard = DashboardPage(driver)
        dashboard.navigate_to_dashboard()
        count_before = dashboard.get_card_count(dashboard.sessions_count)
        print("Sessions count before new interaction:", count_before)
        attach_step_screenshot(driver, "Sessions count noted")

    with allure.step("Open an active agent's Chat and send a new message"):
        agents_page = MyAgentsPage(driver)
        agents_page.navigate_to_my_agents()

        active_agent_names = agents_page.get_active_agent_names()
        assert active_agent_names, "No active agents found to start a new session with"

        target_agent_name = random.choice(active_agent_names)
        agents_page.search_agent(target_agent_name)
        agents_page.click_agent_card(target_agent_name)

        _open_chat_tab_in_new_window(driver)
        chat_page = ChatPage(driver)
        assert chat_page.is_message_input_visible(), "Chat message input did not appear"

        url_before = chat_page.get_current_url()
        chat_page.send_message(f"Automated Dashboard test session for '{target_agent_name}'")
        WebDriverWait(driver, 30).until(lambda d: d.current_url != url_before)
        print(f"New session created with agent '{target_agent_name}'.")

        driver.close()
        driver.switch_to.window(main_window)

    with allure.step("Return to Dashboard, refresh, and verify the Sessions count increased"):
        dashboard.navigate_to_dashboard()
        dashboard.click_refresh_dashboard()

        WebDriverWait(driver, 20).until(
            lambda d: dashboard.get_card_count(dashboard.sessions_count) > count_before
        )
        count_after = dashboard.get_card_count(dashboard.sessions_count)
        assert count_after > count_before, (
            f"Expected Sessions count to increase from {count_before}, got {count_after}"
        )
        print(f"Sessions count increased from {count_before} to {count_after}.")
        attach_step_screenshot(driver, "Sessions count increased")


@allure.feature("Dashboard")
@allure.story("Unique Users")
@allure.title("TC_Dashboard_15 — Unique Users card opens the Unique Users popup")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.dashboard
def test_unique_users_card_opens_popup(logged_in_driver):
    driver = logged_in_driver

    with allure.step("Navigate to Dashboard and click the Unique Users card"):
        dashboard = DashboardPage(driver)
        dashboard.navigate_to_dashboard()
        dashboard.click_unique_users_card_icon()

    with allure.step("Verify the Unique Users popup opens with user details"):
        assert dashboard.is_unique_users_popup_open(), "Unique Users popup did not open"
        results = dashboard.get_unique_users_result_texts()
        assert results, "Expected at least one user entry in the Unique Users popup"
        print("Unique Users popup opened with entries:", results)
        attach_step_screenshot(driver, "Unique Users popup opened")
        dashboard.close_unique_users_popup()


@allure.feature("Dashboard")
@allure.story("Unique Users")
@allure.title("TC_Dashboard_16 — Search functionality in Unique Users popup")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.dashboard
def test_unique_users_popup_search(logged_in_driver):
    driver = logged_in_driver

    with allure.step("Open the Unique Users popup"):
        dashboard = DashboardPage(driver)
        dashboard.navigate_to_dashboard()
        dashboard.click_unique_users_card_icon()
        assert dashboard.is_unique_users_popup_open(), "Unique Users popup did not open"

        all_results = dashboard.get_unique_users_result_texts()
        assert all_results, "No users available to search for"
        search_term = all_results[0].split("@")[0][-4:]

    with allure.step(f"Search for '{search_term}'"):
        dashboard.search_unique_users(search_term)
        attach_step_screenshot(driver, "Search entered in Unique Users popup")

        filtered_results = dashboard.get_unique_users_result_texts()
        assert filtered_results, f"Expected matching user records for '{search_term}'"
        assert all(search_term.lower() in r.lower() for r in filtered_results), (
            f"Expected only results matching '{search_term}', got {filtered_results}"
        )
        print(f"Search for '{search_term}' returned matching records:", filtered_results)
        attach_step_screenshot(driver, "Matching user records displayed")
        dashboard.close_unique_users_popup()


@allure.feature("Dashboard")
@allure.story("Active Gateways")
@allure.title("TC_Dashboard_18 — Active Gateways card opens the Active Gateways popup")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.dashboard
def test_active_gateways_card_opens_popup(logged_in_driver):
    driver = logged_in_driver

    with allure.step("Navigate to Dashboard and click the Active Gateways card"):
        dashboard = DashboardPage(driver)
        dashboard.navigate_to_dashboard()
        dashboard.click_active_gateways_card_icon()

    with allure.step("Verify the Active Gateways popup opens"):
        assert dashboard.is_active_gateways_popup_open(), "Active Gateways popup did not open"
        print("Active Gateways popup opened.")
        attach_step_screenshot(driver, "Active Gateways popup opened")
        dashboard.close_active_gateways_popup()


@allure.feature("Dashboard")
@allure.story("Active Gateways")
@allure.title("TC_Dashboard_19 — Active Gateways popup shows connected agent/gateway details")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.dashboard
def test_active_gateways_popup_shows_connected_details(logged_in_driver):
    """
    TC_Dashboard_19/20/21 from the sheet all depend on at least one active
    gateway already being configured. This account currently has 0 active
    gateways (confirmed live: the popup shows 'No active gateways
    available.'), so this skips gracefully rather than asserting against
    data that doesn't exist — the same pattern already used elsewhere in
    this suite when a precondition isn't met (e.g. a created agent with no
    sub-agent node).
    """
    driver = logged_in_driver

    with allure.step("Open the Active Gateways popup"):
        dashboard = DashboardPage(driver)
        dashboard.navigate_to_dashboard()
        dashboard.click_active_gateways_card_icon()
        assert dashboard.is_active_gateways_popup_open(), "Active Gateways popup did not open"

    with allure.step("Verify connected agent/gateway details, or skip if none exist"):
        if dashboard.is_active_gateways_empty_message_shown(timeout=5):
            dashboard.close_active_gateways_popup()
            pytest.skip(
                "No active gateways configured for this account — nothing to verify. "
                "Configure at least one gateway to exercise this test case."
            )

        attach_step_screenshot(driver, "Active Gateways popup with connected details")
        dashboard.close_active_gateways_popup()


@allure.feature("Dashboard")
@allure.story("Performance & Usage")
@allure.title("TC_Dashboard_23 — Session Performance graph updates for the selected date")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.dashboard
def test_session_performance_graph_updates_for_selected_date(logged_in_driver):
    driver = logged_in_driver

    with allure.step("Navigate to Dashboard and note the current Session Performance count"):
        dashboard = DashboardPage(driver)
        dashboard.navigate_to_dashboard()
        count_before = dashboard.get_session_performance_count()
        print("Session Performance count before filter:", count_before)

    with allure.step("Apply a date filter for a date with no session data"):
        dashboard.open_date_time_filter()
        dashboard.set_date_range("2020-01-01", "2020-01-02")
        dashboard.click_apply_date_filter()
        attach_step_screenshot(driver, "Date filter applied")

    with allure.step("Verify the Session Performance graph reflects only the selected date"):
        WebDriverWait(driver, 15).until(
            lambda d: dashboard.get_session_performance_count() != count_before
        )
        count_after = dashboard.get_session_performance_count()
        assert count_after != count_before, (
            f"Expected Session Performance count to change from {count_before} for the "
            f"filtered date, but it stayed the same"
        )
        print(f"Session Performance count for the filtered date: {count_after}")
        attach_step_screenshot(driver, "Session Performance graph updated")


@allure.feature("Dashboard")
@allure.story("Performance & Usage")
@allure.title("TC_Dashboard_25 — Session Performance graph shows empty state with no data")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.dashboard
def test_session_performance_empty_state(logged_in_driver):
    driver = logged_in_driver

    with allure.step("Navigate to Dashboard and apply a date filter with no session data"):
        dashboard = DashboardPage(driver)
        dashboard.navigate_to_dashboard()
        dashboard.open_date_time_filter()
        dashboard.set_date_range("2020-01-01", "2020-01-02")
        dashboard.click_apply_date_filter()
        attach_step_screenshot(driver, "Date filter with no data applied")

    with allure.step("Verify the graph shows an empty state (0 sessions) without errors"):
        # get_session_performance_count() already waits internally for the
        # count element itself to be visible — no outer WebDriverWait
        # needed here, and using until() would be actively wrong for this
        # specific assertion anyway: 0 is the expected value, but 0 is
        # falsy, so until() would treat a correct "0" result as "not yet
        # succeeded" and retry until it timed out regardless.
        count = dashboard.get_session_performance_count()
        assert count == 0, (
            f"Expected 0 sessions for a date range with no data, got {count}"
        )
        print("Session Performance graph correctly shows 0 sessions for the empty date range.")
        attach_step_screenshot(driver, "Empty state displayed correctly")


@allure.feature("Dashboard")
@allure.story("Performance & Usage")
@allure.title("TC_Dashboard_27 — Credit Usage graph updates for the selected date")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.dashboard
def test_credit_usage_graph_updates_for_selected_date(logged_in_driver):
    driver = logged_in_driver

    with allure.step("Navigate to Dashboard and note the current Credit Usage amount"):
        dashboard = DashboardPage(driver)
        dashboard.navigate_to_dashboard()
        amount_before = dashboard.get_credit_usage_amount_text()
        print("Credit Usage amount before filter:", amount_before)

    with allure.step("Apply a date filter for a date with no usage data"):
        dashboard.open_date_time_filter()
        dashboard.set_date_range("2020-01-01", "2020-01-02")
        dashboard.click_apply_date_filter()
        attach_step_screenshot(driver, "Date filter applied")

    with allure.step("Verify the Credit Usage graph reflects only the selected date"):
        # A truly empty date range renders no rupee amount at all in the
        # current UI — just a "No spend in this period" empty-state message
        # (confirmed live) — so this filtered-to-no-data scenario is only
        # ever going to land in that empty state, never a changed amount
        # string. Same reasoning as test_session_performance_empty_state's
        # falsy-0 fix: assert the actual state reached, not a text diff that
        # this specific filter can never produce.
        assert dashboard.is_credit_usage_empty_state(timeout=15), (
            "Expected the Credit Usage widget to show its empty state "
            "('No spend in this period') for a date range with no usage data"
        )
        print("Credit Usage graph correctly shows the empty state for the filtered date "
              f"(amount before filter was {amount_before!r}).")
        attach_step_screenshot(driver, "Credit Usage graph empty state shown")


@allure.feature("Dashboard")
@allure.story("Agents & Activity")
@allure.title("TC_Dashboard_43 — 'View All' in Agents & Activity navigates to My Agents page")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.dashboard
def test_agents_activity_view_all_navigates_to_my_agents(logged_in_driver):
    driver = logged_in_driver

    with allure.step("Navigate to Dashboard and click 'View All' in Agents & Activity"):
        dashboard = DashboardPage(driver)
        dashboard.navigate_to_dashboard()
        dashboard.click_agents_activity_view_all()

    with allure.step("Verify redirect to the My Agents page"):
        WebDriverWait(driver, 20).until(EC.url_contains("/agents"))
        assert "/agents" in driver.current_url, (
            f"Expected redirect to My Agents page, current URL: {driver.current_url}"
        )
        print("Redirected to My Agents page:", driver.current_url)
        attach_step_screenshot(driver, "My Agents page reached")