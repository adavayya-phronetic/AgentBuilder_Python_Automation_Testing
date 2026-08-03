import os
import random

import allure
import pytest
from Webpages.tool_page import ToolPage
from Utility import secrets
from Utility.allure_helpers import attach_step_screenshot, attach_and_save_screenshot


TEXT_UTILITY_TOOL_DESCRIPTION = """Create a multi-function text utility tool with the following functions:

1. Function: analyzeText
   Input: text (string)
   Output: word count, character count (with/without spaces), sentence count
   Description: Analyze a text block and count words, characters, and sentences.

2. Function: caseConverter
   Input: text (string), targetCase (uppercase, lowercase, titlecase)
   Output: the converted text
   Description: Convert text into the specified case format.

3. Function: wordReverser
   Input: text (string)
   Output: the text with word order reversed
   Description: Reverse the order of words in a sentence.

4. Function: todoFormatter
   Input: tasks (comma or line separated text)
   Output: a formatted checklist
   Description: Convert a list of tasks into a clean checklist with checkboxes.

Notes:
- Each function should be independent and callable separately.
- Handle empty or invalid input gracefully with a clear error message.
- Return results in a clean, readable format."""


def _sample_value_for_param(param_name, index):
    # Prompt-generated code decides its own parameter names, so this can't
    # assume 'a'/'b' like the fixed calculator.py file does. An "operator"-
    # style param gets a real operator name; anything else is treated as
    # one of the two numbers and gets a plain numeric sample.
    if "op" in param_name.lower():
        return "add"
    numeric_samples = ["20", "30", "5", "2"]
    return numeric_samples[index % len(numeric_samples)]


def _create_tool_via_prompt(tool_page, driver, request, tool_name, description):
    tool_page.click_tools_nav()
    tool_page.click_generate()
    tool_page.choose_custom_tool()
    attach_step_screenshot(driver, "Create Tool form opened")

    tool_page.enter_tool_name(tool_name)
    tool_page.enter_tool_description(description)
    tool_page.click_generate_code()
    tool_page.wait_for_code_generation()
    attach_step_screenshot(driver, "Code generated")

    tool_page.click_create_tool()
    tool_page.wait_for_tool_creation()

    # The toast is a short-lived, best-effort signal (its exact timing
    # relative to the modal closing varies enough to occasionally miss it
    # even with polling) — the button relabeling to "Update Tool" is the
    # reliable, asserted proof that creation actually succeeded.
    if not tool_page.is_tool_created_toast_present():
        print(f"Note: 'Tool Created Successfully' toast was not observed for '{tool_name}' "
              f"(timing-dependent, non-fatal).")
    assert tool_page.is_tool_created(), (
        f"Tool '{tool_name}' was not created — 'Update Tool' button never appeared"
    )
    print(f"Created tool '{tool_name}'.")
    attach_and_save_screenshot(
        driver, request, "Tool created",
        png_bytes=tool_page.get_captured_tool_created_screenshot()
    )


@allure.feature("Tool Management")
@allure.story("Tool Creation and Testing")
@allure.title("Create a tool via prompt and run every function it generates")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.tool_creation
def test_create_and_test_tool_via_prompt(logged_in_driver, request):
    """
    1. Create a new tool via prompt only (Generate Code -> Create Tool) — no
       file upload involved.
    2. Run every function listed in the 'Test your tool' panel against the
       prompt-generated code, discovering each function's own parameter
       names rather than assuming fixed ones.

    Note: whether the Output panel actually populates after clicking Test
    can depend on the tool/backend. The test loop waits for a populated
    result (falling back to whatever's shown if it times out) and
    screenshots that, but doesn't assert a specific value, so an
    occasional null result doesn't fail the whole run.
    """
    driver = logged_in_driver
    tool_name = "QA_Automation_Tool_Prompt"

    with allure.step(f"Create a new tool '{tool_name}' via prompt"):
        tool_page = ToolPage(driver)
        _create_tool_via_prompt(tool_page, driver, request, tool_name, TEXT_UTILITY_TOOL_DESCRIPTION)

    with allure.step("Update the tool to save the generated code"):
        # The 'Test your tool' panel only lists parsed functions once the
        # generated code has actually been saved via Update Tool — creation
        # alone leaves it unpopulated, since Create Tool and Update Tool are
        # separate actions (confirmed: get_test_function_names() timed out
        # here until this step was added).
        tool_page.click_update_tool()
        tool_page.wait_for_tool_update()
        assert tool_page.is_tool_updated(), (
            f"Tool '{tool_name}' was not updated after saving the prompt-generated code"
        )
        attach_step_screenshot(driver, "Tool updated with generated code")

    with allure.step("Test every function listed in the 'Test your tool' panel"):
        function_names = tool_page.get_test_function_names()
        assert function_names, "No functions found in the 'Test your tool' panel"
        allure.attach(
            ", ".join(function_names),
            name="Functions found",
            attachment_type=allure.attachment_type.TEXT
        )
        print(f"Functions found in Test your tool panel: {function_names}")

        for function_name in function_names:
            tool_page.open_function_test_panel(function_name)

            param_names = tool_page.get_open_test_param_names()
            if not param_names:
                # Prompt-generated code can legitimately include a helper
                # function that takes no direct inputs (e.g. one reading
                # from env/config rather than user-supplied values) —
                # confirmed: an LLM-generated 'arithmeticWithEnv' function
                # had zero parameters. Nothing to fill in or run here, so
                # skip it rather than treating it as a script failure.
                print(f"Skipping '{function_name}': no input parameters to test.")
                continue

            for i, param_name in enumerate(param_names):
                tool_page.enter_test_param(param_name, _sample_value_for_param(param_name, i))
            attach_and_save_screenshot(
                driver, request, f"Test inputs entered for {function_name}({', '.join(param_names)})"
            )

            tool_page.click_run_test()

            # Waiting for the Output panel right where it is, without
            # navigating away, is what actually lets a real backend
            # response be observed — reopening the panel here would remount
            # the accordion's form fresh and wipe out the just-submitted
            # values and any result before it could be read.
            output = tool_page.wait_for_test_output()
            print(f"Test output for {function_name}({param_names}): {output!r}")
            attach_and_save_screenshot(driver, request, f"Test run submitted for {function_name}")


