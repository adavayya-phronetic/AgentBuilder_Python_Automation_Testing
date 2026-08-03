import os
import random
from urllib.parse import urlparse

import allure
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from Webpages.landing_page import LandingPage
from Webpages.login_page import LoginPage
from Webpages.my_agents_page import MyAgentsPage
from Webpages.chat_page import ChatPage
from Utility import config
from Utility.allure_helpers import attach_step_screenshot, attach_and_save_screenshot


def _open_chat_tab_in_new_window(driver):
    chat_link = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//a[normalize-space()='Chat']"))
    )
    chat_link.click()
    WebDriverWait(driver, 20).until(lambda d: len(d.window_handles) > 1)
    driver.switch_to.window(driver.window_handles[-1])


def _open_random_active_agent_chat(driver):
    agents_page = MyAgentsPage(driver)
    agents_page.click_my_agents()

    active_agent_names = agents_page.get_active_agent_names()
    assert active_agent_names, "No active agents found in the agent card list"

    target_agent_name = random.choice(active_agent_names)
    allure.attach(target_agent_name, name="Target agent", attachment_type=allure.attachment_type.TEXT)

    agents_page.search_agent(target_agent_name)
    agents_page.click_agent_card(target_agent_name)

    # The Chat tab is an <a target="_blank"> that opens chat.phronetic.ai
    # in a separate browser tab rather than navigating in-place.
    _open_chat_tab_in_new_window(driver)
    return target_agent_name


def _close_chat_tab(driver, main_window, request):
    # The generic pass/fail screenshot fixture in conftest.py captures the
    # main window after this test has already switched back to it (and the
    # chat tab has already been closed), so it can never show the chat tab
    # itself — that content is structurally gone by the time it runs. Save
    # the chat tab's real final state here, before it's closed, using
    # attach_and_save_screenshot so a meaningful screenshot actually lands
    # on disk in Screenshot/Passed instead of only the Allure report.
    try:
        attach_and_save_screenshot(
            driver, request, "Chat tab final state",
            png_bytes=driver.get_screenshot_as_png()
        )
    except Exception as e:
        print(f"Failed to capture chat tab screenshot: {e}")

    driver.close()
    driver.switch_to.window(main_window)

    # main_window sat idle for this entire test (everything happened in the
    # chat tab instead), often long enough that its session/auth state goes
    # stale and it drifts into a transient "Redirecting, please wait..."
    # interstitial. conftest.py's teardown screenshot captures whatever is
    # on screen at this exact moment, so without settling main_window back
    # onto a real page first, that screenshot ends up showing the loader
    # instead of anything meaningful.
    try:
        parsed = urlparse(driver.current_url)
        agents_url = f"{parsed.scheme}://{parsed.netloc}/agents"
        driver.get(agents_url)
        WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located(MyAgentsPage(driver).search_input)
        )
    except Exception as e:
        print(f"Failed to settle main window back onto /agents: {e}")


