import os
import random
import time

import allure
import pytest

from conftest import _capture_test_artifacts
from Webpages.dashboard_page import DashboardPage
from Webpages.my_agents_page import MyAgentsPage
from Webpages.agent_build_page import AgentBuildPage
from Utility.allure_helpers import attach_step_screenshot, attach_scrolled_screenshot, attach_and_save_screenshot


# ----------------------------------------------------------------------
# One agent, created once, shared by every test below it in this module.
# Login also happens exactly once: every test here uses the session-scoped
# `logged_in_driver` fixture (login happens the first time it's requested,
# by test_create_agent since it runs first) rather than each test logging
# in independently.
#
# All automation after creation runs directly on that one agent's Build
# Agent page (EDITOR / GRAPH / CODE tabs) — tests switch tabs on the page
# they're already on rather than leaving for My Agents and searching/
# re-opening the card each time. That repeated leave-and-reopen cycle was
# both slow and the source of most of this suite's flakiness.
# ----------------------------------------------------------------------

_created_agent_name = None


def _require_created_agent_name():
    assert _created_agent_name, (
        "No agent has been created yet — test_create_agent must run first "
        "and successfully produce an agent name for the rest of this module."
    )
    return _created_agent_name


@pytest.fixture(autouse=True)
def _capture_screenshot_then_reset(request):
    """Overrides conftest.py's module-wide fixture of the same name for
    just this file: every test here operates on the SAME agent's Build
    Agent page, so — unlike other test files, where each test picks a
    different agent and a hard reset to /agents between tests is the right
    default — resetting to /agents here would force every single test to
    re-navigate, re-search, and re-open the same card again. Screenshot
    capture is preserved; only the reset-to-/agents step is dropped."""
    yield
    if "driver" in request.node.funcargs:
        return
    driver = request.node.funcargs.get("logged_in_driver")
    if driver is None:
        return
    _capture_test_artifacts(driver, request)


# ----------------------------------------------------------------------
# Agent Creation
# ----------------------------------------------------------------------

@allure.feature("Agent Management")
@allure.story("Agent Creation")
@allure.title("Create a new agent via natural language prompt and verify it appears in the list")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.agent_creation
def test_create_agent(logged_in_driver):
    # No @pytest.mark.flaky here: this test now shares the session-scoped
    # logged_in_driver browser with every other test in this module (so
    # login happens only once for the whole file), and a rerun replays the
    # function from the top on that *same*, already-navigated-forward
    # browser rather than a fresh one — by the time a rerun fires, the
    # dashboard's "Create Agent" button is no longer on screen, so the
    # retry itself fails immediately instead of helping.

    driver = logged_in_driver
    global _created_agent_name

    with allure.step("Click 'Create Agent' on the dashboard and submit a creation prompt"):
        dashboard_page = DashboardPage(driver)
        dashboard_page.click_create_agent()

        agents_page = MyAgentsPage(driver)

        agents_page.enter_prompt(
            "Create an assistant that explains Python concepts for beginners."
            "Do not ask follow-up questions,just do the basic configuration."
        )

        agents_page.click_create_agent()
        attach_step_screenshot(driver, "Creation prompt submitted")

    with allure.step("Wait for agent configuration page to load"):
        config_page = AgentBuildPage(driver)
        config_page.wait_for_agent_creation()

        assert config_page.verify_agent_configuration_page()
        print("Agent URL:", config_page.get_current_url())

        if config_page.is_duplicate_name_error_present():
            raise AssertionError(
                f"Agent Creation Failed: {config_page.get_creation_error()}"
            )
        attach_step_screenshot(driver, "Agent configuration page loaded")

    with allure.step("Wait for the agent to finish generating and deploy"):
        config_page.wait_for_creation_signal()

        # A duplicate-name collision only ever shows up here — once the LLM
        # has picked a name and the deploy itself fails — not at the earlier
        # check right after the config page loads. Every other test in this
        # module now depends on a successfully created agent, so unlike the
        # old standalone version of this test, this can no longer be waved
        # off as a non-fatal warning — fail loudly so the whole chain stops
        # here instead of every downstream test failing confusingly.
        if config_page.is_duplicate_name_error_present():
            attach_step_screenshot(driver, "Agent creation failed - duplicate name")
            raise AssertionError(
                "Agent creation hit a duplicate-name collision "
                f"({config_page.get_creation_error()}); no agent is available "
                "for the rest of this module's tests."
            )

        # Captured right here, at the moment the "Agent Deployed
        # Successfully!" toast appears — it auto-dismisses after a few
        # seconds, so read the name immediately rather than after any
        # further work.
        attach_step_screenshot(driver, "Agent build successfully")

        # get_stabilized_agent_name() (rather than a one-shot text read) waits
        # for the name to actually finish rendering/settling — and recovers
        # via a refresh if it's still stuck on "Untitled Agent" — since a raw
        # read right here can catch it before the DOM updates, silently
        # producing an empty string that every downstream test would then
        # fail to look up.
        agent_name = config_page.get_stabilized_agent_name()
        assert agent_name and agent_name != "Untitled Agent", (
            f"Agent name did not stabilize to a real name (got {agent_name!r})"
        )
        print("Generated agent name:", agent_name)
        allure.attach(agent_name, name="Generated agent name", attachment_type=allure.attachment_type.TEXT)
        _created_agent_name = agent_name
        # Deliberately no navigation away from here: every test below stays
        # on this same Build Agent page and just switches EDITOR/GRAPH/CODE
        # tabs as needed, picking up exactly where this one left off.


