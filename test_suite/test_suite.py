# Purpose: Test login & logout flow using POM

from datetime import datetime

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
        f"Develop an AI agent (ref #{unique_id}) that helps You are a blog post writer. When given a topic, write a complete," 
f"well-structured blog post with a title, introduction, subheadings,"
f"body content, and conclusion. Assume a general audience, professional "
f"tone, and 600-800 word length unless specified. Never ask for clarification —" 
f"make reasonable assumptions and deliver the full post immediately. "
        f"Dont ask any follow up questions just do basic configuration"
    )

    agents_page.click_create_agent()

    # Agent Configuration Page
    config_page = AgentConfigurationPage(driver)

    config_page.wait_for_agent_creation()

    assert config_page.verify_agent_configuration_page()

    print("Agent URL:", config_page.get_current_url())

    config_page.click_save()

    if config_page.is_duplicate_name_error_present():
        raise AssertionError(
            f"Agent Creation Failed: {config_page.get_creation_error()}"
        )

    agent_name = config_page.wait_for_agent_name_update()
    print("Generated agent name:", agent_name)

    config_page.go_back_to_agents()

    agents_page.set_status_filter_all()

    assert agents_page.verify_agent_card(agent_name)

    print("Agent created successfully:", agent_name)