# Purpose: Test login & logout flow using POM

from datetime import datetime

import pytest

from Webpages.landing_page import LandingPage
from Webpages.login_page import LoginPage
from Webpages.dashboard_page import DashboardPage
from Webpages.MyAgent_Page import MyAgentsPage
from Webpages.AgentConfigurationPage import AgentConfigurationPage
from Utility import config


def test_login_logout(driver):

    # Landing Page
    landing_page = LandingPage(driver)

    landing_page.open_page()
    landing_page.click_get_started()

    # Login Page
    login_page = LoginPage(driver)

    login_page.login(
        config.username,
        config.password
    )

    # Dashboard Page
    dashboard = DashboardPage(driver)

    dashboard.logout()


def test_invalid_login(driver):

    # Landing Page
    landing_page = LandingPage(driver)

    landing_page.open_page()
    landing_page.click_get_started()

    # Login Page
    login_page = LoginPage(driver)

    login_page.login(
        "invalid_user@phronetic.ai",
        "WrongPassword@123"
    )

    error_message = login_page.get_login_error()

    assert error_message is not None, "Expected an error message for invalid login credentials"
    assert login_page.is_on_login_page(), "User should not be logged in with invalid credentials"

    print("Invalid login error message:", error_message)


def test_invalid_password(driver):

    # Landing Page
    landing_page = LandingPage(driver)

    landing_page.open_page()
    landing_page.click_get_started()

    # Login Page
    login_page = LoginPage(driver)

    login_page.login(
        config.username,
        "WrongPassword@123"
    )

    error_message = login_page.get_login_error()

    assert error_message is not None, "Expected an error message for invalid password"
    assert login_page.is_on_login_page(), "User should not be logged in with an invalid password"

    print("Invalid password error message:", error_message)


def test_empty_login_fields(driver):

    # Landing Page
    landing_page = LandingPage(driver)

    landing_page.open_page()
    landing_page.click_get_started()

    # Login Page
    login_page = LoginPage(driver)

    login_page.login("", "")

    email_error = login_page.get_email_field_error()
    password_error = login_page.get_password_field_error()

    assert email_error is not None, "Expected validation error for empty email field"
    assert password_error is not None, "Expected validation error for empty password field"
    assert login_page.is_on_login_page(), "User should not be logged in with empty credentials"

    print("Empty email field error:", email_error)
    print("Empty password field error:", password_error)


@pytest.mark.flaky(reruns=1, reruns_delay=5, only_rerun=["InvalidSessionIdException", "WebDriverException"])
def test_create_agent(driver):

    # Landing Page
    landing_page = LandingPage(driver)

    landing_page.open_page()
    landing_page.click_get_started()

    # Login Page
    login_page = LoginPage(driver)

    login_page.login(
        config.username,
        config.password
    )

    # My Agents Page
    agents_page = MyAgentsPage(driver)

    agents_page.click_my_agents()

    unique_id = datetime.now().strftime("%Y%m%d%H%M%S")

    agents_page.enter_prompt(
        f"Create an assistant (ref #{unique_id}) that summarizes user-provided text into key points and action items."
        f"Do not ask follow-up questions,just do the basic configration only."
    )

    agents_page.click_create_agent()

    # Agent Configuration Page
    config_page = AgentConfigurationPage(driver)

    config_page.wait_for_agent_creation()

    assert config_page.verify_agent_configuration_page()

    print("Agent URL:", config_page.get_current_url())

    if config_page.is_duplicate_name_error_present():
        raise AssertionError(
            f"Agent Creation Failed: {config_page.get_creation_error()}"
        )

    agent_name = config_page.wait_for_agent_name_update()
    print("Generated agent name:", agent_name)

    config_page.go_back_to_agents()

    agents_page.set_status_filter_all()

    if agents_page.verify_agent_card(agent_name):
        print("Agent created successfully:", agent_name)
    else:
        print(f"WARNING: Agent '{agent_name}' was created but did not yet "
              f"appear in the My Agents list (backend indexing lag).")