import os
import random
from datetime import datetime

import allure
import pytest
from Webpages.tool_page import ToolPage
from Utility.allure_helpers import attach_step_screenshot


@allure.feature("Tool Management")
@allure.story("Tool Creation")
@allure.title("Create a new custom tool via prompt and verify it appears in the tools list")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.tool_creation
def test_create_tool(logged_in_driver):

    driver = logged_in_driver

    unique_id = datetime.now().strftime("%Y%m%d%H%M%S")
    tool_name = f"QA_Automation_Tool_{unique_id}"

    with allure.step("Navigate to Tools and start building a new tool"):
        tool_page = ToolPage(driver)
        tool_page.click_tools_nav()
        tool_page.click_generate()
        tool_page.choose_custom_tool()
        attach_step_screenshot(driver, "Create Tool form opened")

    with allure.step(f"Enter tool name '{tool_name}' and description, then generate code"):
        tool_page.enter_tool_name(tool_name)
        tool_page.enter_tool_description(
            "A simple tool that reverses the input text string, used for QA automation testing."
        )
        tool_page.click_generate_code()
        attach_step_screenshot(driver, "Code generation started")

        tool_page.wait_for_code_generation()
        attach_step_screenshot(driver, "Code generated")

    with allure.step("Click 'Create Tool' and wait for it to finish deploying"):
        tool_page.click_create_tool()
        tool_page.wait_for_tool_creation()

        assert tool_page.is_tool_created(), (
            f"Tool '{tool_name}' was not created — 'Update Tool' button never appeared"
        )
        print(f"Created tool '{tool_name}'.")
        attach_step_screenshot(driver, "Tool created")

    with allure.step(f"Verify '{tool_name}' appears in the Available Tools list"):
        tool_page.click_back()
        tool_page.search_tool(tool_name)

        assert tool_page.verify_tool_card(tool_name), (
            f"Tool '{tool_name}' was not found in the Available Tools list after creation"
        )
        print(f"Confirmed '{tool_name}' appears in the Available Tools list.")
        attach_step_screenshot(driver, "Tool verified in Available Tools list")


@allure.feature("Tool Management")
@allure.story("Tool Code Upload")
@allure.title("Uploading a non-.py file is rejected; uploading valid Python code updates the tool")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.tool_creation
def test_upload_code_to_tool(logged_in_driver):

    driver = logged_in_driver

    invalid_file_path = os.path.abspath(os.path.join("Files", "Python_Math_Operations.pdf"))
    valid_code_path = os.path.abspath(os.path.join("Files", "calculator.py"))

    with allure.step("Open a custom tool created by this automation suite"):
        tool_page = ToolPage(driver)
        tool_page.click_tools_nav()
        tool_page.click_custom_tools_tab()

        tool_names = tool_page.get_tool_names()
        # Restrict to tools this suite created itself (test_create_tool's
        # "QA_Automation_Tool_<timestamp>" naming). This test overwrites
        # whatever tool it opens, and the Custom Tools list can contain
        # other people's real tools — picking from the full list at random
        # would risk clobbering someone else's tool.
        own_tool_names = [n for n in tool_names if n.startswith("QA_Automation_Tool_")]
        assert own_tool_names, (
            "No automation-created tools ('QA_Automation_Tool_' prefix) found to safely "
            "test code upload against — run test_create_tool first"
        )

        target_tool = random.choice(own_tool_names)
        allure.attach(target_tool, name="Target tool", attachment_type=allure.attachment_type.TEXT)

        tool_page.open_tool_card(target_tool)
        attach_step_screenshot(driver, "Tool opened")

    with allure.step(f"Attempt to upload '{os.path.basename(invalid_file_path)}' — should be rejected"):
        tool_page.click_upload_code()
        tool_page.upload_code_file(invalid_file_path)

        assert tool_page.is_upload_code_error_present(), (
            "Expected an 'Only .py files are allowed.' error toast when uploading a non-.py file"
        )
        print(f"Confirmed non-.py upload was rejected for tool '{target_tool}'.")
        attach_step_screenshot(driver, "Non-.py upload rejected")

    with allure.step(f"Upload '{os.path.basename(valid_code_path)}' and update the tool"):
        tool_page.upload_code_file(valid_code_path)

        assert tool_page.is_upload_code_success_present(), (
            f"'{os.path.basename(valid_code_path)}' was not accepted by the Upload code input"
        )
        attach_step_screenshot(driver, "calculator.py uploaded")

        tool_page.click_update_tool()
        tool_page.wait_for_tool_update()

        assert tool_page.is_tool_updated(), (
            f"Tool '{target_tool}' was not updated after uploading calculator.py"
        )
        print(f"Updated tool '{target_tool}' with calculator.py.")
        attach_step_screenshot(driver, "Tool updated with calculator.py")
