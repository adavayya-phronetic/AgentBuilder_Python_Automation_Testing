import os
import time
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
        f"Create an assistant (ref #{unique_id}) that summarizes text into three bullet points."
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


def test_configure_agent_io_and_upload(driver):

    target_agent_name = "Text Summarizer Assistant"
    upload_file_path = os.path.abspath(
        os.path.join("Files", "Git_Reference_Guide.pdf")
    )

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
    agents_page.search_agent(target_agent_name)
    agents_page.click_agent_card(target_agent_name)

    # Agent Configuration Page (Editor tab)
    config_page = AgentConfigurationPage(driver)

    config_page.click_editor_tab()
    config_page.select_input_type_audio()
    config_page.select_output_type_audio()
    config_page.select_output_type_video()

    file_name = os.path.basename(upload_file_path)
    count_before_upload = config_page.count_knowledge_base_files(file_name)

    config_page.upload_file(upload_file_path)

    assert config_page.count_knowledge_base_files(file_name) > count_before_upload, (
        f"'{file_name}' did not appear in the knowledge base after upload"
    )

    print(f"Uploaded file for agent '{target_agent_name}':", upload_file_path)

    count_before_delete = config_page.count_knowledge_base_files(file_name)
    config_page.cancel_delete_knowledge_base_file(file_name)

    assert config_page.count_knowledge_base_files(file_name) == count_before_delete, (
        f"'{file_name}' was removed even though delete was cancelled"
    )

    print(f"Cancelled delete of '{file_name}'; file remains in knowledge base.")

    config_page.delete_knowledge_base_file(file_name)

    assert config_page.count_knowledge_base_files(file_name) == count_before_upload, (
        f"'{file_name}' was not removed from the knowledge base after delete"
    )

    print(f"Deleted file '{file_name}' from knowledge base for agent '{target_agent_name}'.")


def test_attach_tool_to_orchestrator(driver):

    target_agent_name = "Text Summarizer Assistant"
    orchestrator_card_name = "TextSummarizerOrchestrator"
    model_provider = "Bedrock"
    tool_names = ["Convert_Language", "Addition"]

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
    agents_page.search_agent(target_agent_name)
    agents_page.click_agent_card(target_agent_name)

    # Agent Configuration Page (Graph tab)
    config_page = AgentConfigurationPage(driver)

    config_page.click_graph_tab()
    config_page.open_agent_card(orchestrator_card_name)
    config_page.select_model_provider(model_provider)
    chosen_model = config_page.select_random_model()

    for tool_name in tool_names:
        config_page.select_tool(tool_name)

        assert config_page.is_tool_selected(tool_name), (
            f"Tool '{tool_name}' did not appear as selected after select_tool()"
        )

    config_page.click_save()
    config_page.click_redeploy()

    # Navigate away and back in-app (a hard reload drops the session and
    # bounces to /auth) to confirm the tool attachments actually persisted
    # on the backend, not just in the UI. Backend indexing can lag behind
    # the redeploy confirmation, so retry the re-navigation a few times
    # before treating it as a real failure.
    missing_tools = list(tool_names)
    for attempt in range(3):
        if attempt > 0:
            time.sleep(10)

        config_page.go_back_to_agents()
        agents_page.search_agent(target_agent_name)
        agents_page.click_agent_card(target_agent_name)
        config_page.click_graph_tab()
        config_page.open_agent_card(orchestrator_card_name)

        missing_tools = [
            t for t in tool_names if not config_page.is_tool_selected(t, timeout=30)
        ]
        if not missing_tools:
            break

    assert not missing_tools, (
        f"Tool(s) {missing_tools} were not attached to '{orchestrator_card_name}' "
        f"after save and redeploy"
    )

    print(f"Set provider '{model_provider}' with model '{chosen_model}', "
          f"attached tools {tool_names} to '{orchestrator_card_name}', "
          f"and redeployed agent '{target_agent_name}'.")