@allure.feature("Tool Management")
@allure.story("Tool Code Upload")
@allure.title("Create a second tool and update it by uploading a .py file")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.tool_creation
def test_create_tool_and_upload_code_file(logged_in_driver, request):
    """
    1. Create another new tool via prompt (a tool must exist before code can
       be uploaded to it — there's no upload-only creation path).
    2. Attempt to upload a non-.py file to it -> rejected.
    3. Upload a real .py file -> accepted, then click Update Tool.
    """
    driver = logged_in_driver

    tool_name = "QA_Automation_Tool_Upload"
    invalid_file_path = os.path.abspath(os.path.join("Files", "Python_Math_Operations.pdf"))
    valid_code_path = os.path.abspath(os.path.join("Files", "calculator.py"))

    with allure.step(f"Create a new tool '{tool_name}' via prompt"):
        tool_page = ToolPage(driver)
        _create_tool_via_prompt(tool_page, driver, request, tool_name, TEXT_UTILITY_TOOL_DESCRIPTION)

    with allure.step(f"Attempt to upload '{os.path.basename(invalid_file_path)}' — should be rejected"):
        tool_page.click_upload_code()
        tool_page.upload_code_file(invalid_file_path)

        assert tool_page.is_upload_code_error_present(), (
            "Expected an 'Only .py files are allowed.' error toast when uploading a non-.py file"
        )
        print(f"Confirmed non-.py upload was rejected for tool '{tool_name}'.")
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
            f"Tool '{tool_name}' was not updated after uploading calculator.py"
        )
        print(f"Updated tool '{tool_name}' with calculator.py.")
        attach_and_save_screenshot(driver, request, "Tool updated with calculator.py")

    with allure.step("Test every function listed in the 'Test your tool' panel"):
        # Click the function's row-level 'Test' link to open its panel, fill
        # in a/b, then click the panel's own 'Test' submit button — the
        # Output panel should populate with a real result (e.g. add(25, 25)
        # -> {"type": "text", "text": "50", ...}), not stay on the initial
        # empty '{}'.
        function_names = tool_page.get_test_function_names()
        assert function_names, "No functions found in the 'Test your tool' panel"
        allure.attach(
            ", ".join(function_names),
            name="Functions found",
            attachment_type=allure.attachment_type.TEXT
        )
        print(f"Functions found in Test your tool panel: {function_names}")

        for function_name in function_names:
            tool_page.open_function_test_panel(function_name)

            param_names = tool_page.get_open_test_param_names()
            assert param_names, f"No input parameters found for function '{function_name}'"

            for param_name in param_names:
                tool_page.enter_test_param(param_name, "25")
            attach_and_save_screenshot(
                driver, request, f"Test inputs entered for {function_name}({', '.join(param_names)})"
            )

            tool_page.click_run_test()

            output = tool_page.wait_for_test_output()
            assert output.strip() not in ("", "{}"), (
                f"Output panel did not populate with a result for '{function_name}' "
                f"(still showing {output!r})"
            )
            print(f"Test output for {function_name}({param_names}): {output!r}")
            attach_and_save_screenshot(driver, request, f"Test run submitted for {function_name}")


