import random
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


class AgentConfigurationPage:

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 180)

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

        self.graph_tab = (
            By.XPATH,
            "//*[self::button or self::a][normalize-space()='GRAPH']"
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

        self.modal_overlay = (
            By.XPATH,
            "//div[@data-state='open' and contains(@class,'fixed') and contains(@class,'inset-0')]"
        )

        self.deploy_confirm_button = (
            By.XPATH,
            "//div[@role='dialog']//button[normalize-space()='Continue']"
        )

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

    def wait_for_agent_name_update(self):

        def name_updated_or_tool_error(d):
            name = d.find_element(*self.agent_name).text.strip()
            if name != "Untitled Agent":
                return True
            return self.is_tool_search_error_present()

        try:
            WebDriverWait(self.driver, 480).until(name_updated_or_tool_error)
        except TimeoutException:
            pass

        agent_name = self.driver.find_element(*self.agent_name).text.strip()

        if agent_name != "Untitled Agent":
            agent_name = self._wait_for_name_to_stabilize(agent_name)

        if agent_name == "Untitled Agent":
            # The chat can finish and rename the agent on the backend without
            # the page header re-rendering. Reload once to re-sync state.
            self.driver.refresh()

            try:
                WebDriverWait(self.driver, 120).until(
                    lambda d: d.find_element(*self.agent_name).text.strip() != "Untitled Agent"
                )
            except TimeoutException:
                raise AssertionError(
                    "Agent creation failed: the agent remained 'Untitled Agent' "
                    "even after the chat finished and the page was refreshed."
                )

            agent_name = self.driver.find_element(*self.agent_name).text.strip()
            agent_name = self._wait_for_name_to_stabilize(agent_name)

        return agent_name

    def click_editor_tab(self):
        self.wait.until(
            EC.element_to_be_clickable(self.editor_tab)
        ).click()

    def select_input_type_audio(self):
        self.wait.until(
            EC.element_to_be_clickable(self.input_type_audio_button)
        ).click()

    def select_output_type_audio(self):
        self.wait.until(
            EC.element_to_be_clickable(self.output_type_audio_button)
        ).click()

    def select_output_type_video(self):
        self.wait.until(
            EC.element_to_be_clickable(self.output_type_video_button)
        ).click()

    def upload_file(self, file_path):
        # Clicking the visible "Upload" button opens the native OS file
        # dialog, which Selenium cannot drive and would just sit there
        # blocking the browser. Skip the click and send the path straight
        # to the underlying <input type="file"> instead.
        file_input = self.wait.until(
            EC.presence_of_element_located(self.knowledge_base_file_input)
        )

        pending_count_before = len(self.driver.find_elements(*self.pending_upload_status))

        file_input.send_keys(file_path)

        # The new row briefly shows "Pending" before flipping to "Completed".
        # Wait for both transitions so the upload is actually visible on
        # screen instead of the test racing past it.
        WebDriverWait(self.driver, 15).until(
            lambda d: len(d.find_elements(*self.pending_upload_status)) > pending_count_before
        )
        WebDriverWait(self.driver, 60).until(
            lambda d: len(d.find_elements(*self.pending_upload_status)) <= pending_count_before
        )

    def count_knowledge_base_files(self, file_name):
        locator = (By.XPATH, self.knowledge_base_row_xpath.format(file_name=file_name))
        return len(self.driver.find_elements(*locator))

    def delete_knowledge_base_file(self, file_name, index=0):
        row_xpath = f"({self.knowledge_base_row_xpath.format(file_name=file_name)})[{index + 1}]"
        before_count = self.count_knowledge_base_files(file_name)

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

    def cancel_delete_knowledge_base_file(self, file_name, index=0):
        row_xpath = f"({self.knowledge_base_row_xpath.format(file_name=file_name)})[{index + 1}]"

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

    def click_graph_tab(self):
        self.wait.until(
            EC.element_to_be_clickable(self.graph_tab)
        ).click()

    def open_agent_card(self, card_name):
        card_locator = (
            By.XPATH,
            f"//*[contains(text(),'{card_name}')]"
        )

        card = self.wait.until(
            EC.presence_of_element_located(card_locator)
        )

        self.driver.execute_script("arguments[0].scrollIntoView(true);", card)
        self.driver.execute_script("arguments[0].click();", card)

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

    def click_save(self):
        self.wait.until(
            EC.element_to_be_clickable(self.save_button)
        ).click()

    def click_redeploy(self):
        self.wait.until(
            EC.element_to_be_clickable(self.redeploy_button)
        ).click()

        # Redeploying opens a "Are you sure you want to deploy changes?"
        # confirmation dialog that must be confirmed before it clears.
        self.wait.until(
            EC.element_to_be_clickable(self.deploy_confirm_button)
        ).click()

        try:
            WebDriverWait(self.driver, 120).until(
                EC.invisibility_of_element_located(self.modal_overlay)
            )
        except TimeoutException:
            pass

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