# ----------------------------------------------------------------------
# Agent Configuration
# ----------------------------------------------------------------------

@allure.feature("Agent Configuration")
@allure.story("I/O Types")
@allure.title("Configure audio and video I/O types on the EDITOR tab")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.knowledge_base
def test_configure_agent_io_types(logged_in_driver):

    driver = logged_in_driver
    target_agent_name = _require_created_agent_name()

    with allure.step("Configure audio and video I/O types on the EDITOR tab"):
        config_page = AgentBuildPage(driver)
        config_page.click_editor_tab()
        config_page.select_input_type_audio()
        config_page.select_output_type_audio()
        config_page.select_output_type_video()
        print(f"Configured I/O types for '{target_agent_name}'.")
        attach_step_screenshot(driver, "Audio/video I/O configured")

    with allure.step("Save so the next test doesn't inherit unsaved changes"):
        # Tests in this module no longer get a fresh page reload between
        # each other (see the module's reset-fixture override) — leaving
        # these toggles unsaved would carry them, still-pending, straight
        # into whichever test runs next.
        config_page.click_save()
        config_page.try_redeploy()
        attach_step_screenshot(driver, "I/O types saved")


@allure.feature("Agent Configuration")
@allure.story("Knowledge Base")
@allure.title("Upload a file to the knowledge base")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.knowledge_base
@pytest.mark.knowledge_base_upload
def test_upload_knowledge_base_file(logged_in_driver):

    driver = logged_in_driver
    target_agent_name = _require_created_agent_name()

    upload_file_path = os.path.abspath(
        os.path.join("Files", "Git_Reference_Guide.pdf")
    )
    file_name = os.path.basename(upload_file_path)

    with allure.step("Open the EDITOR tab"):
        config_page = AgentBuildPage(driver)
        config_page.click_editor_tab()

    with allure.step(f"Upload '{file_name}' to the knowledge base"):
        count_before_upload = config_page.count_knowledge_base_files(file_name)
        pending_count_before = config_page.submit_upload_file(upload_file_path)

        # The "File submitted for processing" toast auto-dismisses after a
        # few seconds, so it's captured here, right as it appears, instead
        # of after the (slower) wait for the upload to finish below.
        config_page.wait_for_upload_toast()
        attach_step_screenshot(driver, "File uploaded to knowledge base")

        config_page.wait_for_upload_completion(upload_file_path, pending_count_before)

        assert config_page.count_knowledge_base_files(file_name) > count_before_upload, (
            f"'{file_name}' did not appear in the knowledge base after upload"
        )
        print(f"Uploaded file for agent '{target_agent_name}':", upload_file_path)

        # The uploaded row can land below the fold of the internally
        # scrolling knowledge base panel, so scroll it into view (only if
        # it actually needs it) before capturing the completed-state screenshot.
        uploaded_row = config_page.get_knowledge_base_row(file_name)
        attach_scrolled_screenshot(driver, uploaded_row, "Upload completed")


@allure.feature("Agent Configuration")
@allure.story("Knowledge Base")
@allure.title("Cancel a delete, then delete a file from the knowledge base")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.knowledge_base
@pytest.mark.knowledge_base_delete
def test_delete_knowledge_base_file(logged_in_driver):

    driver = logged_in_driver
    target_agent_name = _require_created_agent_name()

    # A distinct file from test_upload_knowledge_base_file's own upload —
    # this test shares the same agent/knowledge base with no reset in
    # between, so reusing that test's exact filename would leave two
    # identically-named rows in the list. get_knowledge_base_row() matches
    # by filename text and picks whichever occurrence renders first, so a
    # name collision here made the scrolled screenshots unreliably target
    # the wrong (older) copy instead of the one this test just acted on.
    upload_file_path = os.path.abspath(
        os.path.join("Files", "Git_Reference_Guide_For_Delete.pdf")
    )
    file_name = os.path.basename(upload_file_path)

    with allure.step(f"Open the EDITOR tab and upload '{file_name}' to have something to delete"):
        config_page = AgentBuildPage(driver)
        config_page.click_editor_tab()

        count_before_upload = config_page.count_knowledge_base_files(file_name)
        config_page.upload_file(upload_file_path)

        assert config_page.count_knowledge_base_files(file_name) > count_before_upload, (
            f"'{file_name}' did not appear in the knowledge base after upload"
        )

    with allure.step(f"Cancel deletion of '{file_name}' — file must remain"):
        count_before_delete = config_page.count_knowledge_base_files(file_name)
        config_page.cancel_delete_knowledge_base_file(file_name)

        assert config_page.count_knowledge_base_files(file_name) == count_before_delete, (
            f"'{file_name}' was removed even though delete was cancelled"
        )
        print(f"Cancelled delete of '{file_name}'; file remains in knowledge base.")

        remaining_row = config_page.get_knowledge_base_row(file_name)
        attach_scrolled_screenshot(driver, remaining_row, "Deletion cancelled, file remains")

    with allure.step(f"Delete '{file_name}' from the knowledge base"):
        config_page.delete_knowledge_base_file(file_name)

        # The "File deleted successfully" toast auto-dismisses after a few
        # seconds, so it's captured here, right as it appears, rather than
        # after the assertions/prints below.
        config_page.wait_for_delete_toast()
        attach_step_screenshot(driver, "File deleted from knowledge base")

        assert config_page.count_knowledge_base_files(file_name) == count_before_upload, (
            f"'{file_name}' was not removed from the knowledge base after delete"
        )
        print(f"Deleted file '{file_name}' from knowledge base for agent '{target_agent_name}'.")


