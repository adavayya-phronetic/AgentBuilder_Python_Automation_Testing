"""
End-to-end platform flow.

Chains through the full product journey in one deliberate page-to-page
order, mirroring how a real user actually moves through the app, rather
than each page's file independently logging in and navigating to itself
from scratch:

    Landing -> "Get Started" -> Login page -> (log in) -> Dashboard page
    -> "Create Agent" -> My Agents page -> (enter prompt, create agent)
    -> Build Agent page -> "Chat" -> Chat page -> "Meet" -> Meet page
    -> Tools page

Sign Up and Login run first as their own self-contained batches — most of
their test cases are deliberately testing failure/edge scenarios (wrong
password, duplicate email, etc.) that each need an isolated fresh browser,
so they already use the function-scoped `driver` fixture per test case
exactly as they do standalone; there's no single continuous session to
join yet at that point in the journey. From Dashboard onward, every test
below shares the ONE session-scoped `logged_in_driver` browser that
conftest.py's `logged_in_driver` fixture establishes via Landing ->
Get Started -> Login -> Dashboard already, so the flow really does stay
on one continuous browser session for the rest of the journey.

Every test function below is the SAME function object imported from its
original file (re-exported, not duplicated) — this file adds no new test
logic of its own. Running this file alone (`pytest test_suite/test_full_platform_flow.py`)
executes every existing test case from all 8 pages, in this exact order,
with full unmodified coverage. The original per-page files
(test_signuppage.py, test_login.py, ...) are untouched and remain fully
independently runnable on their own, exactly as before.
"""

# --- 1. Sign Up page ---
from test_signuppage import (
    test_empty_signup_form,
    test_signup_password_mismatch,
    test_signup_weak_password,
    test_signup_invalid_email_format,
    test_signup_duplicate_email,
    test_signup_signin_link_navigation,
    test_signup_password_visibility_toggle,
)

# --- 2. Login page ---
from test_login import (
    test_incorrect_email_correct_password,
    test_invalid_password,
    test_invalid_login,
    test_unregistered_email,
    test_empty_email_field,
    test_empty_password_field,
    test_empty_login_fields,
    test_invalid_email_format,
    test_email_with_spaces,
    test_forgot_password_navigation,
    test_signup_navigation,
    test_sql_injection_login_input,
    test_case_insensitive_email_login,
    test_enter_key_submits_login,
    test_login_logout,
    test_unverified_user_blocked_from_signin,
)

# --- 3. Dashboard page ---
# logged_in_driver's own fixture (conftest.py) is what actually performs
# Landing -> "Get Started" -> Login -> Dashboard for every test from here on.
from test_dashboardpage import (
    test_dashboard_loads_successfully,
    test_agents_card_navigates_to_my_agents,
    test_back_button_from_my_agents_returns_to_dashboard,
    test_tools_created_card_navigates_to_tools_page,
    test_back_button_from_tools_page_returns_to_dashboard,
    test_sessions_count_increases_after_new_interaction,
    test_unique_users_card_opens_popup,
    test_unique_users_popup_search,
    test_active_gateways_card_opens_popup,
    test_active_gateways_popup_shows_connected_details,
    test_session_performance_graph_updates_for_selected_date,
    test_session_performance_empty_state,
    test_credit_usage_graph_updates_for_selected_date,
    test_agents_activity_view_all_navigates_to_my_agents,
    test_top_agents_row_navigates_to_build_agent_page,
    test_activity_row_navigates_to_traces_page,
)

