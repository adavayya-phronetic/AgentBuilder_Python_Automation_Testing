import os
import random
import time

import allure
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException


class AgentBuildPage:

    def __init__(self, driver):
        self.driver = driver
        # Routine UI interactions (clicks, tab switches, dropdowns) should
        # resolve within seconds; genuinely slow operations (LLM name
        # generation, deploy confirmation) use their own longer, explicit
        # WebDriverWait instances below instead of this default, so this
        # doesn't need to be — and shouldn't be — minutes long. A too-long
        # default here means any single transient hiccup on an ordinary
        # click silently retries for minutes before failing, which looks
        # exactly like the test being "stuck" on the same page.
        self.wait = WebDriverWait(driver, 30)

        self.status_badge = (
            By.XPATH,
            "//div[contains(@class,'tracking-wider')]"
        )

        self.agent_name = (
            By.XPATH,
            "//p[contains(@class,'font-semibold') and contains(@class,'truncate')]"
        )

        self.back_button = (
            By.XPATH,
            "//*[self::a or self::button][normalize-space()='Back']"
        )

        self.agent_exists_error = (
            By.XPATH,
            "//*[contains(text(),'Agent with this name already exists')]"
        )

        # Fires once the agent finishes generating and is auto-deployed —
        # the clearest completion signal, and it auto-dismisses after a few
        # seconds, so callers must screenshot right when it's detected
        # rather than after any further processing.
        self.deploy_success_toast = (
            By.XPATH,
            "//*[contains(text(),'Agent Deployed Successfully')]"
        )

        self.leave_page_button = (
            By.XPATH,
            "//button[normalize-space()='Leave Page']"
        )

        self.tool_search_error = (
            By.XPATH,
            "//*[contains(text(),'I encountered an issue while searching for supporting tools')]"
        )

        self.editor_tab = (
            By.XPATH,
            "//*[self::button or self::a][normalize-space()='EDITOR']"
        )

        # --- Top-level agent name (EDITOR tab, Details panel) ---
        # Distinct from orchestrator_name_input below: this is the agent's
        # own name (avatar + name, shown at the top of Details), reached by
        # clicking directly on the name text rather than opening a card.
        self.agent_name_edit_trigger = (
            By.XPATH,
            "//div[@title='Click to edit']"
        )

        self.agent_name_input = (
            By.XPATH,
            "//input[contains(@class,'capitalize')]"
        )

        # Deliberately without "Orchestrator" — that's a different message
        # for a different field (see name_empty_error below).
        self.agent_name_empty_error = (
            By.XPATH,
            "//*[contains(text(),'Agent name cannot be empty')]"
        )

        self.instructions_empty_error = (
            By.XPATH,
            "//*[contains(text(),'Orchestrator agent instructions cannot be empty')]"
        )

        self.orchestrator_name_input = (
            By.XPATH,
            "//input[@placeholder='Enter agent name']"
        )

        self.name_empty_error = (
            By.XPATH,
            "//*[contains(text(),'Orchestrator agent name cannot be empty')]"
        )

        self.name_alphanumeric_error = (
            By.XPATH,
            "//*[contains(text(),'Name can only contain alphanumeric characters')]"
        )

        self.error_toast_close_button = (
            By.XPATH,
            "//button[@aria-label='close' and contains(@class,'Toastify__close-button')]"
        )

        self.instructions_eye_button = (
            By.XPATH,
            "//*[normalize-space()='Instructions']/following::button[1]"
        )

        # The eye icon opens a separate Radix dialog with its own textarea
        # and a "Close" (X) button rather than toggling an inline editor.
        self.instructions_modal_textarea = (
            By.XPATH,
            "//div[@role='dialog']//textarea"
        )

        self.instructions_modal_close_button = (
            By.XPATH,
            "//div[@role='dialog']//button[.//span[normalize-space()='Close']]"
        )

        self.input_type_audio_button = (
            By.ID,
            "agent-definition-input-audio"
        )

        self.output_type_audio_button = (
            By.ID,
            "agent-definition-output-audio"
        )

        self.output_type_video_button = (
            By.ID,
            "agent-definition-output-video"
        )

        self.upload_to_knowledge_base_button = (
            By.XPATH,
            "//button[@title='Upload file to knowledge base']"
        )

        self.knowledge_base_file_input = (
            By.XPATH,
            "//input[@type='file' and contains(@accept,'.pdf')]"
        )

        self.pending_upload_status = (
            By.XPATH,
            "//span[normalize-space()='Pending']"
        )

        self.knowledge_base_row_xpath = (
            "//span[contains(@class,'truncate') and normalize-space()='{file_name}']"
            "/ancestor::div[contains(@class,'group') and contains(@class,'relative')][1]"
        )

        self.knowledge_base_heading = (
            By.XPATH,
            "//*[self::h2 or self::h3 or self::p or self::span][normalize-space()='Knowledge Base']"
        )

        # Both of these auto-dismiss after a few seconds (react-toastify),
        # so callers must screenshot immediately after detecting them rather
        # than doing further work first — see wait_for_upload_toast() /
        # wait_for_delete_toast().
        self.file_upload_toast = (
            By.XPATH,
            "//*[contains(text(),'File submitted for processing')]"
        )

        self.file_delete_toast = (
            By.XPATH,
            "//*[contains(text(),'File deleted successfully')]"
        )

        self.graph_tab = (
            By.XPATH,
            "//*[self::button or self::a][normalize-space()='GRAPH']"
        )

        self.graph_node = (
            By.CSS_SELECTOR,
            ".react-flow__node"
        )

        self.orchestrator_node = (
            By.CSS_SELECTOR,
            ".react-flow__node[data-id='orchestrator']"
        )

        self.sub_agent_node = (
            By.CSS_SELECTOR,
            ".react-flow__node[data-id^='agent-']"
        )

        self.instructions_preview = (
            By.XPATH,
            "//*[normalize-space()='Instructions']/following::div[contains(@class,'whitespace-pre-wrap')][1]"
        )

        self.model_provider_combobox = (
            By.XPATH,
            "//button[@role='combobox']"
        )

        self.model_field_button = (
            By.XPATH,
            "//label[starts-with(normalize-space(.),'Model') "
            "and not(starts-with(normalize-space(.),'Model Provider'))]"
            "/following::button[1]"
        )

        self.model_option_names = (
            By.XPATH,
            "//div[@role='option']//p[contains(@class,'font-semibold')]"
        )

        self.tools_select_input = (
            By.XPATH,
            "//*[normalize-space()='Tools']/following::input[contains(@class,'react-select__input')][1]"
        )

        self.tools_selected_chips = (
            By.XPATH,
            "//*[normalize-space()='Tools']/following::div[contains(@class,'react-select__multi-value__label')]"
        )

        self.save_button = (
            By.XPATH,
            "//button[normalize-space()='Save']"
        )

        self.redeploy_button = (
            By.XPATH,
            "//button[normalize-space()='Redeploy']"
        )

        self.publish_button = (
            By.XPATH,
            "//button[normalize-space()='Publish']"
        )

        self.modal_overlay = (
            By.XPATH,
            "//div[@data-state='open' and contains(@class,'fixed') and contains(@class,'inset-0')]"
        )

        # Auto-dismisses after a few seconds like every other toast in this
        # app — callers must screenshot immediately after detecting it.
        self.redeploy_success_toast = (
            By.XPATH,
            "//*[contains(@class,'Toastify__toast--success') and contains(.,'Redeployed')]"
        )

        self.deploy_confirm_button = (
            By.XPATH,
            "//div[@role='dialog']//button[normalize-space()='Continue']"
        )

        # The "Interact" button (top bar, alongside Undo/Save) slides in a
        # right-hand panel to chat with the agent directly from the Build
        # page — a separate feature from the always-present "AI Copilot"
        # panel on the left (which helps build/debug the agent itself, not
        # talk to it). Every locator below is scoped to this panel's own
        # fixed/right-0/z-50 container so it can never match the AI
        # Copilot's similarly-shaped message input/send/attach controls.
        self.interact_button = (
            By.XPATH,
            "//span[normalize-space()='Interact']/ancestor::button[1]"
        )

        self._interact_panel_prefix = (
            "//div[contains(@class,'fixed') and contains(@class,'right-0') "
            "and contains(@class,'z-50')]"
        )

        # svg is matched via *[local-name()='svg'] rather than a bare svg
        # element test — chromedriver's XPath evaluator is namespace-aware
        # for SVG's foreign namespace, so an unprefixed `svg` step silently
        # matches nothing even though the element is clearly there in the
        # DOM (confirmed: this was the actual cause of close/attach button
        # lookups timing out).
        self.interact_close_button = (
            By.XPATH,
            f"{self._interact_panel_prefix}//button[.//*[local-name()='svg' "
            "and contains(@class,'lucide-x')]]"
        )

        self.interact_message_input = (
            By.XPATH,
            "//textarea[@placeholder='Type your message...']"
        )

        self.interact_send_button = (
            By.XPATH,
            f"{self._interact_panel_prefix}//button[contains(@class,'bg-blue-600') "
            "and contains(@class,'rounded-lg')]"
        )

        self.interact_attach_button = (
            By.XPATH,
            f"{self._interact_panel_prefix}//button[.//*[local-name()='svg' "
            "and contains(@class,'lucide-paperclip')]]"
        )

        self.interact_file_input = (
            By.XPATH,
            f"{self._interact_panel_prefix}//input[@type='file']"
        )

        self.interact_new_chat_button = (
            By.XPATH,
            f"{self._interact_panel_prefix}//button[normalize-space()='New Chat']"
        )

        self.interact_welcome_text = (
            By.XPATH,
            f"{self._interact_panel_prefix}//p[contains(@class,'text-2xl')]"
        )

    @allure.step("Wait for agent creation to complete")
    def wait_for_agent_creation(self):
        self.wait.until(
            EC.url_contains("/build-agent/configure")
        )

    def verify_agent_configuration_page(self):
        return "/build-agent/configure" in self.driver.current_url

    def get_current_url(self):
        return self.driver.current_url

    def get_agent_name(self):
        return self.wait.until(
            EC.visibility_of_element_located(self.agent_name)
        ).text

    def is_tool_search_error_present(self):
        try:
            return self.driver.find_element(*self.tool_search_error).is_displayed()
        except Exception:
            return False

    def _wait_for_name_to_stabilize(self, current_name, timeout=30, poll=1, stable_checks=3):
        # The agent name can still be streaming in when first detected,
        # so wait until it stops changing before treating it as final.
        end_time = time.monotonic() + timeout
        stable_count = 0

        while time.monotonic() < end_time:
            time.sleep(poll)
            latest_name = self.driver.find_element(*self.agent_name).text.strip()

            if latest_name == current_name:
                stable_count += 1
                if stable_count >= stable_checks:
                    return latest_name
            else:
                current_name = latest_name
                stable_count = 0

        return current_name

    def _creation_completed(self, d):
        # The agent's name can update as soon as the chat parses the
        # requirements — well before the build/deploy pipeline actually
        # finishes — so it's not a safe completion signal on its own. Only
        # the deploy-success toast, a duplicate-name error (deployment
        # fails, but the chat won't progress past it on its own), or the
        # known tool-search limitation mean generation has actually reached
        # a terminal state — the duplicate-name error in particular only
        # shows up here, once the LLM has picked a name and tried to
        # deploy, not any earlier.
        if d.find_elements(*self.deploy_success_toast):
            return True
        if d.find_elements(*self.agent_exists_error):
            return True
        return self.is_tool_search_error_present()

    def _name_updated_or_tool_error(self, d):
        element = d.find_element(*self.agent_name)
        if element is None:
            # Selenium can return None instead of raising when the
            # browser window/tab crashes mid-poll. Surface it as a real
            # WebDriverException so it propagates and is recognized by
            # the test's @pytest.mark.flaky(only_rerun=[...]) check,
            # instead of failing here with an opaque AttributeError.
            raise WebDriverException(
                "Agent name element became unavailable; "
                "the browser window/tab may have crashed."
            )

        name = element.text.strip()
        if name != "Untitled Agent":
            return True
        return self.is_tool_search_error_present()

    @allure.step("Wait for the agent to finish generating and deploy")
    def wait_for_creation_signal(self, timeout=180):
        # Split out from the name-stabilisation logic below so a caller can
        # screenshot right here, at the moment generation actually finishes
        # (the deploy-success toast auto-dismisses after a few seconds, so
        # screenshotting only after the slower stabilisation work below
        # would usually miss it).
        try:
            WebDriverWait(self.driver, timeout).until(self._creation_completed)
        except TimeoutException:
            pass

    @allure.step("Confirm the generated agent name has stabilised")
    def get_stabilized_agent_name(self):
        agent_name = self.driver.find_element(*self.agent_name).text.strip()

        if agent_name != "Untitled Agent":
            agent_name = self._wait_for_name_to_stabilize(agent_name)

        if agent_name == "Untitled Agent":
            # The chat can finish and rename the agent on the backend without
            # the page header re-rendering. Reload once to re-sync state.
            self.driver.refresh()

            try:
                WebDriverWait(self.driver, 120).until(self._name_updated_or_tool_error)
            except TimeoutException:
                raise AssertionError(
                    "Agent creation failed: the agent remained 'Untitled Agent' "
                    "even after the chat finished and the page was refreshed."
                )

            agent_name = self.driver.find_element(*self.agent_name).text.strip()
            agent_name = self._wait_for_name_to_stabilize(agent_name)

        return agent_name

    @allure.step("Click EDITOR tab")
    def click_editor_tab(self):
        self.wait.until(
            EC.element_to_be_clickable(self.editor_tab)
        ).click()

    @allure.step("Open the agent name edit field")
    def click_agent_name_edit(self):
        self.wait.until(
            EC.element_to_be_clickable(self.agent_name_edit_trigger)
        ).click()

    @allure.step("Set the agent name to '{name}'")
    def set_agent_name(self, name):
        field = self.wait.until(
            EC.element_to_be_clickable(self.agent_name_input)
        )
        field.send_keys(Keys.CONTROL, "a")
        field.send_keys(Keys.DELETE)
        if name:
            field.send_keys(name)

    def is_agent_name_empty_error_present(self, timeout=10):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.agent_name_empty_error)
            ).is_displayed()
        except TimeoutException:
            return False

    def is_instructions_empty_error_present(self):
        try:
            return WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(self.instructions_empty_error)
            ).is_displayed()
        except TimeoutException:
            return False

    def get_model_provider_options(self):
        """Returns available model provider names from the dropdown."""
        self.wait.until(EC.element_to_be_clickable(self.model_provider_combobox)).click()
        option_locator = (By.XPATH, "//div[@role='option']")
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located(option_locator)
        )
        # The option elements can be present in the DOM as empty placeholders
        # a tick before their text renders (confirmed live: reading .text
        # immediately after presence_of_all_elements_located sometimes
        # returned an empty list even though the dropdown had real options
        # a moment later) — wait for at least one to actually have text
        # before reading them all, rather than trusting the first snapshot.
        names = WebDriverWait(self.driver, 10).until(
            lambda d: [o.text.strip() for o in d.find_elements(*option_locator) if o.text.strip()]
        )
        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
        return names

    def is_model_required_error_present(self):
        """Checks for an error toast indicating the model field must be filled."""
        locator = (
            By.XPATH,
            "//*[contains(@class,'Toastify__toast--error') and "
            "contains(translate(normalize-space(.),"
            "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'model')]"
        )
        try:
            return WebDriverWait(self.driver, 8).until(
                EC.visibility_of_element_located(locator)
            ).is_displayed()
        except TimeoutException:
            return False

    def is_deploy_confirm_visible(self, timeout=5):
        """Returns True if the 'Continue?' deploy confirmation dialog appeared
        (meaning validation did NOT block the deployment)."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable(self.deploy_confirm_button)
            )
            return True
        except TimeoutException:
            return False

    @allure.step("Close error notification")
    def close_error_toast(self):
        try:
            WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable(self.error_toast_close_button)
            ).click()
        except TimeoutException:
            pass

    def get_orchestrator_name(self):
        return self.wait.until(
            EC.visibility_of_element_located(self.orchestrator_name_input)
        ).get_attribute("value")

    @allure.step("Set orchestrator name to '{name}'")
    def set_orchestrator_name(self, name):
        field = self.wait.until(
            EC.element_to_be_clickable(self.orchestrator_name_input)
        )
        field.click()
        field.send_keys(Keys.CONTROL, "a")
        field.send_keys(Keys.DELETE)
        if name:
            field.send_keys(name)
        field.send_keys(Keys.TAB)

    def is_name_empty_error_present(self):
        try:
            return WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(self.name_empty_error)
            ).is_displayed()
        except TimeoutException:
            return False

    def is_name_alphanumeric_error_present(self):
        try:
            return WebDriverWait(self.driver, 5).until(
                EC.visibility_of_element_located(self.name_alphanumeric_error)
            ).is_displayed()
        except TimeoutException:
            return False

    @allure.step("Open instructions edit dialog")
    def click_instructions_eye_toggle(self):
        self.wait.until(
            EC.element_to_be_clickable(self.instructions_eye_button)
        ).click()

    @allure.step("Close instructions dialog")
    def close_instructions_modal(self):
        self.wait.until(
            EC.element_to_be_clickable(self.instructions_modal_close_button)
        ).click()

        try:
            WebDriverWait(self.driver, 10).until(
                EC.invisibility_of_element_located(self.instructions_modal_close_button)
            )
        except TimeoutException:
            pass

    @allure.step("Clear all instructions")
    def clear_instructions(self):
        textarea = self.wait.until(
            EC.element_to_be_clickable(self.instructions_modal_textarea)
        )
        textarea.click()
        textarea.send_keys(Keys.CONTROL, "a")
        textarea.send_keys(Keys.DELETE)
        self.close_instructions_modal()

    @allure.step("Set instructions text")
    def set_instructions_text(self, text):
        textarea = self.wait.until(
            EC.element_to_be_clickable(self.instructions_modal_textarea)
        )
        textarea.click()
        textarea.send_keys(Keys.CONTROL, "a")
        textarea.send_keys(Keys.DELETE)
        textarea.send_keys(text)
        self.close_instructions_modal()

    @allure.step("Select audio input type")
    def select_input_type_audio(self):
        self.wait.until(
            EC.element_to_be_clickable(self.input_type_audio_button)
        ).click()

    @allure.step("Select audio output type")
    def select_output_type_audio(self):
        self.wait.until(
            EC.element_to_be_clickable(self.output_type_audio_button)
        ).click()

    @allure.step("Select video output type")
    def select_output_type_video(self):
        self.wait.until(
            EC.element_to_be_clickable(self.output_type_video_button)
        ).click()

    @allure.step("Submit '{file_path}' for upload to knowledge base")
    def submit_upload_file(self, file_path):
        """Sends the file to the upload input and returns as soon as the request is
        submitted, without waiting for it to finish processing.

        Split out from upload_file() so a caller can screenshot the
        "File submitted for processing" toast right as it appears (see
        wait_for_upload_toast()) — it auto-dismisses after a few seconds, so
        capturing it after the slower completion wait below would miss it.
        """
        # Clicking the visible "Upload" button opens the native OS file
        # dialog, which Selenium cannot drive and would just sit there
        # blocking the browser. Skip the click and send the path straight
        # to the underlying <input type="file"> instead.

        # The knowledge base panel scrolls internally, so scroll it into
        # view *before* submitting — scrolling afterwards, once the toast is
        # already showing, would happen too late to appear in a screenshot
        # taken right when the toast fires.
        self.scroll_knowledge_base_heading_into_view()

        file_input = self.wait.until(
            EC.presence_of_element_located(self.knowledge_base_file_input)
        )

        pending_count_before = len(self.driver.find_elements(*self.pending_upload_status))
        file_input.send_keys(file_path)
        return pending_count_before

    def wait_for_upload_toast(self, timeout=10):
        """Waits for the 'File submitted for processing' toast. Auto-dismisses after
        a few seconds — callers should screenshot immediately after this returns."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.file_upload_toast)
            )
        except TimeoutException:
            pass

    @allure.step("Wait for '{file_path}' upload to complete")
    def wait_for_upload_completion(self, file_path, pending_count_before, timeout=60):
        # The new row briefly shows "Pending" before flipping to "Completed".
        # Wait for both transitions so the upload is actually visible on
        # screen instead of the test racing past it.
        WebDriverWait(self.driver, 15).until(
            lambda d: len(d.find_elements(*self.pending_upload_status)) > pending_count_before
        )
        WebDriverWait(self.driver, timeout).until(
            lambda d: len(d.find_elements(*self.pending_upload_status)) <= pending_count_before
        )

        # The knowledge base list scrolls internally, so a newly uploaded
        # file can land outside the visible area even though the upload
        # succeeded. Scroll it into view so it's actually visible on screen.
        self._scroll_knowledge_base_row_into_view(os.path.basename(file_path))

    @allure.step("Upload '{file_path}' to knowledge base")
    def upload_file(self, file_path):
        pending_count_before = self.submit_upload_file(file_path)
        self.wait_for_upload_completion(file_path, pending_count_before)

    def get_knowledge_base_row(self, file_name, index=0, timeout=5):
        """Returns the WebElement for the given knowledge base row, or None if it
        isn't present (e.g. called right after the row was deleted)."""
        row_xpath = f"({self.knowledge_base_row_xpath.format(file_name=file_name)})[{index + 1}]"
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, row_xpath))
            )
        except TimeoutException:
            return None

    def _scroll_knowledge_base_row_into_view(self, file_name, index=0):
        row = self.get_knowledge_base_row(file_name, index, timeout=5)
        if row is not None:
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", row)

    def scroll_knowledge_base_heading_into_view(self):
        """Scrolls the Knowledge Base panel itself into view. Used after a delete,
        when the row that would otherwise anchor the scroll no longer exists."""
        try:
            heading = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(self.knowledge_base_heading)
            )
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", heading)
        except TimeoutException:
            pass

    def count_knowledge_base_files(self, file_name):
        locator = (By.XPATH, self.knowledge_base_row_xpath.format(file_name=file_name))
        return len(self.driver.find_elements(*locator))

    @allure.step("Delete '{file_name}' from knowledge base")
    def delete_knowledge_base_file(self, file_name, index=0):
        row_xpath = f"({self.knowledge_base_row_xpath.format(file_name=file_name)})[{index + 1}]"
        before_count = self.count_knowledge_base_files(file_name)

        self._scroll_knowledge_base_row_into_view(file_name, index)

        delete_locator = (By.XPATH, row_xpath + "//button[@title='Delete file']")
        self.wait.until(
            EC.element_to_be_clickable(delete_locator)
        ).click()

        # Deleting shows an inline "Confirm"/"Cancel" pair in place of the
        # trash icon rather than opening a separate dialog.
        confirm_locator = (By.XPATH, row_xpath + "//button[normalize-space()='Confirm']")
        WebDriverWait(self.driver, 5).until(
            EC.element_to_be_clickable(confirm_locator)
        ).click()

        WebDriverWait(self.driver, 15).until(
            lambda d: self.count_knowledge_base_files(file_name) < before_count
        )

    def wait_for_delete_toast(self, timeout=10):
        """Waits for the 'File deleted successfully' toast. Auto-dismisses after a
        few seconds — callers should screenshot immediately after this returns."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.file_delete_toast)
            )
        except TimeoutException:
            pass

    @allure.step("Cancel delete of '{file_name}' from knowledge base")
    def cancel_delete_knowledge_base_file(self, file_name, index=0):
        row_xpath = f"({self.knowledge_base_row_xpath.format(file_name=file_name)})[{index + 1}]"

        self._scroll_knowledge_base_row_into_view(file_name, index)

        delete_locator = (By.XPATH, row_xpath + "//button[@title='Delete file']")
        self.wait.until(
            EC.element_to_be_clickable(delete_locator)
        ).click()

        cancel_locator = (By.XPATH, row_xpath + "//button[normalize-space()='Cancel']")
        WebDriverWait(self.driver, 5).until(
            EC.element_to_be_clickable(cancel_locator)
        ).click()

        # Cancel should revert the row back to showing the delete icon
        # instead of the Confirm/Cancel pair.
        WebDriverWait(self.driver, 5).until(
            EC.element_to_be_clickable(delete_locator)
        )

    @allure.step("Click GRAPH tab")
    def click_graph_tab(self):
        tab = self.wait.until(
            EC.element_to_be_clickable(self.graph_tab)
        )
        self.driver.execute_script("arguments[0].click();", tab)

    @allure.step("Open agent card '{card_name}' in graph")
    def open_agent_card(self, card_name):
        # A page-wide text search (e.g. //*[contains(text(),...)]) can match
        # the card's name somewhere else on the page (like the top-level
        # Agent Name header) before it reaches the actual graph node, silently
        # clicking the wrong element and never opening the Model/Tools panel.
        # Scoping the search to react-flow nodes (same set get_agent_card_names
        # uses) guarantees the click lands on the real card.
        nodes = self.wait.until(
            EC.presence_of_all_elements_located(self.graph_node)
        )

        card = None
        for node in nodes:
            text = node.text.strip()
            if text and text.splitlines()[0].strip() == card_name:
                card = node
                break

        assert card is not None, f"No graph node found matching '{card_name}'"

        self.driver.execute_script("arguments[0].scrollIntoView(true);", card)
        self.driver.execute_script("arguments[0].click();", card)

    @allure.step("Open orchestrator card in graph")
    def open_orchestrator_card(self):
        node = self.wait.until(
            EC.presence_of_element_located(self.orchestrator_node)
        )

        self.driver.execute_script("arguments[0].scrollIntoView(true);", node)
        self.driver.execute_script("arguments[0].click();", node)

    def get_sub_agent_cards(self):
        # Returns (data_id, name) pairs for real sub-agent nodes (data-id
        # starts with "agent-"), excluding the orchestrator and mcp tool nodes.
        # Using data_id to open the card avoids ambiguous text-search matches
        # when the name also appears in another card's description text.
        nodes = self.driver.find_elements(*self.sub_agent_node)

        cards = []
        for node in nodes:
            data_id = node.get_attribute("data-id") or ""
            text = node.text.strip()
            if not text:
                continue
            cards.append((data_id, text.splitlines()[0].strip()))

        return cards

    @allure.step("Open graph node '{data_id}'")
    def open_card_by_data_id(self, data_id):
        locator = (By.CSS_SELECTOR, f".react-flow__node[data-id='{data_id}']")
        for attempt in range(3):
            node = self.wait.until(EC.element_to_be_clickable(locator))
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", node)
            if attempt == 0:
                self.driver.execute_script("arguments[0].click();", node)
            else:
                ActionChains(self.driver).move_to_element(node).click().perform()
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located(self.instructions_eye_button)
                )
                return
            except TimeoutException:
                continue

    def get_instructions_modal_text(self):
        """Returns the full text currently in the instructions modal textarea."""
        return self.wait.until(
            EC.visibility_of_element_located(self.instructions_modal_textarea)
        ).get_attribute("value")

    def get_instructions_preview_text(self):
        return self.wait.until(
            EC.visibility_of_element_located(self.instructions_preview)
        ).text.strip()

    def is_agent_instructions_empty_error_present(self, agent_name):
        locator = (
            By.XPATH,
            f"//*[contains(text(),'instructions cannot be empty') and contains(text(),'{agent_name}')]"
        )
        try:
            return WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(locator)
            ).is_displayed()
        except TimeoutException:
            return False

    def get_agent_card_names(self):
        # MCP tool nodes (data-id contains "mcp") and the Knowledge Base node
        # (data-id == "knowledge-base", confirmed live — added to the graph
        # once at least one file has been uploaded to the agent's knowledge
        # base) sit on the graph alongside agent/orchestrator nodes but don't
        # open the Model/Tools panel, so they're excluded. Missing this
        # exclusion was a real, reproducible bug: callers that
        # random.choice() a card from this list (e.g.
        # test_attach_tool_to_orchestrator) could pick "Knowledge Base" and
        # open that panel instead of an agent's config panel, then time out
        # forever waiting for a Model Provider dropdown that panel doesn't
        # have. An agent node's display name is the first line of its text
        # (name, description, model, role stacked underneath).
        nodes = self.wait.until(
            EC.presence_of_all_elements_located(self.graph_node)
        )

        names = []
        for node in nodes:
            data_id = node.get_attribute("data-id") or ""
            if "mcp" in data_id or data_id == "knowledge-base":
                continue

            text = node.text.strip()
            if not text:
                continue

            names.append(text.splitlines()[0].strip())

        return names

    @allure.step("Select model provider '{provider_name}'")
    def select_model_provider(self, provider_name):
        self.wait.until(
            EC.element_to_be_clickable(self.model_provider_combobox)
        ).click()

        option_locator = (
            By.XPATH,
            f"//div[@role='option' and normalize-space()='{provider_name}']"
        )

        self.wait.until(
            EC.element_to_be_clickable(option_locator)
        ).click()

    @allure.step("Select a random model")
    def select_random_model(self):
        model_button = self.wait.until(
            EC.element_to_be_clickable(self.model_field_button)
        )

        self.driver.execute_script("arguments[0].scrollIntoView(true);", model_button)
        self.driver.execute_script("arguments[0].click();", model_button)

        options = self.wait.until(
            EC.presence_of_all_elements_located(self.model_option_names)
        )

        chosen = random.choice(options)
        chosen_name = chosen.text

        self.driver.execute_script("arguments[0].scrollIntoView(true);", chosen)
        self.driver.execute_script("arguments[0].click();", chosen)

        return chosen_name

    @allure.step("Select tool '{tool_name}'")
    def select_tool(self, tool_name):
        if self.is_tool_selected(tool_name):
            return

        self.wait.until(
            EC.element_to_be_clickable(self.tools_select_input)
        ).click()

        option_locator = (
            By.XPATH,
            f"//div[contains(@class,'react-select__option') and normalize-space()='{tool_name}']"
        )

        self.wait.until(
            EC.element_to_be_clickable(option_locator)
        ).click()

    def is_tool_selected(self, tool_name, timeout=5):
        try:
            chips = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_all_elements_located(self.tools_selected_chips)
            )
            return any(chip.text.strip() == tool_name for chip in chips)
        except TimeoutException:
            return False

    @allure.step("Save configuration")
    def click_save(self):
        self.wait.until(
            EC.element_to_be_clickable(self.save_button)
        ).click()

    @allure.step("Redeploy agent")
    def click_redeploy(self):
        self.wait.until(
            EC.element_to_be_clickable(self.redeploy_button)
        ).click()

        # Validation errors (empty name, empty instructions) fire as an
        # error toast almost instantly after the click — typically < 1s.
        # A real "Continue?" confirmation dialog may take several seconds
        # to render. Check for the error toast first with a short window;
        # if none appears, wait generously for the confirm dialog instead.
        error_toast_locator = (
            By.XPATH,
            "//*[contains(@class,'Toastify__toast--error')]"
        )
        try:
            WebDriverWait(self.driver, 3).until(
                EC.visibility_of_element_located(error_toast_locator)
            )
            return
        except TimeoutException:
            pass

        try:
            WebDriverWait(self.driver, 60).until(
                EC.element_to_be_clickable(self.deploy_confirm_button)
            ).click()
        except TimeoutException:
            return

        try:
            WebDriverWait(self.driver, 120).until(
                EC.invisibility_of_element_located(self.modal_overlay)
            )
        except TimeoutException:
            pass

    def is_redeploy_success_toast_present(self, timeout=10):
        """Waits for the 'Agent Redeployed Successfully!' toast. Auto-dismisses
        after a few seconds — callers should screenshot immediately after this
        returns True."""
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.redeploy_success_toast)
            ).is_displayed()
        except TimeoutException:
            return False

    @allure.step("Redeploy if available (skip if only Publish is offered)")
    def try_redeploy(self, timeout=5):
        """Clicks Redeploy from the Save dropdown when available.
        If the dropdown only offers Publish (e.g. a newly created agent that was
        never deployed), presses Escape to close it without publishing."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable(self.redeploy_button)
            ).click()
        except TimeoutException:
            ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
            return
        try:
            WebDriverWait(self.driver, 60).until(
                EC.element_to_be_clickable(self.deploy_confirm_button)
            ).click()
        except TimeoutException:
            pass
        try:
            WebDriverWait(self.driver, 120).until(
                EC.invisibility_of_element_located(self.modal_overlay)
            )
        except TimeoutException:
            pass

    @allure.step("Publish agent")
    def click_publish(self):
        self.wait.until(
            EC.element_to_be_clickable(self.publish_button)
        ).click()

    @allure.step("Save and deploy agent")
    def click_save_and_deploy(self):
        # After clicking Save the toolbar dropdown shows Redeploy and/or
        # Publish depending on the agent's current deploy state.  Try Redeploy
        # first (for already-deployed agents); fall back to Publish when
        # Redeploy is greyed out (agent has unsaved edits that must be
        # published before a redeploy becomes available).
        self.click_save()
        try:
            WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(self.redeploy_button)
            ).click()

            try:
                WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable(self.deploy_confirm_button)
                ).click()
            except TimeoutException:
                return

            try:
                WebDriverWait(self.driver, 120).until(
                    EC.invisibility_of_element_located(self.modal_overlay)
                )
            except TimeoutException:
                pass

        except TimeoutException:
            self.click_publish()

    @allure.step("Navigate back to My Agents")
    def go_back_to_agents(self):
        self.wait.until(
            EC.element_to_be_clickable(self.back_button)
        ).click()

        self.handle_unsaved_changes_dialog()

        self.wait.until(
            EC.url_contains("/agents")
        )

    def handle_unsaved_changes_dialog(self, timeout=5):
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable(self.leave_page_button)
            ).click()
        except TimeoutException:
            pass

    def get_status(self):
        return self.wait.until(
            EC.visibility_of_element_located(self.status_badge)
        ).text.strip().lower()

    def is_duplicate_name_error_present(self):
        try:
            WebDriverWait(self.driver, 5).until(
                EC.visibility_of_element_located(self.agent_exists_error)
            )
            return True

        except TimeoutException:
            return False

    def get_creation_error(self):
        try:
            return WebDriverWait(self.driver, 5).until(
                EC.visibility_of_element_located(self.agent_exists_error)
            ).text

        except TimeoutException:
            return None

    # ------------------------------------------------------------------
    # Interact window
    # ------------------------------------------------------------------

    @allure.step("Click 'Interact' to open the Interact window")
    def click_interact(self):
        # The panel slides in with a CSS transition right after this click,
        # and a native .click() can lose a race against that animation —
        # Selenium's own post-click interception check sees the panel
        # already covering the button and raises
        # ElementClickInterceptedException even though the click already
        # landed and opened the panel (confirmed: the failure screenshot
        # showed the panel open in its fresh, empty state). A JS click
        # dispatches directly on the element and skips that check.
        button = self.wait.until(EC.element_to_be_clickable(self.interact_button))
        self.driver.execute_script("arguments[0].click();", button)

    @allure.step("Close the Interact window")
    def close_interact_panel(self):
        # Same category of issue as click_interact(): a native .click() here
        # can get intercepted by the panel's own welcome-screen/message-list
        # container overlapping the button's coordinates, even though the
        # button itself is the right element — a JS click sidesteps it.
        #
        # Confirmed reproducible when called immediately after the panel
        # just opened (no action in between): the click can silently not
        # register — likely the panel's own open transition still settling
        # — so this retries rather than assuming one click is enough.
        for _ in range(3):
            button = self.wait.until(EC.element_to_be_clickable(self.interact_close_button))
            self.driver.execute_script("arguments[0].click();", button)
            if self.is_interact_panel_closed(timeout=5):
                return
        raise TimeoutException(
            "Interact window did not close after repeated attempts to click the close button"
        )

    def is_interact_panel_open(self, timeout=10):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.interact_message_input)
            ).is_displayed()
        except TimeoutException:
            return False

    def is_interact_panel_closed(self, timeout=10):
        # Not just `not is_interact_panel_open()`: that method's wait
        # returns as soon as the element is seen visible even once, so
        # calling it right after close_interact_panel() can catch the
        # textarea still present mid-exit-animation and report "open" on
        # the very first poll. This waits for actual absence instead.
        try:
            return WebDriverWait(self.driver, timeout).until_not(
                EC.presence_of_element_located(self.interact_message_input)
            )
        except TimeoutException:
            return False

    @allure.step("Enter message '{message}' in the Interact window")
    def enter_interact_message(self, message):
        field = self.wait.until(EC.element_to_be_clickable(self.interact_message_input))
        field.clear()
        field.send_keys(message)

    def get_interact_message_value(self):
        return self.driver.find_element(*self.interact_message_input).get_attribute("value")

    def is_interact_send_button_enabled(self):
        # The button carries its own disabled: classes rather than a plain
        # disabled attribute check being unreliable here — reading the
        # actual DOM attribute is the direct signal either way.
        button = self.driver.find_element(*self.interact_send_button)
        return button.get_attribute("disabled") is None

    @allure.step("Click Send in the Interact window")
    def click_interact_send(self):
        self.wait.until(EC.element_to_be_clickable(self.interact_send_button)).click()

    @allure.step("Wait for the Interact agent to finish responding")
    def wait_for_interact_response(self, timeout=120):
        WebDriverWait(self.driver, timeout).until(
            lambda d: len(d.find_elements(By.XPATH, "//*[contains(text(),'Thinking')]")) == 0
        )

    @allure.step("Click 'New Chat' in the Interact window")
    def click_interact_new_chat(self):
        # The button stays disabled slightly longer than the "Thinking"
        # indicator takes to clear (confirmed: clicking right after
        # wait_for_interact_response() alone can land on a still-disabled
        # button and silently do nothing), so this waits for it to actually
        # become clickable rather than just present.
        self.wait.until(EC.element_to_be_clickable(self.interact_new_chat_button)).click()

    def is_interact_welcome_screen_present(self, timeout=10):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.interact_welcome_text)
            ).is_displayed()
        except TimeoutException:
            return False

    @allure.step("Upload '{file_path}' in the Interact window")
    def upload_interact_file(self, file_path):
        file_input = self.wait.until(EC.presence_of_element_located(self.interact_file_input))
        file_input.send_keys(file_path)

    def is_interact_file_attached(self, file_name, timeout=10):
        locator = (
            By.XPATH,
            f"{self._interact_panel_prefix}//*[contains(text(),'{file_name}')]"
        )
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(locator)
            ).is_displayed()
        except TimeoutException:
            return False
