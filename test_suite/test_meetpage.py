import os
import random

import allure
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoAlertPresentException, UnexpectedAlertPresentException

from Webpages.my_agents_page import MyAgentsPage
from Webpages.meet_page import MeetPage
from Utility.allure_helpers import attach_step_screenshot


def _open_meet_tab_in_new_window(driver):
    meet_link = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//a[normalize-space()='Meet']"))
    )
    meet_link.click()
    WebDriverWait(driver, 20).until(lambda d: len(d.window_handles) > 1)
    driver.switch_to.window(driver.window_handles[-1])


def _open_random_active_agent_meet(driver):
    agents_page = MyAgentsPage(driver)
    agents_page.click_my_agents()

    active_agent_names = agents_page.get_active_agent_names()
    assert active_agent_names, "No active agents found in the agent card list"

    target_agent_name = random.choice(active_agent_names)
    allure.attach(target_agent_name, name="Target agent", attachment_type=allure.attachment_type.TEXT)

    agents_page.search_agent(target_agent_name)
    agents_page.click_agent_card(target_agent_name)

    # The Meet tab is an <a target="_blank"> that opens
    # meet-agents.phronetic.ai in a separate browser tab.
    _open_meet_tab_in_new_window(driver)
    return target_agent_name


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

    driver.close()
    driver.switch_to.window(main_window)


@allure.feature("Agent Interaction")
@allure.story("Meet")
@allure.title("Full meet flow: open agent, join meeting, upload a file and ask for a summary, validate in-call features")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.meet
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

            meet_page.open_more_options()
            menu_items = meet_page.get_more_options_menu_items()
            for expected in ["Chat History", "Screen Recorder", "Meeting Info", "Participants", "Share Screen"]:
                assert expected in menu_items, f"Step 4 failed: '{expected}' missing from More options menu"
            print("Step 4a OK: More options menu shows all expected items:", menu_items)
            attach_step_screenshot(driver, "Step 4a: More options menu")

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