# --- 4. My Agents page ---
# (dashboard's "Create Agent" button, exercised by
# test_agents_activity_view_all_navigates_to_my_agents/friends above,
# is what lands the shared session here.)
from test_my_agents import (
    test_my_agents_page_loads,
    test_description_textbox_visible,
    test_create_agent_button_visible,
    test_create_agent_button_disabled_when_empty,
    test_valid_description_submission_starts_creation,
    test_character_count_updates_dynamically,
    test_maximum_character_limit,
    test_multiline_input_via_shift_enter,
    test_create_agent_using_enter_key,
    test_special_characters_accepted_safely,
    test_empty_spaces_submission_disabled,
    test_template_selection_populates_description,
    test_switching_templates_overwrites_previous,
    test_template_left_arrow_navigation,
    test_template_right_arrow_navigation,
    test_all_tab_shows_all_agents,
    test_private_tab_shows_only_private_agents,
    test_published_tab_shows_only_published_agents,
    test_status_dropdown_options,
    test_search_full_partial_middle_text,
    test_search_case_insensitive,
    test_search_no_matching_results,
    test_search_leading_trailing_spaces_trim,
    test_agent_cards_visible,
    test_click_agent_card_navigates_to_details,
    test_edit_share_hidden_by_default,
    test_edit_share_appear_on_hover,
    test_edit_share_disappear_after_mouse_leaves,
    test_edit_button_navigates_to_edit_page,
    test_share_button_opens_popup,
    test_share_popup_shows_correct_agent_details,
)

# --- 5. Build Agent page ---
# test_create_agent (the first test case in this stage) clicks the
# *Dashboard's own* "Create Agent" button — that's a correct assumption when
# test_agent_buildpage.py runs standalone (a fresh logged_in_driver session
# lands exactly on Dashboard, and this is the first test to touch it there),
# but by this point in the flow the My Agents stage above has already
# navigated the shared session to /agents, so that button is no longer on
# screen. Confirmed live: without this, test_create_agent times out waiting
# for it, then cascades into every other test in this stage failing via
# _require_created_agent_name(). A plain glue step back to /dashboard here —
# not a modification to any original test — closes that seam.
import allure as _allure
from urllib.parse import urlparse as _urlparse
from Webpages.dashboard_page import DashboardPage as _DashboardPage


@_allure.step("[Flow glue] Return to Dashboard before the Build Agent stage")
def test_flow_glue_return_to_dashboard(logged_in_driver):
    driver = logged_in_driver
    parsed = _urlparse(driver.current_url)
    driver.get(f"{parsed.scheme}://{parsed.netloc}/dashboard")
    assert _DashboardPage(driver).is_dashboard_loaded(), (
        "Flow glue step failed: Dashboard did not load when returning to it "
        "ahead of the Build Agent stage"
    )


from test_agent_buildpage import (
    test_create_agent,
    test_configure_agent_io_types,
    test_upload_knowledge_base_file,
    test_delete_knowledge_base_file,
    test_attach_tool_to_orchestrator,
    test_orchestrator_empty_instructions_validation,
    test_sub_agent_empty_instructions_validation,
    test_instructions_modal_close_without_changes_preserves_content,
    test_orchestrator_name_validation,
    test_agent_name_validation,
    test_model_field_required_on_redeploy,
    test_interact_window_opens,
    test_interact_message_input_field,
    test_interact_query_submission,
    test_interact_empty_message_validation,
    test_interact_spaces_only_validation,
    test_interact_new_chat_functionality,
    test_interact_file_attachment_upload,
)

# --- 6. Chat page ---
# Uses its own fresh `driver` (not the shared logged_in_driver) and logs in
# again internally — deliberately: this test logs out at the end (Step 7,
# see test_chatpage.py), which tears down the SSO session for the whole
# browser, so running it on the shared session would break every test after
# it in this flow. It reaches Chat via its own "Chat" button click.
from test_chatpage import (
    test_chat_interact_new_chat_and_file_upload,
)

# --- 7. Meet page ---
# (this test's own "Meet" button click, on the shared session, is what
# reaches the Meet page.)
from test_meetpage import (
    test_meet_interact_upload_and_validate_features,
)

# --- 8. Tools page ---
from test_toolpage import (
    test_create_and_test_tool_via_prompt,
    test_create_tool_and_upload_code_file,
    test_create_tool_via_mcp_url,
    test_delete_tool,
    test_all_tools_tab_displays_all_tools,
    test_platform_tools_tab_displays_platform_tools,
    test_custom_tools_tab_displays_custom_tools,
    test_search_tool_by_first_middle_last_letters,
)