@allure.feature("Agent Configuration")
@allure.story("Tool Attachment")
@allure.title("Attach tools to orchestrator, redeploy, and verify persistence after navigating away")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.tool_attachment
def test_attach_tool_to_orchestrator(logged_in_driver, request):

    driver = logged_in_driver
    target_agent_name = _require_created_agent_name()

    tool_names = ["Convert_Language", "Addition"]

    with allure.step("Open a random agent card on the GRAPH tab and set model"):
        config_page = AgentBuildPage(driver)
        config_page.click_graph_tab()

        card_names = config_page.get_agent_card_names()
        assert card_names, f"No configurable agent cards found in the graph for '{target_agent_name}'"

        orchestrator_card_name = random.choice(card_names)
        allure.attach(orchestrator_card_name, name="Orchestrator card", attachment_type=allure.attachment_type.TEXT)

        config_page.open_agent_card(orchestrator_card_name)

        # This test only needs *some* provider to proceed to tool attachment
        # (which is what it's actually testing) — it doesn't depend on which
        # one. A freshly created agent may only have a single provider
        # available (unlike the varied, manually-configured pre-existing
        # agents this test used to pick from at random), so pick whichever
        # is offered rather than assuming "Bedrock" specifically exists.
        providers = config_page.get_model_provider_options()
        assert providers, f"No model providers available for '{orchestrator_card_name}'"
        model_provider = providers[0]
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

        assert config_page.is_redeploy_success_toast_present(), (
            f"Expected 'Agent Redeployed Successfully!' toast after redeploying '{target_agent_name}'"
        )
        print(f"Confirmed 'Agent Redeployed Successfully!' toast shown for '{target_agent_name}'.")
        # Saved as its own file (not just an Allure step attachment) since
        # the "navigate away and back" step below leaves the plain
        # Screenshot/Passed capture showing a different, later state.
        attach_and_save_screenshot(driver, request, "Agent redeployed successfully")

    with allure.step("Navigate away and back to confirm tools persisted on the backend"):
        # This is the one deliberate exception to "stay on this agent's Build
        # page": the whole point here is confirming the tool attachment
        # survived a real navigate-away-and-back cycle, so leaving via My
        # Agents and re-opening the card is intentional, not incidental.
        # Backend indexing can lag behind the redeploy confirmation, so retry.
        agents_page = MyAgentsPage(driver)
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


# ----------------------------------------------------------------------
# Agent Validation
# ----------------------------------------------------------------------

