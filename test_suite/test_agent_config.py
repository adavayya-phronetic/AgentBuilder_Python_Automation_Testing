import os
import random
import time

import allure
import pytest
from Webpages.my_agent_page import MyAgentsPage
from Webpages.agent_configuration_page import AgentConfigurationPage
from Utility.allure_helpers import attach_step_screenshot


@allure.feature("Agent Configuration")
@allure.story("Knowledge Base")
@allure.title("Configure I/O types and upload, cancel-delete, then delete a knowledge base file")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.knowledge_base
def test_configure_agent_io_and_upload(logged_in_driver):

    driver = logged_in_driver

    upload_file_path = os.path.abspath(
        os.path.join("Files", "Git_Reference_Guide.pdf")
    )
    file_name = os.path.basename(upload_file_path)

    with allure.step("Select a random active agent"):
        agents_page = MyAgentsPage(driver)
        agents_page.click_my_agents()

        active_agent_names = agents_page.get_active_agent_names()
        assert active_agent_names, "No active agents found in the agent card list"

        target_agent_name = random.choice(active_agent_names)
        allure.attach(target_agent_name, name="Target agent", attachment_type=allure.attachment_type.TEXT)

        agents_page.search_agent(target_agent_name)
        agents_page.click_agent_card(target_agent_name)
        attach_step_screenshot(driver, "Agent selected")

    with allure.step("Configure audio and video I/O types on the EDITOR tab"):
        config_page = AgentConfigurationPage(driver)
        config_page.click_editor_tab()
        config_page.select_input_type_audio()
        config_page.select_output_type_audio()
        config_page.select_output_type_video()
        attach_step_screenshot(driver, "Audio/video I/O configured")

    with allure.step(f"Upload '{file_name}' to the knowledge base"):
        count_before_upload = config_page.count_knowledge_base_files(file_name)
        config_page.upload_file(upload_file_path)

        assert config_page.count_knowledge_base_files(file_name) > count_before_upload, (
            f"'{file_name}' did not appear in the knowledge base after upload"
        )
        print(f"Uploaded file for agent '{target_agent_name}':", upload_file_path)
        attach_step_screenshot(driver, "File uploaded to knowledge base")

    with allure.step(f"Cancel deletion of '{file_name}' — file must remain"):
        count_before_delete = config_page.count_knowledge_base_files(file_name)
        config_page.cancel_delete_knowledge_base_file(file_name)

        assert config_page.count_knowledge_base_files(file_name) == count_before_delete, (
            f"'{file_name}' was removed even though delete was cancelled"
        )
        print(f"Cancelled delete of '{file_name}'; file remains in knowledge base.")
        attach_step_screenshot(driver, "Deletion cancelled, file remains")

    with allure.step(f"Delete '{file_name}' from the knowledge base"):
        config_page.delete_knowledge_base_file(file_name)

        assert config_page.count_knowledge_base_files(file_name) == count_before_upload, (
            f"'{file_name}' was not removed from the knowledge base after delete"
        )
        print(f"Deleted file '{file_name}' from knowledge base for agent '{target_agent_name}'.")
        attach_step_screenshot(driver, "File deleted from knowledge base")


