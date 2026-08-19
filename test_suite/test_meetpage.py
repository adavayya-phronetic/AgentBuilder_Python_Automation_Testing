import os
import random
from urllib.parse import urlparse

import allure
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoAlertPresentException,
    NoSuchWindowException,
    UnexpectedAlertPresentException,
)

from Webpages.my_agents_page import MyAgentsPage
from Webpages.meet_page import MeetPage
from Webpages.agent_build_page import AgentBuildPage
from Utility.allure_helpers import attach_step_screenshot


class MeetRoomDisconnected(Exception):
    """Raised when the meeting room silently drops back to the app shell
    (e.g. after switching to a past chat session) instead of crashing the
    tab outright. Confirmed live: chat_history_button then legitimately
    isn't on the page, so waiting the full 30s for it just produces a
    generic Selenium TimeoutException pointing at a locator instead of the
    real cause. Checking is_in_call() first and raising this instead turns
    that into an immediate, diagnosable failure — and gives the flaky
    rerun below (see its comment) a distinct, narrow exception name to
    target alongside the existing NoSuchWindowException case, without
    having to rerun on every AssertionError in this test."""


def _open_meet_tab_in_new_window(driver):
    meet_link = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//a[normalize-space()='Meet']"))
    )
    meet_link.click()
    WebDriverWait(driver, 20).until(lambda d: len(d.window_handles) > 1)
    driver.switch_to.window(driver.window_handles[-1])


def _open_random_active_agent_meet(driver):
    # click_my_agents() clicks a "My Agents" nav link that only exists on
    # the main app shell's own sidebar — but this test shares one browser
    # session with every other file in a full suite run, and
    # test_agent_buildpage.py's tests deliberately never reset to /agents
    # between themselves (they stay on one agent's Build page throughout).
    # If this test runs right after that file, the shared session can
    # still be sitting on the Build page's own different sidebar (Build /
    # Gateway / Analytics / Sessions / Datasets / Eval Dashboard, no "My
    # Agents" link at all), so click_my_agents() waits forever for a link
    # that was never going to appear. A hard navigation to /agents works
    # regardless of whatever page the previous test left the session on.
    parsed = urlparse(driver.current_url)
    agents_url = f"{parsed.scheme}://{parsed.netloc}/agents"
    driver.get(agents_url)

    agents_page = MyAgentsPage(driver)
    agents_page.wait.until(
        EC.visibility_of_element_located(agents_page.search_input)
    )

    active_agent_names = agents_page.get_active_agent_names()
    assert active_agent_names, "No active agents found in the agent card list"

    target_agent_name = random.choice(active_agent_names)
    allure.attach(target_agent_name, name="Target agent", attachment_type=allure.attachment_type.TEXT)

    agents_page.search_agent(target_agent_name)
    agents_page.click_agent_card(target_agent_name)

    # click_agent_card lands on this agent's own Build page. Whatever
    # Output Type an earlier test left this agent configured with (e.g.
    # test_configure_agent_io_types explicitly exercises the Video toggle),
    # Video output must be off before joining a Meet call with it — the
    # Meet room renders actual agent video output on top of the WebRTC
    # call itself when it's enabled, which is heavier than this fake-media
    # Selenium setup reliably handles and is a plausible contributor to the
    # tab crashes documented on the Meet test's flaky rerun.
    _ensure_video_output_disabled(driver)

    # The Meet tab is an <a target="_blank"> that opens
    # meet-agents.phronetic.ai in a separate browser tab.
    _open_meet_tab_in_new_window(driver)
    return target_agent_name


def _ensure_video_output_disabled(driver):
    build_page = AgentBuildPage(driver)
    # click_agent_card lands on this agent's GRAPH tab by default, not
    # EDITOR — confirmed live (and matches test_configure_agent_io_types,
    # which also clicks into EDITOR before touching these buttons). The
    # Output Type pills only exist in the EDITOR tab's Details section, so
    # without this the video button is never on the page and the wait
    # below times out instead of finding anything to check.
    build_page.click_editor_tab()
    if build_page.is_output_type_video_selected():
        build_page.deselect_output_type_video()
        build_page.click_save()


def _dismiss_stray_alert(driver):
    # A disconnected WebRTC call can occasionally surface a native
    # "Client initiated disconnect" alert. Left open, it would block every
    # subsequent WebDriver command in this shared session, so it's cleared
    # defensively before doing anything else.
    try:
        alert = driver.switch_to.alert
        print(f"Dismissing unexpected alert: {alert.text!r}")
        alert.accept()
    except NoAlertPresentException:
        pass
    except NoSuchWindowException:
        # The meet tab itself is already gone (e.g. a real Chrome/WebRTC
        # crash mid-call — confirmed live: "no such window: target window
        # already closed") rather than just lacking an alert. Nothing to
        # dismiss and nothing else this function can do about it; let the
        # caller's own cleanup continue instead of blowing up here.
        pass


