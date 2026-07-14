import random

import allure
import pytest
from Webpages.my_agent_page import MyAgentsPage
from Webpages.agent_configuration_page import AgentConfigurationPage
from Utility.allure_helpers import attach_step_screenshot, attach_and_save_screenshot


@allure.feature("Agent Validation")
@allure.story("Instructions Validation")
@allure.title("Empty and whitespace-only orchestrator instructions are rejected; valid instructions succeed")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.agent_validation
def test_orchestrator_empty_instructions_validation(logged_in_driver, request):

    driver = logged_in_driver

    with allure.step("Select a random active agent and open its orchestrator card"):
        agents_page = MyAgentsPage(driver)
        agents_page.click_my_agents()

        active_agent_names = agents_page.get_active_agent_names()
        assert active_agent_names, "No active agents found in the agent card list"

        target_agent_name = random.choice(active_agent_names)
        allure.attach(target_agent_name, name="Target agent", attachment_type=allure.attachment_type.TEXT)

        agents_page.search_agent(target_agent_name)
        agents_page.click_agent_card(target_agent_name)

        config_page = AgentConfigurationPage(driver)
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

    with allure.step("Find an active agent that has at least one sub-agent node"):
        agents_page = MyAgentsPage(driver)
        agents_page.click_my_agents()

        active_agent_names = agents_page.get_active_agent_names()
        assert active_agent_names, "No active agents found in the agent card list"

        config_page = AgentConfigurationPage(driver)

        # Not every agent has a true sub-agent node (some only attach tools),
        # so search through the active agents until one with a sub-agent is found.
        candidates = active_agent_names[:]
        random.shuffle(candidates)

        target_agent_name = None
        sub_agent_data_id = None
        sub_agent_name = None

        for candidate_name in candidates:
            agents_page.search_agent(candidate_name)
            agents_page.click_agent_card(candidate_name)

            config_page.click_graph_tab()
            sub_agent_cards = config_page.get_sub_agent_cards()

            if sub_agent_cards:
                target_agent_name = candidate_name
                sub_agent_data_id, sub_agent_name = random.choice(sub_agent_cards)
                break

            config_page.go_back_to_agents()

        if not target_agent_name:
            pytest.skip("No active agent with a sub-agent node was found in the graph")

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

    with allure.step("Select a random active agent and open its orchestrator card"):
        agents_page = MyAgentsPage(driver)
        agents_page.click_my_agents()

        active_agent_names = agents_page.get_active_agent_names()
        assert active_agent_names, "No active agents found in the agent card list"

        target_agent_name = random.choice(active_agent_names)
        allure.attach(target_agent_name, name="Target agent", attachment_type=allure.attachment_type.TEXT)

        agents_page.search_agent(target_agent_name)
        agents_page.click_agent_card(target_agent_name)

        config_page = AgentConfigurationPage(driver)
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

    with allure.step("Select a random active agent and open its orchestrator card"):
        agents_page = MyAgentsPage(driver)
        agents_page.click_my_agents()

        active_agent_names = agents_page.get_active_agent_names()
        assert active_agent_names, "No active agents found in the agent card list"

        target_agent_name = random.choice(active_agent_names)
        allure.attach(target_agent_name, name="Target agent", attachment_type=allure.attachment_type.TEXT)

        agents_page.search_agent(target_agent_name)
        agents_page.click_agent_card(target_agent_name)

        config_page = AgentConfigurationPage(driver)
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
        # Neither error case actually saved anything to the server, so the agent
        # is unchanged. Restoring the field value and leaving the panel is enough.
        config_page.set_orchestrator_name(original_name)

        assert not config_page.is_name_alphanumeric_error_present(), (
            "Alphanumeric error still present after restoring the original name "
            f"for orchestrator of '{target_agent_name}'"
        )
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

    with allure.step("Select a random active agent and open its EDITOR tab"):
        agents_page = MyAgentsPage(driver)
        agents_page.click_my_agents()

        active_agent_names = agents_page.get_active_agent_names()
        assert active_agent_names, "No active agents found in the agent card list"

        target_agent_name = random.choice(active_agent_names)
        allure.attach(target_agent_name, name="Target agent", attachment_type=allure.attachment_type.TEXT)

        agents_page.search_agent(target_agent_name)
        agents_page.click_agent_card(target_agent_name)

        config_page = AgentConfigurationPage(driver)
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
    1. Open an active agent's orchestrator card.
    2. Select a model provider and note the available providers.
    3. Switch to a DIFFERENT model provider (this clears the Model selection).
    4. Do NOT select a model.
    5. Click Save → Redeploy.
    6. Assert a validation error appears and the deployment was not triggered.
    """
    driver = logged_in_driver

    with allure.step("Select a random active agent and open its orchestrator card"):
        agents_page = MyAgentsPage(driver)
        agents_page.click_my_agents()

        active_names = agents_page.get_active_agent_names()
        assert active_names, "No active agents found"

        target_name = random.choice(active_names)
        allure.attach(target_name, name="Target agent", attachment_type=allure.attachment_type.TEXT)

        agents_page.search_agent(target_name)
        agents_page.click_agent_card(target_name)

        config_page = AgentConfigurationPage(driver)
        config_page.click_graph_tab()
        config_page.open_orchestrator_card()
        attach_step_screenshot(driver, "Orchestrator card opened")

    with allure.step("Identify two different model providers"):
        providers = config_page.get_model_provider_options()
        assert len(providers) >= 2, (
            f"Only one model provider available ({providers}); "
            "need at least two to clear the model selection by switching"
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
