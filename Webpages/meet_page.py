import random
import time

import allure
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
    NoSuchWindowException,
)


class MeetPage:
    # The "Meet" tab on an agent's toolbar is an <a target="_blank"> to
    # meet-agents.phronetic.ai/<agent_id>/rooms/<room_id> and opens in a new
    # browser tab, so callers must switch to that window handle before
    # constructing this page object. Covers the pre-join lobby (Join Now)
    # and the in-call view reached via join_now() (meeting chat, More
    # options menu, Hang Up).

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 30)
        self._guard_against_crashed_tab_finds()

    def _guard_against_crashed_tab_finds(self):
        # The Meet tab's WebRTC renderer can crash mid-call independent of
        # anything this test does (see the flaky-rerun comment on the test
        # itself, which already handles the usual NoSuchWindowException
        # shape of that crash). Confirmed live: when the crash lands mid
        # find_element instead, chromedriver's response can come back with
        # no 'value', so Selenium's find_element() returns None rather than
        # raising. That None then reaches expected_conditions'
        # _element_if_visible, which calls None.is_displayed() and blows up
        # with a confusing AttributeError far from the real cause — and one
        # the existing flaky rerun doesn't recognize, so the test fails
        # outright instead of riding out infra noise it's designed to
        # tolerate. Wrapping find_element here turns that back into the
        # same NoSuchWindowException every other crash path already
        # produces. Guarded by a flag on the driver itself since the same
        # shared session-scoped driver can construct several MeetPage
        # instances across a run.
        if getattr(self.driver, "_crashed_tab_find_guard_applied", False):
            return

        original_find_element = self.driver.find_element

        def _guarded_find_element(*args, **kwargs):
            element = original_find_element(*args, **kwargs)
            if element is None:
                raise NoSuchWindowException(
                    "find_element returned no element — the meet tab most "
                    "likely crashed mid-call"
                )
            return element

        self.driver.find_element = _guarded_find_element
        self.driver._crashed_tab_find_guard_applied = True

        self.join_now_button = (
            By.XPATH,
            "//button[normalize-space()='Join Now']"
        )

        # --- Post-call "rejoin" lobby (after hang_up()) ---
        # Hanging up doesn't close the tab — it returns to a lobby offering
        # either "Rejoin" (same session) or "New Meeting".
        self.rejoin_button = (
            By.XPATH,
            "//button[normalize-space()='Rejoin']"
        )

        self.new_meeting_button = (
            By.XPATH,
            "//button[normalize-space()='New Meeting']"
        )

        # --- In-call view (after join_now()) ---

        self.hang_up_button = (
            By.XPATH,
            "//button[@aria-label='Hang Up']"
        )

        self.chat_panel_toggle = (
            By.XPATH,
            "//button[@title='Chat']"
        )

        # Unlike the standalone Chat page (a real <textarea>), the meeting
        # chat composer is a contenteditable div using a custom
        # data-placeholder attribute rather than the native HTML
        # placeholder attribute — confirmed by direct DOM inspection after
        # a plain "//textarea[@placeholder=...]" locator never matched it.
        self.meeting_message_input = (
            By.XPATH,
            "//div[@contenteditable='true' and @data-placeholder=\"Type your message...\"]"
        )

        self.meeting_send_button = (
            By.XPATH,
            "//button[@type='submit' and contains(@class,'bg-blue')]"
        )

        self.meeting_file_input = (
            By.XPATH,
            "//input[@type='file']"
        )

        self.more_options_button = (
            By.XPATH,
            "//button[@title='More options']"
        )

        # Items inside the "More options" (⋮) dropdown itself. Chat History
        # and Share Screen used to live here too, but a live UI change moved
        # both out into their own dedicated icon-only toolbar buttons
        # (title='Chat History' / title='Share Screen', no visible text) —
        # confirmed live: the dropdown now only ever contains these three,
        # and the two moved-out buttons have real, working locators of
        # their own below rather than text-matching a menu item that no
        # longer exists. Screen Recorder is only checked for presence,
        # never clicked — it requires an OS-level permission dialog
        # Selenium can't drive.
        self.screen_recorder_menu_item = (
            By.XPATH,
            "//*[self::button or self::li][normalize-space()='Screen Recorder']"
        )

        self.meeting_info_menu_item = (
            By.XPATH,
            "//*[self::button or self::li][normalize-space()='Meeting Info']"
        )

        self.participants_menu_item = (
            By.XPATH,
            "//*[self::button or self::li][normalize-space()='Participants']"
        )

        # Standalone toolbar buttons (see note above) — icon-only, identified
        # by their title attribute rather than visible text. Share Screen is
        # only checked for presence, never clicked — same OS-permission-
        # dialog reason as Screen Recorder above.
        self.chat_history_button = (
            By.XPATH,
            "//button[@title='Chat History']"
        )

        self.share_screen_button = (
            By.XPATH,
            "//button[@title='Share Screen']"
        )

        # Panel headers shown in the right-hand panel once opened.
        self.meeting_info_panel_heading = (
            By.XPATH,
            "//*[normalize-space()='Meeting details']"
        )

        self.participants_panel_heading = (
            By.XPATH,
            "//*[normalize-space()='People']"
        )

        # --- Chat History panel ---
        # Lists past chat sessions, each with a "Join" button, plus a
        # "Current Session • LIVE" row. That row shows "Viewing" while the
        # live session is what's on screen, and switches to "Return" once a
        # past chat has been joined instead.
        self.chat_history_panel_heading = (
            By.XPATH,
            "//*[normalize-space()='Your Chats']"
        )

        self.chat_history_join_buttons = (
            By.XPATH,
            "//button[normalize-space()='Join']"
        )

        self.chat_history_return_button = (
            By.XPATH,
            "//button[normalize-space()='Return']"
        )

        self.current_session_viewing_button = (
            By.XPATH,
            "//button[normalize-space()='Viewing']"
        )

    def _click(self, locator, retries=3):
        # A JS click bypasses transient overlays (toast notifications, etc.)
        # that can intercept a normal Selenium click on these buttons. The
        # retry loop additionally covers toolbar re-renders (e.g. right
        # after switching sessions in Chat History) that can invalidate the
        # element reference between locating it and clicking it.
        for attempt in range(retries):
            try:
                element = self.wait.until(EC.presence_of_element_located(locator))
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
                self.driver.execute_script("arguments[0].click();", element)
                return
            except StaleElementReferenceException:
                if attempt == retries - 1:
                    raise

    @allure.step("Join the meeting")
    def join_now(self):
        self.wait.until(
            EC.element_to_be_clickable(self.join_now_button)
        ).click()
        # The WebRTC handshake needs a moment after the in-call controls
        # first render before the room is actually stable enough to
        # interact with (chat panel, device toggles, etc.).
        self.wait.until(
            EC.visibility_of_element_located(self.hang_up_button)
        )
        time.sleep(2)

    def is_join_now_visible(self, timeout=10):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.join_now_button)
            ).is_displayed()
        except TimeoutException:
            return False

    def is_in_call(self, timeout=15):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.hang_up_button)
            ).is_displayed()
        except TimeoutException:
            return False

    @allure.step("Hang up the call")
    def hang_up(self):
        # Transient toast notifications (e.g. connection status messages)
        # can overlap the Hang Up button and intercept a normal click, so
        # this uses the same JS-click fallback as the lobby's _click helper.
        self._click(self.hang_up_button)

    def is_on_rejoin_lobby(self, timeout=15):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.rejoin_button)
            ).is_displayed()
        except TimeoutException:
            return False

    @allure.step("Rejoin the same meeting session")
    def rejoin(self):
        # A transient modal backdrop (page-transition overlay) can still be
        # fading out right as the button becomes clickable, intercepting a
        # plain click — same JS-click fallback as hang_up()/_click() below.
        self._click(self.rejoin_button)
        # Same WebRTC handshake settle as the initial join_now().
        self.wait.until(
            EC.visibility_of_element_located(self.hang_up_button)
        )
        time.sleep(2)

    def _ensure_chat_panel_open(self):
        # The panel is open by default right after joining in most cases,
        # but can lag the in-call controls slightly, so this waits before
        # falling back to clicking the Chat toggle.
        try:
            WebDriverWait(self.driver, 20).until(
                EC.visibility_of_element_located(self.meeting_message_input)
            )
            return
        except TimeoutException:
            pass

        self._click(self.chat_panel_toggle)
        self.wait.until(
            EC.visibility_of_element_located(self.meeting_message_input)
        )

    def is_chat_panel_open(self, timeout=10):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.meeting_message_input)
            ).is_displayed()
        except TimeoutException:
            return False

    @allure.step("Send meeting chat message '{message}'")
    def send_meeting_message(self, message):
        self._ensure_chat_panel_open()

        field = self.wait.until(
            EC.element_to_be_clickable(self.meeting_message_input)
        )
        field.click()
        field.send_keys(message)

        self.wait.until(
            EC.element_to_be_clickable(self.meeting_send_button)
        ).click()

    @allure.step("Upload '{file_path}' in the meeting chat")
    def upload_file_in_meeting(self, file_path):
        self._ensure_chat_panel_open()

        file_input = self.wait.until(
            EC.presence_of_element_located(self.meeting_file_input)
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

    @allure.step("Open More options menu")
    def open_more_options(self):
        # The menu stays open once expanded (selecting an item switches the
        # active panel rather than closing the menu), so clicking the
        # toggle again would close it instead of doing nothing — only open
        # it if it isn't already. A stale reference here (e.g. right after
        # a Chat History session switch re-renders the toolbar) means the
        # old menu is gone, not that a new one is open, so it's treated the
        # same as "not found".
        existing = self.driver.find_elements(*self.participants_menu_item)
        try:
            if existing and existing[0].is_displayed():
                return
        except StaleElementReferenceException:
            pass
        # A plain wait+.click() can hit a stale element reference if the
        # toolbar re-renders between locating the button and clicking it
        # (e.g. right after switching sessions in Chat History), so this
        # uses the same re-locate-then-JS-click helper as hang_up().
        self._click(self.more_options_button)

        # Confirmed reproducible right after Step 3's heavy upload+response
        # wait: the menu opens, but its items can still be mid-render at
        # that exact moment and not show up within
        # get_more_options_menu_items()'s own per-item wait, even though
        # the same locators find them instantly on a fresh, non-rushed
        # open. Waiting for one item's actual presence here adapts to how
        # long rendering genuinely takes on a given run, rather than
        # gambling on a fixed sleep.
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located(self.participants_menu_item)
            )
        except TimeoutException:
            pass

    def get_more_options_menu_items(self, timeout=10):
        """Returns the visible text of every item currently shown in the More
        options (⋮) dropdown — Screen Recorder, Meeting Info, Participants.

        Chat History and Share Screen used to live in this same dropdown,
        but a live UI change moved both out into their own dedicated
        toolbar buttons (see chat_history_button / share_screen_button) —
        checking for them here would wait out the full timeout on every
        call for something that will never appear again.
        """
        items = []
        for locator in (
            self.screen_recorder_menu_item,
            self.meeting_info_menu_item,
            self.participants_menu_item,
        ):
            try:
                el = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located(locator)
                )
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", el
                )
                WebDriverWait(self.driver, timeout).until(
                    lambda d, e=el: e.is_displayed()
                )
                items.append(el.text.strip())
            except TimeoutException:
                pass
        return items

    @allure.step("Open Participants from More options")
    def open_participants(self):
        self.open_more_options()
        self.wait.until(
            EC.element_to_be_clickable(self.participants_menu_item)
        ).click()

    def is_meeting_info_panel_open(self, timeout=10):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.meeting_info_panel_heading)
            ).is_displayed()
        except TimeoutException:
            return False

    def is_participants_panel_open(self, timeout=10):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.participants_panel_heading)
            ).is_displayed()
        except TimeoutException:
            return False

    @allure.step("Open Chat History")
    def open_chat_history(self):
        # A standalone toolbar button now, not a "More options" dropdown
        # item (see chat_history_button) — no need to open that menu first.
        self._click(self.chat_history_button)

    def is_chat_history_panel_open(self, timeout=10):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.chat_history_panel_heading)
            ).is_displayed()
        except TimeoutException:
            return False

    def is_chat_history_button_present(self, timeout=10):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.chat_history_button)
            ).is_displayed()
        except TimeoutException:
            return False

    def is_share_screen_button_present(self, timeout=10):
        # Presence only, never clicked — same OS-permission-dialog reason
        # as Screen Recorder.
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.share_screen_button)
            ).is_displayed()
        except TimeoutException:
            return False

    @allure.step("Join a random past chat from Chat History")
    def join_random_past_chat(self, timeout=5):
        """Returns True if a past chat was joined. Returns False if there
        was no chat history to join — e.g. a brand-new room that only has
        the current live session and no past chats listed — rather than
        waiting out the full default timeout for buttons that will never
        appear."""
        try:
            join_buttons = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_all_elements_located(self.chat_history_join_buttons)
            )
        except TimeoutException:
            return False

        # Joining collapses the Chat History panel back into the in-call
        # view, so the panel must be reopened afterwards for anything else.
        chosen = random.choice(join_buttons)
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", chosen)
        self.driver.execute_script("arguments[0].click();", chosen)

        # Switching sessions tears down and re-establishes the in-call view
        # much like the initial WebRTC join handshake in join_now(), so the
        # toolbar keeps re-rendering for a beat after the button becomes
        # clickable — the same fixed pause used there is needed again here
        # before anything else touches the toolbar.
        self.wait.until(
            EC.element_to_be_clickable(self.more_options_button)
        )
        time.sleep(3)
        return True

    @allure.step("Return to the current active session from Chat History")
    def return_to_current_session(self):
        self._click(self.chat_history_return_button)
        self.wait.until(
            EC.element_to_be_clickable(self.more_options_button)
        )
        time.sleep(3)

    def is_viewing_current_session(self, timeout=10):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.current_session_viewing_button)
            ).is_displayed()
        except TimeoutException:
            return False

    def get_current_url(self):
        return self.driver.current_url