@allure.feature("Agent Validation")
@allure.story("Instructions Validation")
@allure.title("Empty and whitespace-only orchestrator instructions are rejected; valid instructions succeed")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.agent_validation
def test_orchestrator_empty_instructions_validation(logged_in_driver, request):

    driver = logged_in_driver
    target_agent_name = _require_created_agent_name()

    with allure.step("Open its orchestrator card"):
        config_page = AgentBuildPage(driver)
        config_page.click_graph_tab()
        config_page.open_orchestrator_card()
        attach_step_screenshot(driver, "Orchestrator card opened")

    with allure.step("Case 1 — Empty instructions are rejected on redeploy"):
        # The Instructions field's eye icon opens a separate dialog with its own
        # textarea; clearing it there and closing the dialog updates the panel.
        config_page.click_instructions_eye_toggle()
        config_page.clear_instructions()

        config_page.click_save()
        config_page.click_redeploy()

        assert config_page.is_instructions_empty_error_present(), (
            "Expected 'Orchestrator agent instructions cannot be empty' error "
            f"after clearing instructions and redeploying orchestrator for '{target_agent_name}'"
        )
        print(f"Confirmed empty-instructions validation error for orchestrator of '{target_agent_name}'.")
        # Saved as its own file since Case 2/Recovery below leave the plain
        # Screenshot/Passed capture showing a later, different state.
        attach_and_save_screenshot(driver, request, "Case 1: empty instructions error shown")

        config_page.close_error_toast()
        # The side panel closes once the toast clears, so the orchestrator card
        # has to be reopened before the Instructions dialog can be reached again.
        config_page.open_orchestrator_card()

    with allure.step("Case 2 — Whitespace-only instructions are rejected on redeploy"):
        # Whitespace-only instructions carry no real content, so the same
        # validation should reject them rather than treating the array as
        # non-empty just because it has a blank line.
        config_page.click_instructions_eye_toggle()
        config_page.set_instructions_text("   ")

        config_page.click_save()
        config_page.click_redeploy()

        assert config_page.is_instructions_empty_error_present(), (
            "Expected 'Orchestrator agent instructions cannot be empty' error "
            f"after saving whitespace-only instructions for orchestrator of '{target_agent_name}'"
        )
        print(f"Confirmed whitespace-only instructions are rejected for orchestrator of '{target_agent_name}'.")
        # Saved as its own file since Recovery below leaves the plain
        # Screenshot/Passed capture showing the later, successful state.
        attach_and_save_screenshot(driver, request, "Case 2: whitespace-only instructions error shown")

        config_page.close_error_toast()
        config_page.open_orchestrator_card()

    with allure.step("Recovery — Valid instructions allow successful redeploy"):
        # Restoring real instructions and redeploying should clear the
        # validation error and succeed.
        config_page.click_instructions_eye_toggle()
        config_page.set_instructions_text("Respond directly to user queries.")

        config_page.click_save()
        config_page.try_redeploy()

        assert not config_page.is_instructions_empty_error_present(), (
            "Empty-instructions error still present after restoring valid "
            f"instructions and redeploying orchestrator of '{target_agent_name}'"
        )
        print(f"Confirmed orchestrator of '{target_agent_name}' redeploys successfully once valid instructions are restored.")
        attach_step_screenshot(driver, "Recovery: valid instructions redeployed")


@allure.feature("Agent Validation")
@allure.story("Instructions Validation")
@allure.title("Empty sub-agent instructions are rejected on redeploy")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.agent_validation
def test_sub_agent_empty_instructions_validation(logged_in_driver):

    driver = logged_in_driver
    target_agent_name = _require_created_agent_name()

    with allure.step("Look for a sub-agent node in its graph"):
        config_page = AgentBuildPage(driver)
        config_page.click_graph_tab()
        sub_agent_cards = config_page.get_sub_agent_cards()

        # Not every agent has a true sub-agent node (some only attach tools
        # to the orchestrator) — the created agent may or may not have one,
        # depending on how it was built.
        if not sub_agent_cards:
            pytest.skip(f"Created agent '{target_agent_name}' has no sub-agent node in its graph")

        sub_agent_data_id, sub_agent_name = random.choice(sub_agent_cards)
        allure.attach(
            f"Agent: {target_agent_name}\nSub-agent: {sub_agent_name} ({sub_agent_data_id})",
            name="Target sub-agent",
            attachment_type=allure.attachment_type.TEXT
        )
        attach_step_screenshot(driver, "Sub-agent node found")

    with allure.step(f"Clear instructions for sub-agent '{sub_agent_name}' and attempt redeploy"):
        # Open by data-id rather than text to avoid matching the same name that
        # appears in the orchestrator card's description text.
        config_page.open_card_by_data_id(sub_agent_data_id)

        # Capture the original instructions from the modal textarea before clearing
        # so they can be restored at the end (the same browser is reused across tests).
        config_page.click_instructions_eye_toggle()
        original_instructions = config_page.get_instructions_modal_text()
        config_page.clear_instructions()

        config_page.click_save()
        config_page.click_redeploy()

        assert config_page.is_agent_instructions_empty_error_present(sub_agent_name), (
            f"Expected 'Agent \"{sub_agent_name}\" instructions cannot be empty' error "
            f"after clearing instructions and redeploying sub-agent of '{target_agent_name}'"
        )
        print(f"Confirmed empty-instructions validation error for sub-agent '{sub_agent_name}' of '{target_agent_name}'.")
        attach_step_screenshot(driver, "Sub-agent empty instructions error shown")
        config_page.close_error_toast()

    with allure.step(f"Restore original instructions for sub-agent '{sub_agent_name}'"):
        # Restore the original instructions so the agent is left in a clean state
        # for subsequent tests that share the same browser session.
        config_page.open_card_by_data_id(sub_agent_data_id)
        config_page.click_instructions_eye_toggle()
        config_page.set_instructions_text(original_instructions)
        config_page.click_save()
        config_page.try_redeploy()

        print(f"Restored original instructions for sub-agent '{sub_agent_name}'.")
        attach_step_screenshot(driver, "Sub-agent instructions restored")


