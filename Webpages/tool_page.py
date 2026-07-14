import allure
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


class ToolPage:

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 30)

        self.tools_nav_link = (
            By.XPATH,
            "//a[@href='/tools']"
        )

        # The tool builder (create/edit) view has its own sub-sidebar
        # (Back / Build Tool / Publish Tool / Logs) instead of the main app
        # nav, so returning to the Available Tools list from there goes
        # through this "Back" link/button rather than tools_nav_link.
        self.back_button = (
            By.XPATH,
            "//*[self::a or self::button][normalize-space()='Back']"
        )

        self.leave_page_button = (
            By.XPATH,
            "//button[normalize-space()='Leave Page']"
        )

        # A transient "Something went wrong / We're having trouble reaching
        # our servers" modal can pop up from an unrelated background
        # request (observed right after tool creation — likely a stats/log
        # poll, not the creation call itself, since the tool is already
        # confirmed created by this point). Its backdrop then intercepts
        # clicks on anything else on the page, so it's dismissed
        # defensively rather than letting it silently break the next click.
        self.server_error_dismiss_button = (
            By.XPATH,
            "//button[normalize-space()='Dismiss']"
        )

        self.generate_button = (
            By.XPATH,
            "//button[normalize-space()='Generate']"
        )

        self.use_prompt_or_files_button = (
            By.XPATH,
            "//button[normalize-space()='Use Prompt or Files']"
        )

        self.tool_name_input = (
            By.XPATH,
            "//input[@name='name']"
        )

        self.tool_description_textarea = (
            By.XPATH,
            "//textarea[@name='description']"
        )

        self.generate_code_button = (
            By.XPATH,
            "//button[normalize-space()='Generate Code']"
        )

        # Both the code-generation and tool-creation steps show a "Hold
        # tight!" modal with a slightly different message ("...generating a
        # code." vs "...creating your tool."); a single contains() locator
        # covers both since each wait call only ever fires right after the
        # matching trigger action, so there's no ambiguity in practice.
        self.hold_tight_modal = (
            By.XPATH,
            "//*[contains(text(),'Hold tight')]"
        )

        self.create_tool_button = (
            By.XPATH,
            "//button[@type='submit' and normalize-space()='Create Tool']"
        )

        # The submit button's label flips from "Create Tool" to "Update
        # Tool" once the tool actually exists on the server — the clearest
        # signal that creation succeeded.
        self.update_tool_button = (
            By.XPATH,
            "//button[@type='submit' and normalize-space()='Update Tool']"
        )

        self.search_tool_input = (
            By.XPATH,
            "//input[@placeholder='Search Tool...']"
        )

        self.tool_card_title = (
            By.XPATH,
            "//h2"
        )

        self.custom_tools_tab = (
            By.XPATH,
            "//button[normalize-space()='Custom Tools']"
        )

        self.upload_code_trigger = (
            By.XPATH,
            "//*[@title='Upload code']"
        )

        # Clicking upload_code_trigger opens a "Click to upload or drag and
        # drop" modal that mounts its OWN <input type=file accept=".py">,
        # replacing whatever transient input existed right after the click —
        # wait for this text before locating the input, or send_keys can
        # land on a stale/detached node.
        self.upload_modal_dropzone_text = (
            By.XPATH,
            "//*[contains(text(),'Click to upload or drag and drop')]"
        )

        self.file_input = (
            By.XPATH,
            "//input[@type='file']"
        )

        self.upload_code_error_toast = (
            By.XPATH,
            "//*[contains(@class,'Toastify__toast--error') and contains(.,'.py')]"
        )

        self.upload_code_success_toast = (
            By.XPATH,
            "//*[contains(@class,'Toastify__toast--success') and contains(.,'File Uploaded')]"
        )

        self.tool_updated_toast = (
            By.XPATH,
            "//*[contains(@class,'Toastify__toast--success') and contains(.,'Tool Updated')]"
        )

        self.code_editor_view = (
            By.XPATH,
            "//button[normalize-space()='Code']/following::div[contains(@class,'view-line')][1]"
        )

    @allure.step("Navigate to Tools")
    def click_tools_nav(self):
        self.wait.until(
            EC.element_to_be_clickable(self.tools_nav_link)
        ).click()
        # A newly-created tool's edit page URL also contains "/tools", so
        # waiting on the URL alone can pass before the list view actually
        # renders. The "+ Generate" button only exists on the Available
        # Tools list page, so wait on that instead.
        self.wait.until(
            EC.element_to_be_clickable(self.generate_button)
        )

    @allure.step("Click 'Generate' to start building a new tool")
    def click_generate(self):
        self.wait.until(
            EC.element_to_be_clickable(self.generate_button)
        ).click()

    @allure.step("Choose the 'Custom Tool' (prompt/files) build method")
    def choose_custom_tool(self):
        self.wait.until(
            EC.element_to_be_clickable(self.use_prompt_or_files_button)
        ).click()

    @allure.step("Enter tool name '{tool_name}'")
    def enter_tool_name(self, tool_name):
        name_input = self.wait.until(
            EC.presence_of_element_located(self.tool_name_input)
        )
        name_input.clear()
        name_input.send_keys(tool_name)

    @allure.step("Enter tool description")
    def enter_tool_description(self, description):
        self.wait.until(
            EC.presence_of_element_located(self.tool_description_textarea)
        ).send_keys(description)

    @allure.step("Click 'Generate Code'")
    def click_generate_code(self):
        self.wait.until(
            EC.element_to_be_clickable(self.generate_code_button)
        ).click()

    @allure.step("Wait for code generation to complete")
    def wait_for_code_generation(self, timeout=150):
        # Split from click_generate_code() so a caller can screenshot right
        # as the "Hold tight!" modal appears/disappears rather than losing
        # that moment inside a single long wait.
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(self.hold_tight_modal)
            )
        except TimeoutException:
            pass
        WebDriverWait(self.driver, timeout).until_not(
            EC.presence_of_element_located(self.hold_tight_modal)
        )

    @allure.step("Click 'Create Tool'")
    def click_create_tool(self):
        self.wait.until(
            EC.element_to_be_clickable(self.create_tool_button)
        ).click()

    @allure.step("Wait for tool creation to complete")
    def wait_for_tool_creation(self, timeout=150):
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(self.hold_tight_modal)
            )
        except TimeoutException:
            pass
        WebDriverWait(self.driver, timeout).until_not(
            EC.presence_of_element_located(self.hold_tight_modal)
        )

    def _dismiss_server_error_modal(self, timeout=3):
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable(self.server_error_dismiss_button)
            ).click()
        except TimeoutException:
            pass

    @allure.step("Navigate back to Available Tools list")
    def click_back(self):
        self._dismiss_server_error_modal()
        self.wait.until(
            EC.element_to_be_clickable(self.back_button)
        ).click()

        try:
            WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(self.leave_page_button)
            ).click()
        except TimeoutException:
            pass

        self.wait.until(
            EC.element_to_be_clickable(self.generate_button)
        )

    @allure.step("Filter to Custom Tools")
    def click_custom_tools_tab(self):
        self.wait.until(
            EC.element_to_be_clickable(self.custom_tools_tab)
        ).click()

    def get_tool_names(self):
        cards = self.wait.until(
            EC.presence_of_all_elements_located(self.tool_card_title)
        )
        return [c.text.strip() for c in cards if c.text.strip()]

    @allure.step("Open tool '{tool_name}'")
    def open_tool_card(self, tool_name):
        card_locator = self._case_insensitive_card_locator(tool_name)
        card = self.wait.until(EC.presence_of_element_located(card_locator))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", card)
        self.driver.execute_script("arguments[0].click();", card)

    @allure.step("Click 'Upload code'")
    def click_upload_code(self):
        self.wait.until(
            EC.element_to_be_clickable(self.upload_code_trigger)
        ).click()
        self.wait.until(
            EC.presence_of_element_located(self.upload_modal_dropzone_text)
        )

    @allure.step("Upload code file '{file_path}'")
    def upload_code_file(self, file_path):
        # The modal mounts its own <input type=file>; must be located fresh
        # after click_upload_code()'s dropzone-text wait, not reused from any
        # earlier lookup, or send_keys silently lands on a detached node.
        file_input = self.wait.until(
            EC.presence_of_element_located(self.file_input)
        )
        file_input.send_keys(file_path)

    def is_upload_code_error_present(self, timeout=8):
        """True if the 'Only .py files are allowed.' toast appears — fires
        when a non-.py file is fed to the Upload code input."""
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.upload_code_error_toast)
            ).is_displayed()
        except TimeoutException:
            return False

    def is_upload_code_success_present(self, timeout=10):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.upload_code_success_toast)
            ).is_displayed()
        except TimeoutException:
            return False

    @allure.step("Click 'Update Tool'")
    def click_update_tool(self):
        update_btn = self.wait.until(
            EC.element_to_be_clickable(self.update_tool_button)
        )
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", update_btn)
        update_btn.click()

    @allure.step("Wait for tool update to complete")
    def wait_for_tool_update(self, timeout=150):
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(self.hold_tight_modal)
            )
        except TimeoutException:
            pass
        WebDriverWait(self.driver, timeout).until_not(
            EC.presence_of_element_located(self.hold_tight_modal)
        )

    def is_tool_updated(self, timeout=10):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.tool_updated_toast)
            ).is_displayed()
        except TimeoutException:
            return False

    def get_code_editor_text(self, timeout=10):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(self.code_editor_view)
            ).text.strip()
        except TimeoutException:
            return ""

    def is_tool_created(self, timeout=10):
        """The 'Create Tool' submit button relabels to 'Update Tool' once the
        tool exists on the server — the clearest signal that creation succeeded."""
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.update_tool_button)
            ).is_displayed()
        except TimeoutException:
            return False

    @staticmethod
    def _case_insensitive_card_locator(tool_name):
        # Card titles are styled with CSS `capitalize`, which changes how the
        # name renders but not the underlying DOM text node.
        return (
            By.XPATH,
            "//h2[translate(normalize-space(.), "
            "'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')="
            f"'{tool_name.lower()}']"
        )

    @allure.step("Search for tool '{tool_name}'")
    def search_tool(self, tool_name):
        search_box = self.wait.until(
            EC.visibility_of_element_located(self.search_tool_input)
        )
        search_box.clear()
        search_box.send_keys(tool_name)

    def verify_tool_card(self, tool_name, timeout=10):
        card_locator = self._case_insensitive_card_locator(tool_name)
        try:
            card = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(card_locator)
            )
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", card)
            return card.is_displayed()
        except TimeoutException:
            return False