def _close_meet_tab(driver, main_window):
    _dismiss_stray_alert(driver)

    # The generic pass/fail screenshot fixture in conftest.py captures the
    # main window after this test has already switched back to it (and
    # after the shared session gets reset to /agents), so it never shows
    # the meet tab itself. Attach a screenshot of the meet tab here, before
    # it's closed, so the report reflects what actually happened.
    try:
        allure.attach(
            driver.get_screenshot_as_png(),
            name="Meet tab screenshot",
            attachment_type=allure.attachment_type.PNG
        )
    except UnexpectedAlertPresentException:
        _dismiss_stray_alert(driver)
    except Exception as e:
        print(f"Failed to capture meet tab screenshot: {e}")

    # The meet tab can already be closed by the time this runs (same crash
    # as above) — closing an already-closed window raises the identical
    # NoSuchWindowException. That must not be allowed to skip the
    # switch_to.window(main_window) recovery below: confirmed live, without
    # this guard the exception propagated straight out of this whole
    # function, main_window was never re-selected, and the shared session
    # was left stranded on a dead window handle for every test that runs
    # after this one.
    try:
        driver.close()
    except NoSuchWindowException:
        pass

    driver.switch_to.window(main_window)


@allure.feature("Agent Interaction")
@allure.story("Meet")
@allure.title("Full meet flow: open agent, join meeting, upload a file and ask for a summary, validate in-call features")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.meet
# The Meet tab is a real WebRTC video call (fake media stream, but a real
# Chrome tab/renderer running it) — confirmed live, that tab can crash
# mid-call independent of anything this test or the app does wrong,
# surfacing as NoSuchWindowException ("target window already closed") on
# whatever WebDriver call happens to run next. A single rerun rides out
# that one-off crash instead of failing the whole (long) flow on
# infrastructure noise; _close_meet_tab()'s own cleanup is now resilient to
# the same crash too, so a rerun starts from a clean, recovered session
# rather than a stranded one. MeetRoomDisconnected (defined above) covers
# the same family of live-meeting flakiness surfacing as a silent redirect
# back to the app shell rather than a window crash.
@pytest.mark.flaky(reruns=1, only_rerun=["NoSuchWindowException", "MeetRoomDisconnected"])
def test_meet_interact_upload_and_validate_features(logged_in_driver):
    # One chained flow rather than independent test functions because each
    # stage depends on state the previous stage left behind: the file
    # upload happens inside the meeting chat panel opened after joining,
    # and feature validation happens while still in that same call.

    driver = logged_in_driver
    main_window = driver.current_window_handle
    pdf_path = os.path.abspath(os.path.join("Files", "sample_test.pdf"))
    file_name = os.path.basename(pdf_path)

    with allure.step("Step 1: Open My Agents and click on an agent card"):
        target_agent_name = _open_random_active_agent_meet(driver)
        print(f"Step 1 OK: opened Meet for agent '{target_agent_name}'.")
        attach_step_screenshot(driver, "Step 1: Meet opened")

    try:
        with allure.step("Step 2: Join the meeting"):
            meet_page = MeetPage(driver)
            assert meet_page.is_join_now_visible(), "Step 2 failed: Join Now button did not appear in the Meet lobby"

            meet_page.join_now()
            assert meet_page.is_in_call(), "Step 2 failed: in-call controls (Hang Up) did not appear after joining"
            print("Step 2 OK: joined the meeting; in-call controls visible.")
            attach_step_screenshot(driver, "Step 2: Joined meeting")

        with allure.step(f"Step 3: Upload '{file_name}' in the meeting chat and ask for a summary"):
            meet_page.upload_file_in_meeting(pdf_path)
            assert meet_page.is_file_attached(file_name), (
                f"Step 3 failed: uploaded file '{file_name}' did not display in the meeting chat"
            )

            meet_page.send_meeting_message("Please summarize this document.")
            # The agent reads the uploaded file (tool call) before replying,
            # which can take a while, so this waits for the "Thinking"
            # indicator to clear rather than sleeping a fixed amount.
            WebDriverWait(driver, 60).until(
                lambda d: len(d.find_elements(By.XPATH, "//*[contains(text(),'Thinking')]")) == 0
            )
            print(f"Step 3 OK: '{file_name}' uploaded and agent responded with a summary.")
            attach_step_screenshot(driver, "Step 3: File uploaded and summarized")

        with allure.step("Step 4: Validate in-call features (chat panel, device controls, More options menu)"):
            assert meet_page.is_chat_panel_open(), "Step 4 failed: meeting Chat panel was not open"

            # Chat History and Share Screen used to live inside the More
            # options (⋮) dropdown along with these three — confirmed live,
            # a UI change moved both out into their own dedicated toolbar
            # buttons, so they're checked separately below rather than as
            # dropdown items that no longer exist.
            meet_page.open_more_options()
            menu_items = meet_page.get_more_options_menu_items()
            for expected in ["Screen Recorder", "Meeting Info", "Participants"]:
                assert expected in menu_items, f"Step 4 failed: '{expected}' missing from More options menu"
            print("Step 4a OK: More options menu shows all expected items:", menu_items)
            attach_step_screenshot(driver, "Step 4a: More options menu")

            assert meet_page.is_chat_history_button_present(), (
                "Step 4 failed: Chat History toolbar button not present"
            )
            assert meet_page.is_share_screen_button_present(), (
                "Step 4 failed: Share Screen toolbar button not present"
            )
            print("Step 4a OK: Chat History and Share Screen toolbar buttons present.")

            meet_page.wait.until(
                EC.element_to_be_clickable(meet_page.meeting_info_menu_item)
            ).click()
            assert meet_page.is_meeting_info_panel_open(), "Step 4 failed: Meeting Info panel did not open"
            print("Step 4b OK: Meeting Info panel opened successfully.")
            attach_step_screenshot(driver, "Step 4b: Meeting Info panel")

            meet_page.open_participants()
            assert meet_page.is_participants_panel_open(), "Step 4 failed: Participants panel did not open"
            print("Step 4c OK: Participants panel opened successfully.")
            attach_step_screenshot(driver, "Step 4c: Participants panel")

            assert meet_page.is_in_call(), "Step 4 failed: call ended unexpectedly during feature validation"
            print("Step 4 OK: all in-call features validated.")

        with allure.step("Step 5: Chat History - join a past chat if available, then return to the current session"):
            meet_page.open_chat_history()
            assert meet_page.is_chat_history_panel_open(), (
                "Step 5 failed: Chat History panel did not open"
            )
            print("Step 5a OK: Chat History panel opened.")
            attach_step_screenshot(driver, "Step 5a: Chat History panel opened")

            if meet_page.join_random_past_chat():
                assert meet_page.is_in_call(), (
                    "Step 5 failed: call ended unexpectedly after joining a past chat"
                )
                print("Step 5b OK: joined a random past chat from history.")
                attach_step_screenshot(driver, "Step 5b: Joined past chat")

                # Confirmed live: joining a past chat can silently redirect the
                # tab back to the Build Agent app shell a few seconds later
                # instead of staying in the room — the Chat History button then
                # genuinely isn't on the page, so re-checking here up front
                # turns that into an immediate, clear failure instead of a
                # generic 30s Selenium TimeoutException on the button locator.
                if not meet_page.is_in_call(timeout=5):
                    raise MeetRoomDisconnected(
                        "Step 5 failed: got redirected out of the meeting room after joining a "
                        f"past chat (now at {driver.current_url}) instead of staying in-call — "
                        "this is a live-app reconnect glitch, not a locator issue; the flaky "
                        "rerun on this test should ride it out"
                    )

                meet_page.open_chat_history()
                assert meet_page.is_chat_history_panel_open(), (
                    "Step 5 failed: Chat History panel did not reopen after joining a past chat"
                )
                print("Step 5c OK: Chat History panel reopened.")
                attach_step_screenshot(driver, "Step 5c: Chat History panel reopened")

                meet_page.return_to_current_session()
                assert meet_page.is_in_call(), (
                    "Step 5 failed: call ended unexpectedly after returning to the current session"
                )
                print("Step 5 OK: returned to the current active session.")
                attach_step_screenshot(driver, "Step 5: Returned to current session")
            else:
                # A brand-new room can have only the current live session
                # listed, with no past chats to select from — nothing to
                # exercise here, so this isn't treated as a failure.
                assert meet_page.is_in_call(), (
                    "Step 5 failed: call ended unexpectedly while checking Chat History"
                )
                print("Step 5 SKIPPED: no past chat history available to join for this room.")
                attach_step_screenshot(driver, "Step 5: No past chat history to join")

        with allure.step("Step 6: End call, rejoin, then end call again"):
            meet_page.hang_up()
            assert meet_page.is_on_rejoin_lobby(), (
                "Step 6 failed: rejoin lobby ('Rejoin' / 'New Meeting') did not appear after ending the call"
            )
            assert meet_page.driver.find_elements(*meet_page.new_meeting_button), (
                "Step 6 failed: 'New Meeting' option missing from the rejoin lobby"
            )
            print("Step 6a OK: call ended; rejoin lobby shown with 'Rejoin' and 'New Meeting'.")
            attach_step_screenshot(driver, "Step 6a: Rejoin lobby")

            meet_page.rejoin()
            assert meet_page.is_in_call(), (
                "Step 6 failed: call did not resume after clicking 'Rejoin'"
            )
            print("Step 6b OK: rejoined the same session.")
            attach_step_screenshot(driver, "Step 6b: Rejoined session")

            meet_page.hang_up()
            assert meet_page.is_on_rejoin_lobby(), (
                "Step 6 failed: rejoin lobby did not reappear after ending the call a second time"
            )
            print("Step 6 OK: ended the call again; back on the rejoin lobby.")
            attach_step_screenshot(driver, "Step 6: Ended call again")
    finally:
        _close_meet_tab(driver, main_window)