@allure.feature("Agent Validation")
@allure.story("Instructions UI")
@allure.title("Closing the instructions dialog without edits leaves content unchanged")
@allure.severity(allure.severity_level.MINOR)
@pytest.mark.agent_validation
def test_instructions_modal_close_without_changes_preserves_content(logged_in_driver):

    driver = logged_in_driver
    target_agent_name = _require_created_agent_name()

    with allure.step("Open its orchestrator card"):
        config_page = AgentBuildPage(driver)
        config_page.click_graph_tab()
        config_page.open_orchestrator_card()
        attach_step_screenshot(driver, "Orchestrator card opened")

    with allure.step("Record existing instructions then open and immediately close the dialog"):
        original_instructions = config_page.get_instructions_preview_text()
        assert original_instructions and "No instructions yet" not in original_instructions, (
            f"Orchestrator of '{target_agent_name}' has no existing instructions to verify against"
        )
        allure.attach(original_instructions, name="Original instructions", attachment_type=allure.attachment_type.TEXT)

        # Opening the dialog and closing it without typing anything should leave
        # the existing instructions untouched.
        config_page.click_instructions_eye_toggle()
        config_page.close_instructions_modal()
        attach_step_screenshot(driver, "Dialog opened and closed without edits")

    with allure.step("Verify instructions preview is unchanged after closing the dialog"):
        unchanged_instructions = config_page.get_instructions_preview_text()

        assert unchanged_instructions == original_instructions, (
            "Instructions changed after opening and closing the dialog without edits "
            f"for orchestrator of '{target_agent_name}': "
            f"before='{original_instructions}', after='{unchanged_instructions}'"
        )
        print(f"Confirmed closing the Instructions dialog without edits preserves content for orchestrator of '{target_agent_name}'.")
        attach_step_screenshot(driver, "Instructions confirmed unchanged")


@allure.feature("Agent Validation")
@allure.story("Name Validation")
@allure.title("Empty and non-alphanumeric orchestrator names are rejected; original name restores cleanly")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.agent_validation
def test_orchestrator_name_validation(logged_in_driver):

    driver = logged_in_driver
    target_agent_name = _require_created_agent_name()

    with allure.step("Open its orchestrator card"):
        config_page = AgentBuildPage(driver)
        config_page.click_graph_tab()
        config_page.open_orchestrator_card()

        original_name = config_page.get_orchestrator_name()
        allure.attach(original_name, name="Original orchestrator name", attachment_type=allure.attachment_type.TEXT)
        attach_step_screenshot(driver, "Orchestrator card opened")

    with allure.step("Case 1 — Empty name is rejected on redeploy"):
        # Save opens a dropdown; clicking Redeploy from it triggers server-side
        # validation. With an empty name the server blocks the action and returns
        # a validation toast — nothing is actually deployed.
        config_page.set_orchestrator_name("")
        config_page.click_save()
        config_page.click_redeploy()

        assert config_page.is_name_empty_error_present(), (
            "Expected 'Orchestrator agent name cannot be empty' error after "
            f"clearing the name field for '{target_agent_name}'"
        )
        print(f"Confirmed empty-name validation error for orchestrator of '{target_agent_name}'.")
        attach_step_screenshot(driver, "Case 1: empty name error shown")

        config_page.close_error_toast()
        config_page.open_orchestrator_card()

    with allure.step("Case 2 — Non-alphanumeric name triggers inline validation error"):
        # The inline validator fires on input; the error is visible without
        # needing to attempt a save.
        config_page.set_orchestrator_name("Invalid@Name!")

        assert config_page.is_name_alphanumeric_error_present(), (
            "Expected 'Name can only contain alphanumeric characters.' inline error "
            f"after entering a name with special characters for '{target_agent_name}'"
        )
        print(f"Confirmed non-alphanumeric name triggers inline error for orchestrator of '{target_agent_name}'.")
        attach_step_screenshot(driver, "Case 2: non-alphanumeric name error shown")

    with allure.step(f"Restore original name '{original_name}' and verify no validation errors"):
        # Neither error case actually saved anything to the server, so the
        # agent is unchanged there — but the field itself still shows
        # whatever was last typed into it, and this module no longer gets a
        # fresh page reload between tests, so save explicitly to make sure
        # the next test doesn't inherit an unsaved orchestrator-name field.
        config_page.set_orchestrator_name(original_name)

        assert not config_page.is_name_alphanumeric_error_present(), (
            "Alphanumeric error still present after restoring the original name "
            f"for orchestrator of '{target_agent_name}'"
        )
        config_page.click_save()
        config_page.try_redeploy()
        print(f"Confirmed original name restored cleanly for orchestrator of '{target_agent_name}' with no validation errors.")
        attach_step_screenshot(driver, "Original name restored")