@allure.feature("Agent Interaction")
@allure.story("Chat")
@allure.title("Full chat flow: open agent, chat, start a new chat, upload a file and ask for a summary")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.chat
def test_chat_interact_new_chat_and_file_upload(driver, request):
    # One chained flow rather than independent test functions because each
    # stage depends on state the previous stage left behind: the new chat
    # needs an existing conversation to move on from, and the file-upload
    # question is asked inside that fresh new chat.
    #
    # Uses the function-scoped `driver` fixture (its own dedicated browser)
    # rather than the shared, session-scoped `logged_in_driver`: Step 7 logs
    # out, which tears down the SSO session for the whole browser, so running
    # it on the shared fixture would break every other test that reuses that
    # session afterward.

    with allure.step("Log in"):
        LandingPage(driver).open_page()
        LandingPage(driver).click_get_started()
        LoginPage(driver).login(config.username, config.password)
        attach_step_screenshot(driver, "After login")

    main_window = driver.current_window_handle
    pdf_path = os.path.abspath(os.path.join("Files", "sample_test.pdf"))
    file_name = os.path.basename(pdf_path)

    with allure.step("Step 1: Open My Agents and click on an agent card"):
        target_agent_name = _open_random_active_agent_chat(driver)
        print(f"Step 1 OK: opened Chat for agent '{target_agent_name}'.")
        attach_step_screenshot(driver, "Step 1: Chat opened")

    try:
        with allure.step("Step 2: Interact with the agent once in the chat area"):
            chat_page = ChatPage(driver)
            assert chat_page.is_message_input_visible(), "Step 2 failed: Chat message input did not appear"

            url_before = chat_page.get_current_url()
            chat_page.send_message(f"Automated test message for '{target_agent_name}'")

            # A successful send assigns the conversation its own id and the
            # URL picks it up — the explicit wait for the agent to respond,
            # instead of a hard sleep.
            WebDriverWait(driver, 30).until(lambda d: d.current_url != url_before)
            WebDriverWait(driver, 120).until(
                lambda d: len(d.find_elements(By.XPATH, "//*[contains(text(),'Thinking')]")) == 0
            )
            print("Step 2 OK: message sent and agent responded at", chat_page.get_current_url())
            attach_step_screenshot(driver, "Step 2: Agent responded")

        with allure.step("Step 3: Click New chat and verify a fresh chat opens"):
            first_conversation_url = chat_page.get_current_url()
            chat_page.start_new_chat()

            WebDriverWait(driver, 20).until(lambda d: d.current_url != first_conversation_url)
            assert chat_page.is_message_input_visible(), (
                "Step 3 failed: message input did not reappear after starting a new chat"
            )
            print("Step 3 OK: new chat opened at", chat_page.get_current_url())
            attach_step_screenshot(driver, "Step 3: New chat opened")

        with allure.step(f"Step 4: Upload '{file_name}' and ask for a summary"):
            chat_page.upload_file(pdf_path)
            assert chat_page.is_file_attached(file_name), (
                f"Step 4 failed: uploaded file '{file_name}' did not display in the chat"
            )

            chat_page.send_message("Please summarize this document.")
            # The agent reads the uploaded file (tool call) before replying,
            # which can take a while (occasionally over a minute even after
            # the file-read tool call itself completes), so this waits
            # generously for the "Thinking" indicator to clear rather than
            # sleeping a fixed amount or risking a flaky short timeout.
            WebDriverWait(driver, 120).until(
                lambda d: len(d.find_elements(By.XPATH, "//*[contains(text(),'Thinking')]")) == 0
            )
            print(f"Step 4 OK: '{file_name}' uploaded and agent responded with a summary.")
            # This is the moment the test is actually named for — saved to
            # disk (not just attached to Allure) so a meaningful screenshot
            # of it survives in Screenshot/Passed, since the test's own
            # final state (after Step 8 logs out) is always the login page.
            attach_and_save_screenshot(driver, request, "Step 4: File uploaded and summarized")

        with allure.step("Step 5: View agent details, check Usage History, and navigate back to Chat"):
            chat_url = chat_page.get_current_url()
            chat_page.click_view_agent_details()

            WebDriverWait(driver, 20).until(lambda d: d.current_url != chat_url)
            assert "/agent" in chat_page.get_current_url(), (
                f"Step 5 failed: 'View agent details' did not navigate to the agent details page "
                f"(URL was '{chat_page.get_current_url()}')"
            )
            details_url = chat_page.get_current_url()
            print("Step 5a OK: navigated to agent details page at", details_url)
            attach_step_screenshot(driver, "Step 5a: Agent details page")

            chat_page.click_usage_history_tab()
            assert chat_page.is_usage_history_visible(), (
                "Step 5 failed: Usage History table did not display after clicking the tab"
            )
            print("Step 5b OK: Usage History displayed.")
            attach_step_screenshot(driver, "Step 5b: Usage History displayed")

            chat_page.click_back_to_chat()
            WebDriverWait(driver, 20).until(lambda d: d.current_url != details_url)
            assert chat_page.is_message_input_visible(), (
                "Step 5 failed: message input did not reappear after clicking 'Back to Chat'"
            )
            print("Step 5c OK: returned to Chat at", chat_page.get_current_url())
            attach_step_screenshot(driver, "Step 5c: Back to Chat")

        with allure.step("Step 6: Report a bug from the profile menu"):
            chat_page.click_report_a_bug()
            chat_page.submit_bug_report(
                "[Automated test] This is a test bug report submitted by the automated Selenium flow test."
            )
            assert chat_page.is_bug_report_successful(), (
                "Step 6 failed: 'Bug reported!' confirmation did not appear after submitting"
            )
            chat_page.close_bug_report_modal()
            print("Step 6 OK: bug report submitted and confirmed.")
            attach_step_screenshot(driver, "Step 6: Bug report submitted")

        with allure.step("Step 7: Recharge wallet balance up to the billing redirect"):
            chat_page.click_recharge()
            WebDriverWait(driver, 20).until(lambda d: "/agent" in d.current_url)
            print("Step 7a OK: navigated to agent details page for recharge at", chat_page.get_current_url())
            attach_step_screenshot(driver, "Step 7a: Agent details page for recharge")

            chat_page.open_add_funds_modal()
            assert chat_page.is_add_funds_modal_open(), (
                "Step 7 failed: 'Add Funds to Wallet' modal did not open"
            )
            print("Step 7b OK: 'Add Funds to Wallet' modal opened.")
            attach_step_screenshot(driver, "Step 7b: Add Funds modal opened")

            chosen_amount = chat_page.pick_random_recharge_amount()
            print(f"Step 7c OK: selected amount '{chosen_amount}'.")
            attach_step_screenshot(driver, f"Step 7c: Amount selected ({chosen_amount})")

            # Continue hands off to the CCAvenue payment gateway in the same
            # tab. The flow only needs to reach billing, never submit a real
            # payment, so nothing on that page is touched.
            chat_page.click_continue_to_billing()
            WebDriverWait(driver, 20).until(lambda d: "ccavenue" in d.current_url.lower())
            billing_url = chat_page.get_current_url()
            assert "ccavenue" in billing_url.lower(), (
                f"Step 7 failed: 'Continue' did not redirect to the billing page (URL was '{billing_url}')"
            )
            print("Step 7d OK: redirected to billing page at", billing_url)
            attach_step_screenshot(driver, "Step 7d: Billing page")

            # Browser-history back rather than a "Close"/"Cancel" control:
            # CCAvenue's page offers no in-app way back, and this avoids
            # touching anything on the payment gateway itself.
            driver.back()
            WebDriverWait(driver, 20).until(lambda d: "ccavenue" not in d.current_url.lower())
            driver.back()
            assert chat_page.is_message_input_visible(), (
                "Step 7 failed: message input did not reappear after navigating back from billing"
            )
            print("Step 7e OK: returned to Chat at", chat_page.get_current_url())
            attach_step_screenshot(driver, "Step 7e: Returned to Chat")

        with allure.step("Step 8: Logout from the profile menu"):
            chat_page.logout()

            WebDriverWait(driver, 20).until(
                lambda d: "auth.phronetic.ai" in d.current_url and "login" in d.current_url
            )
            final_url = chat_page.get_current_url()
            assert "auth.phronetic.ai" in final_url and "login" in final_url, (
                f"Step 8 failed: expected redirect to the login page after logout, got '{final_url}'"
            )
            print("Step 8 OK: logged out and redirected to the login page:", final_url)
            attach_and_save_screenshot(driver, request, "Step 8: Logged out")
    finally:
        _close_chat_tab(driver, main_window, request)
