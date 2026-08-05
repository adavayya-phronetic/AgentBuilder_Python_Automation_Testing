import time

import allure
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, InvalidElementStateException, StaleElementReferenceException


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

        # The other "Generate" chooser card — builds a tool from an
        # external MCP server URL instead of a prompt/file upload.
        self.use_urls_button = (
            By.XPATH,
            "//button[normalize-space()='Use URLs']"
        )

        self.authorization_header_toggle = (
            By.XPATH,
            "//button[contains(@class,'peer') and contains(@class,'inline-flex')]"
        )

        # The header *name* field is now a required, editable input (confirmed
        # live: submitting with it empty shows an inline "Header name is
        # required" error) — it is no longer the fixed, read-only 'X-API-KEY'
        # it used to be.
        self.header_name_input = (
            By.XPATH,
            "//label[normalize-space()='Header Name']/following::input[1]"
        )

        self.header_value_input = (
            By.XPATH,
            "//label[normalize-space()='Header Value']/following::input[1]"
        )

        self.save_header_button = (
            By.XPATH,
            "//button[normalize-space()='Save']"
        )

        self.mcp_url_input = (
            By.XPATH,
            "//input[@placeholder=\"Enter your tool's URL\"]"
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

        # Fires once on initial creation only ("Tool Created Successfully"),
        # distinct from tool_updated_toast which fires on every subsequent
        # save — auto-dismisses after a few seconds like every other toast
        # in this app, so callers must screenshot immediately after
        # detecting it.
        self.tool_created_toast = (
            By.XPATH,
            "//*[contains(@class,'Toastify__toast--success') and contains(.,'Tool Created')]"
        )

        self.code_editor_view = (
            By.XPATH,
            "//button[normalize-space()='Code']/following::div[contains(@class,'view-line')][1]"
        )

        # "Test your tool" panel: each function is listed by name with its
        # own row-level "Test" expander (has a chevron icon); expanding it
        # reveals per-parameter inputs and a separate submit "Test" button
        # (no icon) plus an Output panel.
        #
        # NOTE: this must anchor on the h6 and walk up to the NEAREST
        # row ancestor (ancestor::div[...][1]), not "//div[.//h6=X]". The
        # latter also matches the outer Functions container (which contains
        # every row's h6 and every Test button as descendants too), making
        # it ambiguous — it silently resolved to whichever button happened
        # to be first/visible in document order instead of the requested
        # function's own row, so clicking "subtract" could actually expand
        # a completely different function.
        self.function_test_expander_xpath = (
            "//h6[normalize-space()='{function_name}']"
            "/ancestor::div[contains(@class,'border-b')][1]//button[normalize-space()='Test']"
        )

        self.test_function_names = (
            By.XPATH,
            "//label[normalize-space()='Functions']/following::h6"
        )

        # svg must be matched via *[local-name()='svg'] rather than a bare
        # svg element test — chromedriver's XPath evaluator is namespace-aware
        # for SVG's foreign namespace, so an unprefixed `svg` step silently
        # matches nothing. With the bare test, not(.//svg) was always true
        # regardless of whether a button actually had an icon, so this
        # matched every row-level function expander ("add Test >", "subtract
        # Test >", ...) in addition to the real submit button — and since
        # find_element/element_to_be_clickable return the first DOM match,
        # click_run_test() was clicking whichever expander came first (just
        # re-toggling its accordion) instead of the real submit button,
        # which is why the Output panel never actually populated.
        self.run_test_button = (
            By.XPATH,
            "//button[normalize-space()='Test' and not(.//*[local-name()='svg'])]"
        )

        self.test_output_panel = (
            By.XPATH,
            "//label[normalize-space()='Output:']/following-sibling::div[1]"
        )

        # Each tool card's options menu (Edit / Delete / Unpublish) is
        # opened via a three-dot "ellipsis-vertical" icon — an <svg>, not a
        # button, so it has no native JS .click() and must be clicked via
        # Selenium's own click() rather than execute_script.
        self.tool_card_kebab_xpath = (
            "//h2[normalize-space()='{tool_name}']"
            "/ancestor::div[contains(@class,'rounded-xl')][1]"
            "//*[contains(@class,'lucide-ellipsis-vertical')]"
        )

        self.delete_menu_item = (
            By.XPATH,
            "//div[normalize-space()='Delete']"
        )

        self.delete_confirmation_heading = (
            By.XPATH,
            "//h2[normalize-space()='Are you sure?']"
        )

        self.confirm_delete_button = (
            By.XPATH,
            "//h2[normalize-space()='Are you sure?']/following::button[normalize-space()='Delete'][1]"
        )

        self.tool_deleted_toast = (
            By.XPATH,
            "//*[contains(@class,'Toastify__toast--success') and contains(.,'Tool Deleted')]"
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

    @allure.step("Choose the 'External MCP URL' build method")
    def choose_mcp_url_tool(self):
        self.wait.until(
            EC.element_to_be_clickable(self.use_urls_button)
        ).click()

    @allure.step("Toggle Authorization Header on")
    def enable_authorization_header(self):
        self.wait.until(
            EC.element_to_be_clickable(self.authorization_header_toggle)
        ).click()

    @allure.step("Enter Authorization Header name '{name}'")
    def enter_header_name(self, name):
        field = self.wait.until(
            EC.element_to_be_clickable(self.header_name_input)
        )
        field.clear()
        field.send_keys(name)

    @allure.step("Enter Authorization Header value")
    def enter_header_value(self, value):
        field = self.wait.until(
            EC.element_to_be_clickable(self.header_value_input)
        )
        field.send_keys(value)

    @allure.step("Save the Authorization Header")
    def click_save_header(self):
        self.wait.until(
            EC.element_to_be_clickable(self.save_header_button)
        ).click()

    @allure.step("Enter MCP URL")
    def enter_mcp_url(self, url):
        field = self.wait.until(
            EC.element_to_be_clickable(self.mcp_url_input)
        )
        field.send_keys(url)

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
    def wait_for_code_generation(self, timeout=600):
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
    def wait_for_tool_creation(self, timeout=600):
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(self.hold_tight_modal)
            )
        except TimeoutException:
            pass

        # The "Tool Created Successfully" toast can fully appear and fade
        # (~5s lifetime) before the "Hold tight" modal itself finishes
        # closing, so it's tracked here via polling throughout this wait
        # rather than checked separately afterwards — checking only after
        # the modal closes risks missing it entirely. The screenshot is
        # captured the instant it's first seen too, since a fresh
        # screenshot taken later (once the caller gets around to it) can
        # just as easily land after the toast has already faded.
        self._tool_created_toast_seen = False
        self._tool_created_toast_screenshot = None
        end_time = time.monotonic() + timeout
        while True:
            if not self._tool_created_toast_seen and self.driver.find_elements(*self.tool_created_toast):
                self._tool_created_toast_seen = True
                self._tool_created_toast_screenshot = self.driver.get_screenshot_as_png()
            if not self.driver.find_elements(*self.hold_tight_modal):
                return
            if time.monotonic() > end_time:
                raise TimeoutException("Timed out waiting for tool creation to complete")
            time.sleep(0.3)

    def get_captured_tool_created_screenshot(self):
        """Returns the screenshot taken at the instant wait_for_tool_creation()
        first saw the 'Tool Created Successfully' toast, or None if it wasn't
        seen — use this instead of a fresh screenshot, which may be taken
        after the toast (short-lived) has already faded."""
        return getattr(self, "_tool_created_toast_screenshot", None)

    def _dismiss_server_error_modal(self, timeout=3):
        # Best-effort: this modal can also disappear on its own between
        # being located and clicked (e.g. the backend retry it's
        # complaining about quietly succeeds), which surfaces as a stale
        # element rather than anything worth failing on.
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable(self.server_error_dismiss_button)
            ).click()
        except (TimeoutException, StaleElementReferenceException):
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
        trigger = self.wait.until(
            EC.element_to_be_clickable(self.upload_code_trigger)
        )
        # A just-fired success toast (e.g. "Tool Created Successfully") can
        # still be overlapping this button's top-right position, which
        # blocks a plain .click(); a JS-dispatched click bypasses that
        # transient overlay instead of failing on it.
        self.driver.execute_script("arguments[0].click();", trigger)
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
        # The Upload Code modal's backdrop can still be mid-close-animation
        # (pointer-events: auto) right after a successful upload, which
        # intercepts a plain click on the button behind it.
        try:
            WebDriverWait(self.driver, 5).until_not(
                EC.presence_of_element_located(self.upload_modal_dropzone_text)
            )
        except TimeoutException:
            pass

        update_btn = self.wait.until(
            EC.element_to_be_clickable(self.update_tool_button)
        )
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", update_btn)
        self.driver.execute_script("arguments[0].click();", update_btn)

    @allure.step("Wait for tool update to complete")
    def wait_for_tool_update(self, timeout=600):
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

    def get_test_function_names(self):
        """Returns every function name listed in the 'Test your tool' panel,
        so callers can exercise all of them without hardcoding names that
        only apply to one specific uploaded file."""
        elements = self.wait.until(
            EC.presence_of_all_elements_located(self.test_function_names)
        )
        return [e.text.strip() for e in elements if e.text.strip()]

    @allure.step("Open the Test panel for function '{function_name}'")
    def open_function_test_panel(self, function_name):
        self._dismiss_server_error_modal()

        expander = self.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, self.function_test_expander_xpath.format(function_name=function_name))
            )
        )
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", expander)
        self.driver.execute_script("arguments[0].click();", expander)

        # Confirms the detail panel actually switched to this function
        # before the caller starts filling its "a"/"b" fields.
        self.wait.until(
            EC.presence_of_element_located((By.XPATH, f"//label[normalize-space()='{function_name}']"))
        )

    def get_open_test_param_names(self):
        """Returns the parameter names (from each 'Enter <name>' input
        placeholder) for whichever function's Test panel is currently open.

        Prompt-generated tools don't have fixed parameter names the way
        calculator.py's add/subtract/multiply/divide do — the LLM decides
        them — so callers need to discover them per function rather than
        assuming 'a'/'b'.

        Scoped to inputs after the 'Functions' label (i.e. within the Test
        your tool panel itself) rather than the whole page — an MCP-URL
        tool's Core Instructions section has its own 'Enter your tool's
        URL' field earlier on the same page, which also starts with
        'Enter ' and would otherwise get picked up as a false parameter.
        """
        inputs = self.driver.find_elements(
            By.XPATH,
            "//label[normalize-space()='Functions']/following::input[starts-with(@placeholder,'Enter ')]"
        )
        return [i.get_attribute("placeholder")[len("Enter "):].strip() for i in inputs]

    @allure.step("Enter test parameter '{param_name}'")
    def enter_test_param(self, param_name, value):
        # A transient "Something went wrong / We're having trouble reaching
        # our servers" modal (see server_error_dismiss_button) can pop up
        # over this panel from an unrelated background request; its
        # backdrop blocks the input, which surfaces as Selenium's generic
        # "invalid element state: not interactable" rather than anything
        # that names the real cause — dismiss it defensively before/while
        # interacting rather than retrying blind on a settle delay.
        self._dismiss_server_error_modal()

        field = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, f"//input[@placeholder='Enter {param_name}']"))
        )
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", field)

        last_error = None
        for _ in range(5):
            try:
                field.clear()
                field.send_keys(value)
                return
            except InvalidElementStateException as e:
                last_error = e
                self._dismiss_server_error_modal()
                time.sleep(0.5)
                field = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, f"//input[@placeholder='Enter {param_name}']"))
                )
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", field)
        raise last_error

    @allure.step("Run the test")
    def click_run_test(self):
        self._dismiss_server_error_modal()
        run_button = self.wait.until(
            EC.element_to_be_clickable(self.run_test_button)
        )
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", run_button)
        run_button.click()

    def get_test_output(self, timeout=10):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(self.test_output_panel)
            ).text
        except TimeoutException:
            return ""

    def wait_for_test_output(self, timeout=30):
        """Waits for the Output panel to show a populated result instead of
        the initial empty '{}', then returns whatever text is present.

        How long this takes can depend on the tool being tested. Always
        returns the current text either way, so a screenshot taken right
        after reflects the real result whenever the backend does respond,
        instead of only ever capturing the initial empty state.
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.find_element(*self.test_output_panel).text.strip() not in ("", "{}")
            )
        except TimeoutException:
            pass
        return self.get_test_output()

    def is_tool_created(self, timeout=10):
        """The 'Create Tool' submit button relabels to 'Update Tool' once the
        tool exists on the server — the clearest signal that creation succeeded."""
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.update_tool_button)
            ).is_displayed()
        except TimeoutException:
            return False

    def is_tool_created_toast_present(self, timeout=10):
        # wait_for_tool_creation() already polled for this toast throughout
        # the whole "Hold tight" modal window, since the toast can fade
        # before the modal closes — trust that result over a fresh check,
        # which would be too late by this point.
        if getattr(self, "_tool_created_toast_seen", False):
            return True
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.tool_created_toast)
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

    def is_tool_card_absent(self, tool_name, timeout=20):
        # The "Tool Deleted Successfully" toast can fire before the tools
        # list has actually re-fetched/re-rendered without the deleted
        # card, so a short wait here can catch it mid-refresh and report a
        # false negative.
        try:
            WebDriverWait(self.driver, timeout).until_not(
                EC.presence_of_element_located(self._case_insensitive_card_locator(tool_name))
            )
            return True
        except TimeoutException:
            pass

        # Confirmed: even 20s isn't always enough — the in-memory list
        # doesn't reliably re-fetch on its own after a delete. A hard
        # refresh forces a real re-fetch from the server instead of relying
        # on the SPA's own (apparently unreliable) live list update.
        self.driver.refresh()
        try:
            WebDriverWait(self.driver, timeout).until_not(
                EC.presence_of_element_located(self._case_insensitive_card_locator(tool_name))
            )
            return True
        except TimeoutException:
            return False

    @allure.step("Open the options menu for tool '{tool_name}'")
    def open_tool_card_menu(self, tool_name):
        kebab = self.wait.until(
            EC.presence_of_element_located(
                (By.XPATH, self.tool_card_kebab_xpath.format(tool_name=tool_name))
            )
        )
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", kebab)
        kebab.click()
        self.wait.until(EC.element_to_be_clickable(self.delete_menu_item))

    @allure.step("Click 'Delete' from the tool options menu")
    def click_delete_tool(self):
        self.wait.until(
            EC.element_to_be_clickable(self.delete_menu_item)
        ).click()
        self.wait.until(
            EC.presence_of_element_located(self.delete_confirmation_heading)
        )

    @allure.step("Confirm tool deletion")
    def confirm_delete_tool(self):
        self.wait.until(
            EC.element_to_be_clickable(self.confirm_delete_button)
        ).click()

    def is_tool_deleted_toast_present(self, timeout=10):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.tool_deleted_toast)
            ).is_displayed()
        except TimeoutException:
            return False