@allure.feature("Agent Validation")
@allure.story("Name Validation")
@allure.title("Empty, whitespace-only, and non-alphanumeric agent names are rejected; original name restores cleanly")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.agent_validation
def test_agent_name_validation(logged_in_driver, request):
    """
    Validates the top-level agent name field in the EDITOR tab's Details
    panel — distinct from the orchestrator card's own name field covered by
    test_orchestrator_name_validation above.
    """
    driver = logged_in_driver
    target_agent_name = _require_created_agent_name()

    with allure.step("Open its EDITOR tab"):
        config_page = AgentBuildPage(driver)
        config_page.click_editor_tab()
        attach_step_screenshot(driver, "Editor tab opened")

    with allure.step("Case 1 — Empty agent name is rejected on redeploy"):
        # Save opens a dropdown; clicking Redeploy from it triggers server-side
        # validation. With an empty name the server blocks the action and
        # returns a validation toast — nothing is actually deployed.
        config_page.click_agent_name_edit()
        config_page.set_agent_name("")
        config_page.click_save()
        config_page.click_redeploy()

        assert config_page.is_agent_name_empty_error_present(), (
            "Expected 'Agent name cannot be empty' error after clearing the "
            f"agent name for '{target_agent_name}'"
        )
        print(f"Confirmed empty-name validation error for agent '{target_agent_name}'.")
        attach_and_save_screenshot(driver, request, "Case 1 - empty name error")

        config_page.close_error_toast()

    with allure.step("Case 2 — Whitespace-only agent name is rejected on redeploy"):
        # Whitespace carries no real content, so the same validation should
        # reject it rather than treating it as a non-empty name.
        config_page.click_agent_name_edit()
        config_page.set_agent_name("   ")
        config_page.click_save()
        config_page.click_redeploy()

        assert config_page.is_agent_name_empty_error_present(), (
            "Expected 'Agent name cannot be empty' error after setting a "
            f"whitespace-only agent name for '{target_agent_name}'"
        )
        print(f"Confirmed whitespace-only agent name is rejected for '{target_agent_name}'.")
        attach_and_save_screenshot(driver, request, "Case 2 - whitespace name error")

        config_page.close_error_toast()

    with allure.step("Case 3 — Non-alphanumeric agent name triggers inline validation error"):
        # The inline validator fires on input; the error is visible without
        # needing to attempt a save.
        config_page.click_agent_name_edit()
        config_page.set_agent_name("Invalid@Name!")

        assert config_page.is_name_alphanumeric_error_present(), (
            "Expected 'Name can only contain alphanumeric characters.' inline error "
            f"after entering a name with special characters for '{target_agent_name}'"
        )
        print(f"Confirmed non-alphanumeric name triggers inline error for agent '{target_agent_name}'.")
        attach_and_save_screenshot(driver, request, "Case 3 - alphanumeric name error")

    with allure.step(f"Restore original name '{target_agent_name}' and verify no validation errors"):
        config_page.set_agent_name(target_agent_name)
        config_page.click_save()

        # Restoring the name to its original, already-deployed value means
        # there's nothing actually different to redeploy, so Redeploy stays
        # disabled here — unlike Cases 1/2 above, which set a genuinely
        # different (invalid) value. try_redeploy() clicks it if available
        # and otherwise dismisses the dropdown instead of forcing a click on
        # a disabled button.
        config_page.try_redeploy()

        assert not config_page.is_agent_name_empty_error_present(timeout=5), (
            f"Empty-name error still present after restoring the original name for '{target_agent_name}'"
        )
        print(f"Confirmed agent '{target_agent_name}' name restored cleanly with no validation errors.")
        attach_step_screenshot(driver, "Original name restored and redeployed")