@allure.feature("Agent Configuration")
@allure.story("Tool Attachment")
@allure.title("Attach tools to orchestrator, redeploy, and verify persistence after navigating away")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.tool_attachment
def test_attach_tool_to_orchestrator(logged_in_driver):

    driver = logged_in_driver

    model_provider = "Bedrock"
    tool_names = ["Convert_Language", "Addition"]

    with allure.step("Select a random active agent"):
        agents_page = MyAgentsPage(driver)
        agents_page.click_my_agents()

        active_agent_names = agents_page.get_active_agent_names()
        assert active_agent_names, "No active agents found in the agent card list"

        target_agent_name = random.choice(active_agent_names)
        allure.attach(target_agent_name, name="Target agent", attachment_type=allure.attachment_type.TEXT)

        agents_page.search_agent(target_agent_name)
        agents_page.click_agent_card(target_agent_name)
        attach_step_screenshot(driver, "Agent selected")

    with allure.step("Open a random agent card on the GRAPH tab and set model"):
        config_page = AgentConfigurationPage(driver)
        config_page.click_graph_tab()

        card_names = config_page.get_agent_card_names()
        assert card_names, f"No configurable agent cards found in the graph for '{target_agent_name}'"

        orchestrator_card_name = random.choice(card_names)
        allure.attach(orchestrator_card_name, name="Orchestrator card", attachment_type=allure.attachment_type.TEXT)

        config_page.open_agent_card(orchestrator_card_name)
        config_page.select_model_provider(model_provider)
        chosen_model = config_page.select_random_model()

        allure.attach(
            f"Agent: {target_agent_name}\nCard: {orchestrator_card_name}\nProvider: {model_provider}\nModel: {chosen_model}",
            name="Configuration summary",
            attachment_type=allure.attachment_type.TEXT
        )
        print(f"Testing agent '{target_agent_name}', card '{orchestrator_card_name}', "
              f"provider '{model_provider}', model '{chosen_model}'")
        attach_step_screenshot(driver, "Model provider and model set")

    with allure.step(f"Attach tools {tool_names} and verify each appears as selected"):
        for tool_name in tool_names:
            config_page.select_tool(tool_name)

            assert config_page.is_tool_selected(tool_name), (
                f"Tool '{tool_name}' did not appear as selected after select_tool()"
            )
        attach_step_screenshot(driver, "Tools attached")

    with allure.step("Save and redeploy the agent"):
        config_page.click_save()
        config_page.click_redeploy()
        attach_step_screenshot(driver, "Saved and redeployed")

    with allure.step("Navigate away and back to confirm tools persisted on the backend"):
        # A hard reload drops the session so we navigate in-app instead.
        # Backend indexing can lag behind the redeploy confirmation, so retry.
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
        attach_step_screenshot(driver, "Tools persisted after navigation")


@allure.feature("Agent Management")
@allure.story("Search")
@allure.title("Agent search returns results for partial and middle-text matches, not just prefix")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.search
def test_agent_search_partial_match(logged_in_driver):
    """
    Bug: Search only returns results when the query matches the START of an agent name.
    Expected: Searching with any substring (including middle text) should return matching agents.

    Steps:
    1. Navigate to My Agents.
    2. Pick an active agent whose name is long enough to extract a middle substring.
    3. Search using characters from the MIDDLE of the name (not the prefix).
    4. Verify the agent appears in the results.
    """
    driver = logged_in_driver

    with allure.step("Navigate to My Agents and collect active agent names"):
        agents_page = MyAgentsPage(driver)
        agents_page.click_my_agents()

        active_names = agents_page.get_active_agent_names()
        assert active_names, "No active agents found to test search against"

        # Need a name with at least 6 characters so the middle slice is meaningful
        target_name = next((n for n in active_names if len(n.replace(" ", "")) >= 6), None)
        assert target_name, (
            "No active agent with a name long enough (≥6 non-space chars) "
            "to extract a meaningful middle substring for search testing"
        )
        allure.attach(target_name, name="Target agent name", attachment_type=allure.attachment_type.TEXT)
        attach_step_screenshot(driver, "Active agent names collected")

    with allure.step("Search with a middle substring and verify the agent appears"):
        # Extract characters from the middle third of the name, skipping spaces at boundaries
        words = target_name.split()
        if len(words) >= 2:
            # Multi-word name: use the last word (avoids prefix matching)
            partial_text = words[-1]
        else:
            # Single word: take from 1/3 to 2/3 of the string
            start = max(1, len(target_name) // 3)
            end = min(len(target_name) - 1, 2 * len(target_name) // 3)
            partial_text = target_name[start:end].strip()

        assert len(partial_text) >= 2, (
            f"Extracted partial text '{partial_text}' is too short to be a useful search term"
        )
        allure.attach(
            f"Full name : '{target_name}'\nSearch term: '{partial_text}'",
            name="Partial search term",
            attachment_type=allure.attachment_type.TEXT
        )

        agents_page.search_agent(partial_text)

        visible_names = agents_page.get_visible_card_names()
        allure.attach(
            "\n".join(visible_names) if visible_names else "(no results)",
            name="Search results",
            attachment_type=allure.attachment_type.TEXT
        )

        matched = any(target_name.lower() == n.lower() for n in visible_names)
        assert matched, (
            f"Agent '{target_name}' was not found after searching with "
            f"middle-text substring '{partial_text}'. "
            f"Visible cards: {visible_names}"
        )
        attach_step_screenshot(driver, "Search results verified")
