import random

import allure
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


class ChatPage:
    # The "Chat" tab on an agent's toolbar is an <a target="_blank"> to
    # chat.phronetic.ai/<agent_id>/chat and opens in a new browser tab, so
    # callers must switch to that window handle before constructing this
    # page object.

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 30)

        self.message_input = (
            By.XPATH,
            "//textarea[@placeholder='Type your message...']"
        )

        # The primary send action is the larger, blue-styled icon button
        # in the input bar (distinct from the smaller grey attach-file icon
        # button that sits alongside it).
        self.send_button = (
            By.XPATH,
            "//button[contains(@class,'bg-blue') and contains(@class,'w-10')]"
        )

        self.new_chat_button = (
            By.XPATH,
            "//button[normalize-space()='New chat']"
        )

        self.file_input = (
            By.XPATH,
            "//input[@type='file']"
        )

        self.view_agent_details_link = (
            By.XPATH,
            "//span[normalize-space()='View agent details']"
        )

        self.back_to_chat_button = (
            By.XPATH,
            "//button[normalize-space()='Back to Chat']"
        )

        self.usage_history_tab = (
            By.XPATH,
            "//button[normalize-space()='Usage History']"
        )

        # The "Room Name" column header only renders once the usage
        # history table itself has loaded, not just the tab/heading, so
        # it's a stronger signal that the panel actually displayed data.
        self.usage_history_table_header = (
            By.XPATH,
            "//*[normalize-space()='Room Name']"
        )

        # The profile section (bottom-left, e.g. "Adavayya") opens a popover
        # with Report a Bug and Logout options.
        self.profile_menu_button = (
            By.XPATH,
            "//button[@aria-haspopup='dialog']"
        )

        self.report_a_bug_button = (
            By.XPATH,
            "//button[normalize-space()='Report a Bug']"
        )

        self.bug_description_textarea = (
            By.XPATH,
            "//textarea[@placeholder='Describe the bug and steps to reproduce it...']"
        )

        self.submit_bug_button = (
            By.XPATH,
            "//button[normalize-space()='Submit Bug']"
        )

        self.bug_report_success_heading = (
            By.XPATH,
            "//*[normalize-space()='Bug reported!']"
        )

        self.close_bug_modal_button = (
            By.XPATH,
            "//button[normalize-space()='Close']"
        )

        self.logout_button = (
            By.XPATH,
            "//button[normalize-space()='Logout']"
        )

        # --- Recharge / Add Funds ---
        # "Recharge" (next to the balance) also lands on the agent details
        # page, the same place "View agent details" goes.
        self.recharge_link = (
            By.XPATH,
            "//*[normalize-space()='Recharge']"
        )

        self.add_funds_button = (
            By.XPATH,
            "//*[normalize-space()='+ Add Funds' or normalize-space()='Add Funds']"
        )

        self.add_funds_modal_heading = (
            By.XPATH,
            "//*[normalize-space()='Add Funds to Wallet']"
        )

        self.recharge_preset_amount_buttons = (
            By.XPATH,
            "//button[normalize-space()='+20' or normalize-space()='+50' or normalize-space()='+100']"
        )

        self.recharge_amount_input = (
            By.XPATH,
            "//input[@placeholder='Enter amount']"
        )

        self.recharge_continue_button = (
            By.XPATH,
            "//button[normalize-space()='Continue']"
        )

    @allure.step("Send chat message '{message}'")
    def send_message(self, message):
        field = self.wait.until(
            EC.element_to_be_clickable(self.message_input)
        )
        field.click()
        field.send_keys(message)

        self.wait.until(
            EC.element_to_be_clickable(self.send_button)
        ).click()

    @allure.step("Start a new chat")
    def start_new_chat(self):
        self.wait.until(
            EC.element_to_be_clickable(self.new_chat_button)
        ).click()

    def is_message_input_visible(self, timeout=10):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.message_input)
            ).is_displayed()
        except TimeoutException:
            return False

    @allure.step("Upload '{file_path}' in chat")
    def upload_file(self, file_path):
        # The visible attach icon opens a native OS file dialog Selenium
        # can't drive, so the path is sent directly to the underlying
        # hidden <input type="file"> instead.
        file_input = self.wait.until(
            EC.presence_of_element_located(self.file_input)
        )
        file_input.send_keys(file_path)

    def is_file_attached(self, file_name, timeout=10):
        locator = (By.XPATH, f"//*[contains(text(),'{file_name}')]")
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(locator)
            ).is_displayed()
        except TimeoutException:
            return False

    @allure.step("Click 'View agent details'")
    def click_view_agent_details(self):
        self.wait.until(
            EC.element_to_be_clickable(self.view_agent_details_link)
        ).click()

    @allure.step("Click 'Back to Chat'")
    def click_back_to_chat(self):
        self.wait.until(
            EC.element_to_be_clickable(self.back_to_chat_button)
        ).click()

    @allure.step("Click the 'Usage History' tab")
    def click_usage_history_tab(self):
        self.wait.until(
            EC.element_to_be_clickable(self.usage_history_tab)
        ).click()

    def is_usage_history_visible(self, timeout=10):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.usage_history_table_header)
            ).is_displayed()
        except TimeoutException:
            return False

    @allure.step("Open the profile menu")
    def open_profile_menu(self):
        self.wait.until(
            EC.element_to_be_clickable(self.profile_menu_button)
        ).click()

    @allure.step("Open Report a Bug from the profile menu")
    def click_report_a_bug(self):
        self.open_profile_menu()
        self.wait.until(
            EC.element_to_be_clickable(self.report_a_bug_button)
        ).click()

    @allure.step("Submit bug report: '{description}'")
    def submit_bug_report(self, description):
        textarea = self.wait.until(
            EC.element_to_be_clickable(self.bug_description_textarea)
        )
        textarea.click()
        textarea.send_keys(description)

        self.wait.until(
            EC.element_to_be_clickable(self.submit_bug_button)
        ).click()

    def is_bug_report_successful(self, timeout=15):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.bug_report_success_heading)
            ).is_displayed()
        except TimeoutException:
            return False

    @allure.step("Close the bug report confirmation")
    def close_bug_report_modal(self):
        self.wait.until(
            EC.element_to_be_clickable(self.close_bug_modal_button)
        ).click()

    @allure.step("Logout from the profile menu")
    def logout(self):
        self.open_profile_menu()
        self.wait.until(
            EC.element_to_be_clickable(self.logout_button)
        ).click()

    @allure.step("Click 'Recharge'")
    def click_recharge(self):
        self.wait.until(
            EC.element_to_be_clickable(self.recharge_link)
        ).click()

    @allure.step("Open the 'Add Funds to Wallet' modal")
    def open_add_funds_modal(self):
        self.wait.until(
            EC.element_to_be_clickable(self.add_funds_button)
        ).click()

    def is_add_funds_modal_open(self, timeout=10):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.add_funds_modal_heading)
            ).is_displayed()
        except TimeoutException:
            return False

    @allure.step("Pick a recharge amount")
    def pick_random_recharge_amount(self):
        # The modal supports two equally valid ways to choose an amount: tap
        # one of the preset chips (+20/+50/+100) or type a custom amount
        # into the input, so this randomly exercises either path.
        if random.choice([True, False]):
            presets = self.wait.until(
                EC.presence_of_all_elements_located(self.recharge_preset_amount_buttons)
            )
            chosen = random.choice(presets)
            label = chosen.text.strip()
            chosen.click()
            return label
        else:
            amount = str(random.choice([15, 25, 30, 40, 75]))
            field = self.wait.until(
                EC.element_to_be_clickable(self.recharge_amount_input)
            )
            field.clear()
            field.send_keys(amount)
            return amount

    @allure.step("Click 'Continue' to proceed to billing")
    def click_continue_to_billing(self):
        self.wait.until(
            EC.element_to_be_clickable(self.recharge_continue_button)
        ).click()

    def get_current_url(self):
        return self.driver.current_url