@allure.feature("Agent Validation")
@allure.story("Model Validation")
@allure.title("Redeployment is blocked with a validation error when the Model field is empty")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.agent_validation
def test_model_field_required_on_redeploy(logged_in_driver, request):
    """
    Bug: Switching the Model Provider clears the Model field, but clicking Redeploy
    still proceeds and deploys the agent without a model selected.
    Expected: System must block redeployment and show a validation error when Model is empty.

    Steps:
    1. Open the created agent's orchestrator card.
    2. Select a model provider and note the available providers.
    3. Switch to a DIFFERENT model provider (this clears the Model selection).
    4. Do NOT select a model.
    5. Click Save → Redeploy.
    6. Assert a validation error appears and the deployment was not triggered.
    """
    driver = logged_in_driver
    target_name = _require_created_agent_name()

    with allure.step("Open its orchestrator card"):
        config_page = AgentBuildPage(driver)
        config_page.click_graph_tab()
        config_page.open_orchestrator_card()
        attach_step_screenshot(driver, "Orchestrator card opened")

    with allure.step("Identify two different model providers"):
        providers = config_page.get_model_provider_options()
        # A freshly created agent may only have one provider available
        # (unlike the varied, manually-configured pre-existing agents this
        # test used to pick from at random) — this test's whole premise is
        # switching providers to clear the Model field, which isn't
        # meaningful with only one choice, so skip rather than fail.
        if len(providers) < 2:
            pytest.skip(
                f"Created agent's orchestrator only offers one model provider "
                f"({providers}); need at least two to test clearing the model "
                f"field by switching providers"
            )
        provider_a, provider_b = providers[0], providers[1]
        allure.attach(
            f"Switch from '{provider_a}' → '{provider_b}' to clear model field",
            name="Provider switch",
            attachment_type=allure.attachment_type.TEXT
        )
        attach_step_screenshot(driver, "Model providers identified")

    with allure.step(f"Select '{provider_a}', then switch to '{provider_b}' to clear model"):
        config_page.select_model_provider(provider_a)
        config_page.select_model_provider(provider_b)
        # Model dropdown is now empty — do NOT call select_random_model()
        attach_step_screenshot(driver, "Model field cleared by provider switch")

    with allure.step("Attempt to Save and Redeploy with empty model field"):
        config_page.click_save()
        # Click the Redeploy button directly (do NOT use click_redeploy which
        # auto-confirms the dialog, as that would actually deploy the agent).
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.common.action_chains import ActionChains

        WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable(config_page.redeploy_button)
        ).click()

        # If the confirm dialog appears, validation failed to block the deploy.
        # Press Escape immediately to cancel without actually deploying.
        if config_page.is_deploy_confirm_visible(timeout=5):
            attach_step_screenshot(driver, "Bug: deploy dialog appeared with empty model")
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            assert False, (
                f"Bug confirmed: The 'Continue?' deploy dialog appeared for agent "
                f"'{target_name}' even though the Model field was empty. "
                f"System should block redeployment and show a validation error."
            )

        assert config_page.is_model_required_error_present(), (
            f"Expected a validation error about the empty Model field for agent "
            f"'{target_name}', but no model-related error toast was shown."
        )
        print(f"Confirmed: redeployment blocked with model validation error for '{target_name}'.")
        # Saved as its own file (not just an Allure step attachment) since
        # the recovery step below leaves the plain Screenshot/Passed capture
        # showing the restored, error-free state instead of this one.
        attach_and_save_screenshot(driver, request, "Model required error shown")

    with allure.step("Restore original model provider and model"):
        config_page.close_error_toast()
        config_page.open_orchestrator_card()
        config_page.select_model_provider(provider_a)
        config_page.select_random_model()
        config_page.click_save()
        config_page.try_redeploy()
        print(f"Restored original provider '{provider_a}' and model for '{target_name}'.")
        attach_step_screenshot(driver, "Original provider and model restored")


# ----------------------------------------------------------------------
# Interact Window
# ----------------------------------------------------------------------
# The "Interact" button (top bar, alongside Undo/Save) slides in a
# right-hand panel to chat with the created agent directly from the Build
# page — separate from the always-present "AI Copilot" panel (which helps
# build/debug the agent, not talk to it). Every test here opens the panel
# via click_interact() and closes it via close_interact_panel() at the end,
# so each test starts from the same clean, closed state the previous one
# left behind — consistent with this file's "stay on the Build page,
# nothing resets between tests" design.

@allure.feature("Agent Interaction")
@allure.story("Interact Window")
@allure.title("Interact window opens from the Build page and can be closed")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.interact
def test_interact_window_opens(logged_in_driver):
    driver = logged_in_driver
    target_agent_name = _require_created_agent_name()

    with allure.step("Click 'Interact' and verify the window opens"):
        config_page = AgentBuildPage(driver)
        config_page.click_interact()

        assert config_page.is_interact_panel_open(), (
            f"Interact window did not open for agent '{target_agent_name}'"
        )
        print(f"Interact window opened for '{target_agent_name}'.")
        attach_step_screenshot(driver, "Interact window opened")

    with allure.step("Close the Interact window"):
        config_page.close_interact_panel()
        assert config_page.is_interact_panel_closed(timeout=10), (
            "Interact window did not close after clicking the close button"
        )
        print("Interact window closed.")
        attach_step_screenshot(driver, "Interact window closed")


@allure.feature("Agent Interaction")
@allure.story("Interact Window")
@allure.title("Message input field in the Interact window accepts typed text")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.interact
def test_interact_message_input_field(logged_in_driver):
    driver = logged_in_driver
    target_agent_name = _require_created_agent_name()
    message = "Hello, this is an automated test message."

    with allure.step("Open the Interact window and type into the message field"):
        config_page = AgentBuildPage(driver)
        config_page.click_interact()
        assert config_page.is_interact_panel_open(), "Interact window did not open"

        config_page.enter_interact_message(message)
        assert config_page.get_interact_message_value() == message, (
            f"Message input did not reflect the typed text for agent '{target_agent_name}'"
        )
        print(f"Confirmed message input accepts typed text for '{target_agent_name}'.")
        attach_step_screenshot(driver, "Text entered in message field")

    with allure.step("Close the Interact window"):
        config_page.close_interact_panel()