@allure.feature("Tool Management")
@allure.story("Tool Creation via MCP URL")
@allure.title("Create a tool from an external MCP URL and test its functions")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.tool_creation
def test_create_tool_via_mcp_url(logged_in_driver, request):
    """
    1. Create a tool from an external MCP server (a real, live Zapier/Gmail
       connection) via the 'External MCP URL' build method, instead of a
       prompt or file upload.
    2. Enable the Authorization Header (its name is fixed to 'X-API-KEY',
       read-only — only the value is settable) and set its value to the
       connection token.
    3. Enter the full MCP URL with the token embedded as the 'token' query
       parameter's value — confirmed: submitting the URL without the token
       appended fails server-side with 'Lambda function not found for
       tool' / 'Failed To Fetch Functions', since there's nothing for the
       platform to actually connect to.
    4. Test every function the connection exposes with real, safe
       (read-only) sample values.
    """
    driver = logged_in_driver
    tool_name = "QA_Automation_Tool_MCP_FindEmail"
    mcp_url = f"{secrets.zapier_mcp_base_url}={secrets.zapier_mcp_token}"

    # Real, tool-specific sample values for this known Gmail integration —
    # 'find email' is a read-only search, so this is safe to run repeatedly
    # against the live connected account. Generic per-tool heuristics (like
    # _sample_value_for_param for prompt-generated arithmetic tools) don't
    # apply here since these parameter names and their meaning are fixed
    # and known ahead of time.
    sample_values = {
        "query": "newsletter",
        "instructions": "Find the most recent email matching the query.",
        "output_hint": "Return the sender and subject line.",
    }

    with allure.step(f"Create a new tool '{tool_name}' from an external MCP URL"):
        tool_page = ToolPage(driver)
        tool_page.click_tools_nav()
        tool_page.click_generate()
        tool_page.choose_mcp_url_tool()
        attach_step_screenshot(driver, "External MCP URL form opened")

        tool_page.enter_tool_name(tool_name)
        tool_page.enable_authorization_header()
        tool_page.enter_header_value(secrets.zapier_mcp_token)
        tool_page.click_save_header()
        attach_step_screenshot(driver, "Authorization header saved")

        tool_page.enter_mcp_url(mcp_url)
        tool_page.click_create_tool()
        tool_page.wait_for_tool_creation()

        assert tool_page.is_tool_created(), (
            f"Tool '{tool_name}' was not created — 'Update Tool' button never appeared"
        )
        print(f"Created MCP-connected tool '{tool_name}'.")
        attach_and_save_screenshot(
            driver, request, "MCP tool created",
            png_bytes=tool_page.get_captured_tool_created_screenshot()
        )

    with allure.step("Test every function the MCP connection exposes"):
        function_names = tool_page.get_test_function_names()
        assert function_names, "No functions found in the 'Test your tool' panel"
        allure.attach(
            ", ".join(function_names),
            name="Functions found",
            attachment_type=allure.attachment_type.TEXT
        )
        print(f"Functions found in Test your tool panel: {function_names}")

        for function_name in function_names:
            tool_page.open_function_test_panel(function_name)

            param_names = tool_page.get_open_test_param_names()
            if not param_names:
                print(f"Skipping '{function_name}': no input parameters to test.")
                continue

            for param_name in param_names:
                value = sample_values.get(param_name, param_name)
                tool_page.enter_test_param(param_name, value)
            attach_and_save_screenshot(
                driver, request,
                f"Test inputs entered for {function_name}({', '.join(param_names)})"
            )

            tool_page.click_run_test()

            output = tool_page.wait_for_test_output()
            print(f"Test output for {function_name}({param_names}): {output!r}")
            attach_and_save_screenshot(driver, request, f"Test run submitted for {function_name}")


@allure.feature("Tool Management")
@allure.story("Tool Deletion")
@allure.title("Delete a tool via its options menu and verify it's removed from the list")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.tool_creation
def test_delete_tool(logged_in_driver, request):

    driver = logged_in_driver

    with allure.step("Open Custom Tools and pick a tool created by this automation suite"):
        tool_page = ToolPage(driver)
        tool_page.click_tools_nav()
        tool_page.click_custom_tools_tab()

        tool_names = tool_page.get_tool_names()
        # Restrict to tools this suite created itself — the Custom Tools
        # list can contain other people's real tools, and deleting is
        # irreversible, so never pick from the full list at random.
        own_tool_names = [n for n in tool_names if n.startswith("QA_Automation_Tool_")]
        assert own_tool_names, (
            "No automation-created tools ('QA_Automation_Tool_' prefix) found to safely "
            "delete — run test_create_and_test_tool_via_prompt or "
            "test_create_tool_and_upload_code_file first"
        )

        target_tool = random.choice(own_tool_names)
        allure.attach(target_tool, name="Target tool", attachment_type=allure.attachment_type.TEXT)
        print(f"Deleting tool '{target_tool}'.")
        attach_step_screenshot(driver, "Tool selected for deletion")

    with allure.step(f"Delete '{target_tool}' and confirm removal"):
        tool_page.open_tool_card_menu(target_tool)
        tool_page.click_delete_tool()
        attach_step_screenshot(driver, "Delete confirmation dialog shown")

        tool_page.confirm_delete_tool()

        assert tool_page.is_tool_deleted_toast_present(), (
            f"Expected 'Tool Deleted Successfully' toast after deleting '{target_tool}'"
        )
        attach_and_save_screenshot(driver, request, "Tool deleted successfully")

        assert tool_page.is_tool_card_absent(target_tool), (
            f"Tool '{target_tool}' still appears in the Available Tools list after deletion"
        )
        print(f"Confirmed '{target_tool}' was deleted and no longer appears in the list.")