@allure.feature("Agent Interaction")
@allure.story("Interact Window")
@allure.title("A typed query can be submitted and the agent responds")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.interact
def test_interact_query_submission(logged_in_driver):
    driver = logged_in_driver
    target_agent_name = _require_created_agent_name()

    with allure.step("Open the Interact window and submit a query"):
        config_page = AgentBuildPage(driver)
        config_page.click_interact()
        assert config_page.is_interact_panel_open(), "Interact window did not open"

        config_page.enter_interact_message("Please give me a short example response.")
        assert config_page.is_interact_send_button_enabled(), (
            "Send button should be enabled once real text is entered"
        )
        config_page.click_interact_send()
        attach_step_screenshot(driver, "Query submitted")

    with allure.step("Wait for the agent to respond"):
        config_page.wait_for_interact_response()
        # A successful submission clears the input back to empty.
        assert config_page.get_interact_message_value() == "", (
            "Message input was not cleared after submitting the query"
        )
        print(f"Confirmed query was submitted and agent responded for '{target_agent_name}'.")
        attach_step_screenshot(driver, "Agent responded")

    with allure.step("Close the Interact window"):
        config_page.close_interact_panel()


@allure.feature("Agent Interaction")
@allure.story("Interact Window")
@allure.title("Empty message cannot be submitted in the Interact window")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.interact
def test_interact_empty_message_validation(logged_in_driver):
    driver = logged_in_driver
    target_agent_name = _require_created_agent_name()

    with allure.step("Open the Interact window and leave the input blank"):
        config_page = AgentBuildPage(driver)
        config_page.click_interact()
        assert config_page.is_interact_panel_open(), "Interact window did not open"

        assert not config_page.is_interact_send_button_enabled(), (
            f"Send button should stay disabled for an empty message ('{target_agent_name}')"
        )
        print(f"Confirmed Send is disabled for an empty message ('{target_agent_name}').")
        attach_step_screenshot(driver, "Send disabled for empty input")

    with allure.step("Close the Interact window"):
        config_page.close_interact_panel()


@allure.feature("Agent Interaction")
@allure.story("Interact Window")
@allure.title("Whitespace-only message cannot be submitted in the Interact window")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.interact
def test_interact_spaces_only_validation(logged_in_driver):
    driver = logged_in_driver
    target_agent_name = _require_created_agent_name()

    with allure.step("Open the Interact window and enter spaces only"):
        config_page = AgentBuildPage(driver)
        config_page.click_interact()
        assert config_page.is_interact_panel_open(), "Interact window did not open"

        config_page.enter_interact_message("    ")
        assert not config_page.is_interact_send_button_enabled(), (
            f"Send button should stay disabled for a whitespace-only message ('{target_agent_name}')"
        )
        print(f"Confirmed Send is disabled for a whitespace-only message ('{target_agent_name}').")
        attach_step_screenshot(driver, "Send disabled for whitespace-only input")

    with allure.step("Close the Interact window"):
        config_page.close_interact_panel()


@allure.feature("Agent Interaction")
@allure.story("Interact Window")
@allure.title("'New Chat' starts a fresh conversation in the Interact window")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.interact
def test_interact_new_chat_functionality(logged_in_driver):
    driver = logged_in_driver
    target_agent_name = _require_created_agent_name()

    with allure.step("Open the Interact window and send a message"):
        config_page = AgentBuildPage(driver)
        config_page.click_interact()
        assert config_page.is_interact_panel_open(), "Interact window did not open"

        config_page.enter_interact_message("Tell me something interesting.")
        config_page.click_interact_send()
        config_page.wait_for_interact_response()
        attach_step_screenshot(driver, "Conversation started")

    with allure.step("Click 'New Chat' and verify a fresh conversation starts"):
        config_page.click_interact_new_chat()
        assert config_page.is_interact_welcome_screen_present(), (
            f"Interact window did not return to its welcome screen after 'New Chat' "
            f"for agent '{target_agent_name}'"
        )
        print(f"Confirmed 'New Chat' started a fresh conversation for '{target_agent_name}'.")
        attach_step_screenshot(driver, "New chat started")

    with allure.step("Close the Interact window"):
        config_page.close_interact_panel()


@allure.feature("Agent Interaction")
@allure.story("Interact Window")
@allure.title("A file can be attached in the Interact window")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.interact
def test_interact_file_attachment_upload(logged_in_driver):
    driver = logged_in_driver
    target_agent_name = _require_created_agent_name()
    pdf_path = os.path.abspath(os.path.join("Files", "sample_test.pdf"))
    file_name = os.path.basename(pdf_path)

    with allure.step("Open the Interact window and attach a file"):
        config_page = AgentBuildPage(driver)
        config_page.click_interact()
        assert config_page.is_interact_panel_open(), "Interact window did not open"

        config_page.upload_interact_file(pdf_path)
        assert config_page.is_interact_file_attached(file_name), (
            f"Uploaded file '{file_name}' did not appear as attached for agent '{target_agent_name}'"
        )
        print(f"Confirmed '{file_name}' uploaded successfully for '{target_agent_name}'.")
        attach_step_screenshot(driver, "File attached")

    with allure.step("Close the Interact window"):
        config_page.close_interact_panel()