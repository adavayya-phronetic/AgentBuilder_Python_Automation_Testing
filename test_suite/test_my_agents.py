from datetime import datetime

import allure
import pytest
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from Webpages.my_agents_page import MyAgentsPage
from Webpages.agent_build_page import AgentBuildPage
from Utility.allure_helpers import attach_step_screenshot


# ----------------------------------------------------------------------
# TC_MyAgent_01 - TC_MyAgent_11 : creation prompt box
# ----------------------------------------------------------------------

@allure.feature("My Agents")
@allure.story("Page Load")
@allure.title("TC_MyAgent_01 — My Agents page loads with all core UI elements")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.my_agents
def test_my_agents_page_loads(logged_in_driver):
    driver = logged_in_driver

    with allure.step("Navigate to My Agents"):
        agents_page = MyAgentsPage(driver)
        agents_page.navigate_to_my_agents()
        attach_step_screenshot(driver, "My Agents page loaded")

    with allure.step("Verify heading, description box, Create Agent button, filter tabs, "
                      "status dropdown and search box are all present"):
        assert agents_page.is_page_loaded(), "My Agents page did not load all expected UI elements"


@allure.feature("My Agents")
@allure.story("Creation Prompt")
@allure.title("TC_MyAgent_02 — Agent description text box is visible")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.my_agents
def test_description_textbox_visible(logged_in_driver):
    driver = logged_in_driver
    agents_page = MyAgentsPage(driver)
    agents_page.navigate_to_my_agents()

    assert agents_page.is_description_box_visible(), "Description text box should be visible"
    attach_step_screenshot(driver, "Description box visible")


@allure.feature("My Agents")
@allure.story("Creation Prompt")
@allure.title("TC_MyAgent_03 — Create Agent button is visible")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.my_agents
def test_create_agent_button_visible(logged_in_driver):
    driver = logged_in_driver
    agents_page = MyAgentsPage(driver)
    agents_page.navigate_to_my_agents()

    assert agents_page.is_create_button_visible(), "Create Agent button should be visible"
    attach_step_screenshot(driver, "Create Agent button visible")


@allure.feature("My Agents")
@allure.story("Creation Prompt")
@allure.title("TC_MyAgent_04 — Create Agent button stays disabled with empty input")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.my_agents
def test_create_agent_button_disabled_when_empty(logged_in_driver):
    driver = logged_in_driver
    agents_page = MyAgentsPage(driver)
    agents_page.navigate_to_my_agents()

    agents_page.enter_description("")
    assert agents_page.is_create_button_disabled(), "Create Agent button should be disabled with empty input"
    attach_step_screenshot(driver, "Create Agent button disabled")


@allure.feature("My Agents")
@allure.story("Agent Creation")
@allure.title("TC_MyAgent_05 — Valid agent description submission starts agent creation")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.my_agents
def test_valid_description_submission_starts_creation(logged_in_driver):
    driver = logged_in_driver
    agents_page = MyAgentsPage(driver)
    agents_page.navigate_to_my_agents()

    with allure.step("Enter a valid description and click Create Agent"):
        unique_id = datetime.now().strftime("%Y%m%d%H%M%S")
        agents_page.enter_description(
            f"Create an assistant (ref #{unique_id}) that generates motivational quotes. "
            f"Do not ask follow-up questions, just do the basic configuration."
        )
        agents_page.click_create_agent()
        attach_step_screenshot(driver, "Creation prompt submitted")

    with allure.step("Verify agent creation starts successfully"):
        config_page = AgentBuildPage(driver)
        config_page.wait_for_agent_creation()

        assert config_page.verify_agent_configuration_page(), "Should navigate to the agent configure page"
        attach_step_screenshot(driver, "Agent configuration page loaded")


@allure.feature("My Agents")
@allure.story("Creation Prompt")
@allure.title("TC_MyAgent_06 — Character count updates dynamically while typing")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.my_agents
def test_character_count_updates_dynamically(logged_in_driver):
    driver = logged_in_driver
    agents_page = MyAgentsPage(driver)
    agents_page.navigate_to_my_agents()

    agents_page.enter_description("")
    empty_count = agents_page.get_character_count()

    text = "Hello World"
    agents_page.enter_description(text)
    typed_count = agents_page.get_character_count()

    print("Character count (empty):", empty_count)
    print("Character count after typing:", typed_count)
    attach_step_screenshot(driver, "Character count after typing")

    assert empty_count == 0, f"Expected 0 characters for an empty box, got {empty_count}"
    assert typed_count == len(text), f"Expected {len(text)} characters, got {typed_count}"


@allure.feature("My Agents")
@allure.story("Creation Prompt")
@allure.title("TC_MyAgent_07 — Maximum character limit blocks submission")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.my_agents
def test_maximum_character_limit(logged_in_driver):
    driver = logged_in_driver
    agents_page = MyAgentsPage(driver)
    agents_page.navigate_to_my_agents()

    # The box does not hard-block keystrokes past 5000 characters, but the
    # Create Agent button is disabled once the count exceeds the limit —
    # verified live: typing/pasting 5010 characters is accepted into the
    # field (counter shows "5010 / 5000 characters") while the button stays
    # disabled, which is the validation signal being checked here.
    agents_page.set_description_via_js("a" * 5010)
    count = agents_page.get_character_count()
    print("Character count after exceeding limit:", count)
    attach_step_screenshot(driver, "Over character limit")

    assert count > 5000, f"Expected over-limit character count, got {count}"
    assert agents_page.is_create_button_disabled(), "Create Agent button should be disabled over the character limit"


@allure.feature("My Agents")
@allure.story("Creation Prompt")
@allure.title("TC_MyAgent_08 — Shift+Enter adds a new line without submitting")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.my_agents
def test_multiline_input_via_shift_enter(logged_in_driver):
    driver = logged_in_driver
    agents_page = MyAgentsPage(driver)
    agents_page.navigate_to_my_agents()

    field = agents_page.enter_description("Line1")
    agents_page.send_shift_enter()
    field.send_keys("Line2")

    value = agents_page.get_description_value()
    print("Textarea value after Shift+Enter:", repr(value))
    attach_step_screenshot(driver, "Multiline input via Shift+Enter")

    assert value == "Line1\nLine2", f"Expected a new line added via Shift+Enter, got {value!r}"
    assert "/agents" in driver.current_url, "Shift+Enter should not submit the form"


@allure.feature("My Agents")
@allure.story("Agent Creation")
@allure.title("TC_MyAgent_09 — Enter key submits the description and creates the agent")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.my_agents
def test_create_agent_using_enter_key(logged_in_driver):
    driver = logged_in_driver
    agents_page = MyAgentsPage(driver)
    agents_page.navigate_to_my_agents()

    with allure.step("Enter a valid description and press Enter"):
        unique_id = datetime.now().strftime("%Y%m%d%H%M%S")
        agents_page.enter_description(
            f"Create an assistant (ref #{unique_id}) that generates fun trivia questions. "
            f"Do not ask follow-up questions, just do the basic configuration."
        )
        agents_page.press_enter()
        attach_step_screenshot(driver, "Submitted via Enter key")

    with allure.step("Verify agent creation starts successfully"):
        config_page = AgentBuildPage(driver)
        config_page.wait_for_agent_creation()

        assert config_page.verify_agent_configuration_page(), "Pressing Enter should submit and create the agent"
        attach_step_screenshot(driver, "Agent configuration page loaded")


@allure.feature("My Agents")
@allure.story("Creation Prompt")
@allure.title("TC_MyAgent_10 — Special characters are accepted safely in the description")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.my_agents
def test_special_characters_accepted_safely(logged_in_driver):
    driver = logged_in_driver
    agents_page = MyAgentsPage(driver)
    agents_page.navigate_to_my_agents()

    special_text = "<script>alert(1)</script> !@#$%^&*()_+-=[]{}|;:'\",.<>/?~`"
    agents_page.enter_description(special_text)
    value = agents_page.get_description_value()
    attach_step_screenshot(driver, "Special characters entered")

    assert value == special_text, "Special characters should be accepted into the description box as-is"
    # The text lands as a plain textarea value (not injected into the DOM as
    # markup), so no script executes and the app keeps running normally.
    assert "/agents" in driver.current_url


@allure.feature("My Agents")
@allure.story("Creation Prompt")
@allure.title("TC_MyAgent_11 — Whitespace-only description keeps Create Agent disabled")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.my_agents
def test_empty_spaces_submission_disabled(logged_in_driver):
    driver = logged_in_driver
    agents_page = MyAgentsPage(driver)
    agents_page.navigate_to_my_agents()

    agents_page.enter_description("     ")
    attach_step_screenshot(driver, "Whitespace-only description entered")

    assert agents_page.is_create_button_disabled(), "Create Agent button should stay disabled for whitespace-only input"


# ----------------------------------------------------------------------
# TC_Templates_01 - TC_Templates_04 : template carousel
# ----------------------------------------------------------------------

@allure.feature("My Agents")
@allure.story("Templates")
@allure.title("TC_Templates_01 — Selecting a template populates the description box")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.my_agents
def test_template_selection_populates_description(logged_in_driver):
    driver = logged_in_driver
    agents_page = MyAgentsPage(driver)
    agents_page.navigate_to_my_agents()

    agents_page.enter_description("")
    agents_page.click_template("Customer Support Bot")
    value = agents_page.get_description_value()
    print("Description after selecting 'Customer Support Bot':", value)
    attach_step_screenshot(driver, "Template selected")

    assert value.strip() != "", "Selecting a template should populate the description box"


@allure.feature("My Agents")
@allure.story("Templates")
@allure.title("TC_Templates_02 — Switching templates overwrites the previous selection")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.my_agents
def test_switching_templates_overwrites_previous(logged_in_driver):
    driver = logged_in_driver
    agents_page = MyAgentsPage(driver)
    agents_page.navigate_to_my_agents()

    agents_page.click_template("Customer Support Bot")
    first_value = agents_page.get_description_value()

    agents_page.click_template("Knowledge Assistant")
    second_value = agents_page.get_description_value()
    attach_step_screenshot(driver, "Switched templates")

    assert first_value != second_value, "Selecting a second template should change the description"
    assert first_value not in second_value, "The previous template's content should be fully overwritten"


@allure.feature("My Agents")
@allure.story("Templates")
@allure.title("TC_Templates_03 — Left arrow scrolls back to previous templates")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.my_agents
def test_template_left_arrow_navigation(logged_in_driver):
    driver = logged_in_driver
    agents_page = MyAgentsPage(driver)
    agents_page.navigate_to_my_agents()

    with allure.step("Scroll right first so there is somewhere to scroll back from"):
        agents_page.click_template_right_arrow()
        scrolled_position = agents_page.get_template_scroll_left()

    with allure.step("Click the left arrow"):
        agents_page.click_template_left_arrow()
        after_left = agents_page.get_template_scroll_left()
        attach_step_screenshot(driver, "After clicking left arrow")

    print("Template scrollLeft — after right, after left:", scrolled_position, after_left)
    assert after_left < scrolled_position, "Left arrow should scroll back toward the previous templates"


@allure.feature("My Agents")
@allure.story("Templates")
@allure.title("TC_Templates_04 — Right arrow scrolls forward to more templates")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.my_agents
def test_template_right_arrow_navigation(logged_in_driver):
    driver = logged_in_driver
    agents_page = MyAgentsPage(driver)
    agents_page.navigate_to_my_agents()

    before = agents_page.get_template_scroll_left()
    agents_page.click_template_right_arrow()
    after = agents_page.get_template_scroll_left()
    attach_step_screenshot(driver, "After clicking right arrow")

    print("Template scrollLeft — before, after right:", before, after)
    assert after > before, "Right arrow should scroll forward to reveal more templates"


# ----------------------------------------------------------------------
# TC_Filtertabs_05 - TC_Filtertabs_07 : All / Private / Published
# ----------------------------------------------------------------------

@allure.feature("My Agents")
@allure.story("Filter Tabs")
@allure.title("TC_Filtertabs_05 — 'All' tab displays all agents")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.my_agents
def test_all_tab_shows_all_agents(logged_in_driver):
    driver = logged_in_driver
    agents_page = MyAgentsPage(driver)
    agents_page.navigate_to_my_agents()

    agents_page.click_filter_tab("All")
    names = agents_page.get_card_names()
    agents_page.scroll_cards_into_view()
    attach_step_screenshot(driver, "All tab selected")

    assert agents_page.is_filter_tab_selected("All"), "'All' tab should be selected after clicking it"
    assert names, "Expected at least one agent card under the 'All' tab"


@allure.feature("My Agents")
@allure.story("Filter Tabs")
@allure.title("TC_Filtertabs_06 — 'Private' tab displays only private agents")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.my_agents
def test_private_tab_shows_only_private_agents(logged_in_driver):
    driver = logged_in_driver
    agents_page = MyAgentsPage(driver)
    agents_page.navigate_to_my_agents()

    agents_page.click_filter_tab("All")
    all_names = set(agents_page.get_card_names())

    agents_page.click_filter_tab("Private")
    private_names = set(agents_page.get_card_names())
    agents_page.scroll_cards_into_view()
    attach_step_screenshot(driver, "Private tab selected")

    assert agents_page.is_filter_tab_selected("Private"), "'Private' tab should be selected after clicking it"
    assert private_names <= all_names, "Private tab should only show a subset of all agents"


@allure.feature("My Agents")
@allure.story("Filter Tabs")
@allure.title("TC_Filtertabs_07 — 'Published' tab displays only published agents")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.my_agents
def test_published_tab_shows_only_published_agents(logged_in_driver):
    driver = logged_in_driver
    agents_page = MyAgentsPage(driver)
    agents_page.navigate_to_my_agents()

    agents_page.click_filter_tab("All")
    all_names = set(agents_page.get_card_names())

    agents_page.click_filter_tab("Published")
    # Short timeout: this account may have zero published agents, which is a
    # legitimate result, not a failure.
    published_names = set(agents_page.get_card_names(timeout=5))
    agents_page.scroll_cards_into_view()
    attach_step_screenshot(driver, "Published tab selected")

    print("Published agent names:", published_names)
    assert agents_page.is_filter_tab_selected("Published"), "'Published' tab should be selected after clicking it"
    assert published_names <= all_names, "Published tab should only show a subset of all agents"


# ----------------------------------------------------------------------
# TC_Status_08 : status dropdown
# ----------------------------------------------------------------------

@allure.feature("My Agents")
@allure.story("Status Filter")
@allure.title("TC_Status_08 — Status dropdown shows Active, Inactive and All options")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.my_agents
def test_status_dropdown_options(logged_in_driver):
    driver = logged_in_driver
    agents_page = MyAgentsPage(driver)
    agents_page.navigate_to_my_agents()

    options = agents_page.get_status_dropdown_options()
    print("Status dropdown options:", options)
    attach_step_screenshot(driver, "Status dropdown options")

    assert set(options) == {"All", "Active", "Inactive"}, f"Unexpected status options: {options}"


# ----------------------------------------------------------------------
# TC_SearchAgent_02 - TC_SearchAgent_05 : search
# ----------------------------------------------------------------------

@allure.feature("My Agents")
@allure.story("Search")
@allure.title("TC_SearchAgent_02 — Search matches full, partial and middle text")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.my_agents
def test_search_full_partial_middle_text(logged_in_driver):
    driver = logged_in_driver
    agents_page = MyAgentsPage(driver)
    agents_page.navigate_to_my_agents()

    agents_page.click_filter_tab("All")
    all_names = agents_page.get_card_names()
    assert all_names, "Need at least one existing agent to search for"
    target = all_names[0]
    allure.attach(target, name="Target agent", attachment_type=allure.attachment_type.TEXT)

    with allure.step(f"Search full name '{target}'"):
        agents_page.search_agent(target)
        assert target in agents_page.get_card_names()

    with allure.step("Search middle text"):
        middle_text = target[2:-2] if len(target) > 6 else target
        agents_page.search_agent(middle_text)
        assert target in agents_page.get_card_names(), f"Middle text {middle_text!r} should still match {target!r}"

    agents_page.scroll_cards_into_view()
    attach_step_screenshot(driver, "Search full/partial/middle text")


@allure.feature("My Agents")
@allure.story("Search")
@allure.title("TC_SearchAgent_03 — Search is case-insensitive")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.my_agents
def test_search_case_insensitive(logged_in_driver):
    driver = logged_in_driver
    agents_page = MyAgentsPage(driver)
    agents_page.navigate_to_my_agents()

    agents_page.click_filter_tab("All")
    all_names = agents_page.get_card_names()
    assert all_names, "Need at least one existing agent to search for"
    target = all_names[0]

    agents_page.search_agent(target.upper())
    upper_result = agents_page.get_card_names()

    agents_page.search_agent(target.lower())
    lower_result = agents_page.get_card_names()
    agents_page.scroll_cards_into_view()
    attach_step_screenshot(driver, "Case-insensitive search")

    assert target in upper_result, f"Uppercase search should match {target!r}"
    assert target in lower_result, f"Lowercase search should match {target!r}"


@allure.feature("My Agents")
@allure.story("Search")
@allure.title("TC_SearchAgent_04 — Search with no matching results shows a message")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.my_agents
def test_search_no_matching_results(logged_in_driver):
    driver = logged_in_driver
    agents_page = MyAgentsPage(driver)
    agents_page.navigate_to_my_agents()

    agents_page.search_agent("zzznonexistentagentxyz123")
    agents_page.scroll_no_results_message_into_view()
    attach_step_screenshot(driver, "Search with no matching results")

    assert agents_page.is_no_results_message_displayed(), "Expected a 'No agents found' message"
    assert agents_page.get_card_names(timeout=3) == [], "No agent cards should be shown for a non-matching search"


@allure.feature("My Agents")
@allure.story("Search")
@allure.title("TC_SearchAgent_05 — Leading/trailing spaces are trimmed automatically")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.my_agents
def test_search_leading_trailing_spaces_trim(logged_in_driver):
    """
    The test case sheet's expected result is annotated "— currently fails",
    implying trimming was a known bug. Live verification on this build showed
    the opposite: searching "   <name>   " (padded with spaces) still
    returns the matching card, so the app is already trimming/normalizing
    the query. This test asserts the actual, working behavior; worth
    flagging to whoever owns the sheet in case that note is stale.
    """
    driver = logged_in_driver
    agents_page = MyAgentsPage(driver)
    agents_page.navigate_to_my_agents()

    agents_page.click_filter_tab("All")
    all_names = agents_page.get_card_names()
    assert all_names, "Need at least one existing agent to search for"
    target = all_names[0]

    agents_page.search_agent(f"   {target}   ")
    result = agents_page.get_card_names()
    agents_page.scroll_cards_into_view()
    attach_step_screenshot(driver, "Search with leading/trailing spaces")

    assert target in result, f"Padded search should still match {target!r} (auto-trimmed), got {result}"
    agents_page.scroll_cards_into_view()


# ----------------------------------------------------------------------
# TC_AgentCards_01, 03, 04, 05, 07, 08, 09, 10 : agent card grid
# ----------------------------------------------------------------------

@allure.feature("My Agents")
@allure.story("Agent Cards")
@allure.title("TC_AgentCards_01 — Agent cards are visible")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.my_agents
def test_agent_cards_visible(logged_in_driver):
    driver = logged_in_driver
    agents_page = MyAgentsPage(driver)
    agents_page.navigate_to_my_agents()

    agents_page.click_filter_tab("All")
    names = agents_page.get_card_names()
    agents_page.scroll_cards_into_view()
    attach_step_screenshot(driver, "Agent cards visible")

    assert names, "Expected at least one agent card to be visible"


@allure.feature("My Agents")
@allure.story("Agent Cards")
@allure.title("TC_AgentCards_03 — Clicking an agent card navigates to its details")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.my_agents
def test_click_agent_card_navigates_to_details(logged_in_driver):
    driver = logged_in_driver
    agents_page = MyAgentsPage(driver)
    agents_page.navigate_to_my_agents()

    agents_page.click_filter_tab("All")
    names = agents_page.get_card_names()
    assert names, "Need at least one existing agent to click"
    target = names[0]

    agents_page.click_card(target)
    WebDriverWait(driver, 20).until(EC.url_contains("/build-agent/configure"))
    # The URL updates via client-side routing before the agent's actual data
    # (sidebar name/status, chat history, graph) has finished fetching, so a
    # screenshot taken right after the URL check can catch a loading-skeleton
    # placeholder instead of the real page — wait for the sidebar name to
    # render as the real content-loaded signal.
    AgentBuildPage(driver).get_agent_name()
    attach_step_screenshot(driver, "Agent details page opened")

    assert "/build-agent/configure" in driver.current_url


@allure.feature("My Agents")
@allure.story("Agent Cards")
@allure.title("TC_AgentCards_04 — Edit/Share buttons are hidden by default")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.my_agents
def test_edit_share_hidden_by_default(logged_in_driver):
    driver = logged_in_driver
    agents_page = MyAgentsPage(driver)
    agents_page.navigate_to_my_agents()

    agents_page.click_filter_tab("All")
    names = agents_page.get_card_names()
    assert names, "Need at least one existing agent"
    target = names[0]

    agents_page.move_mouse_away_from_cards()
    opacity = agents_page.get_edit_share_opacity(target)
    attach_step_screenshot(driver, "Edit/Share hidden by default")

    assert opacity == 0, f"Edit/Share buttons should be hidden (opacity 0) by default, got opacity {opacity}"


@allure.feature("My Agents")
@allure.story("Agent Cards")
@allure.title("TC_AgentCards_05 — Edit/Share buttons appear on hover")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.my_agents
def test_edit_share_appear_on_hover(logged_in_driver):
    driver = logged_in_driver
    agents_page = MyAgentsPage(driver)
    agents_page.navigate_to_my_agents()

    agents_page.click_filter_tab("All")
    names = agents_page.get_card_names()
    assert names, "Need at least one existing agent"
    target = names[0]

    agents_page.hover_over_card(target)
    opacity = agents_page.get_edit_share_opacity(target)
    attach_step_screenshot(driver, "Edit/Share visible on hover")

    assert opacity == 1, f"Edit/Share buttons should be fully visible (opacity 1) on hover, got opacity {opacity}"


@allure.feature("My Agents")
@allure.story("Agent Cards")
@allure.title("TC_AgentCards_07 — Edit/Share buttons disappear after the mouse leaves the card")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.my_agents
def test_edit_share_disappear_after_mouse_leaves(logged_in_driver):
    driver = logged_in_driver
    agents_page = MyAgentsPage(driver)
    agents_page.navigate_to_my_agents()

    agents_page.click_filter_tab("All")
    names = agents_page.get_card_names()
    assert names, "Need at least one existing agent"
    target = names[0]

    agents_page.hover_over_card(target)
    hover_opacity = agents_page.get_edit_share_opacity(target)

    agents_page.move_mouse_away_from_cards()
    after_opacity = agents_page.get_edit_share_opacity(target)
    attach_step_screenshot(driver, "Edit/Share after mouse leaves")

    assert hover_opacity == 1, f"Expected opacity 1 while hovering, got {hover_opacity}"
    assert after_opacity == 0, f"Expected opacity 0 after the mouse leaves, got {after_opacity}"


@allure.feature("My Agents")
@allure.story("Agent Cards")
@allure.title("TC_AgentCards_08 — Edit button is clickable after hover and navigates to the Edit page")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.my_agents
def test_edit_button_navigates_to_edit_page(logged_in_driver):
    driver = logged_in_driver
    agents_page = MyAgentsPage(driver)
    agents_page.navigate_to_my_agents()

    agents_page.click_filter_tab("All")
    names = agents_page.get_card_names()
    assert names, "Need at least one existing agent"
    target = names[0]

    agents_page.hover_over_card(target)
    agents_page.click_card_edit(target)
    WebDriverWait(driver, 20).until(EC.url_contains("/build-agent/configure"))
    # Same race as the card-click navigation test above: the URL changes
    # before the agent's real data has loaded, so wait for the sidebar name
    # to render before treating the page as ready to screenshot.
    AgentBuildPage(driver).get_agent_name()
    attach_step_screenshot(driver, "Edit page opened")

    assert "/build-agent/configure" in driver.current_url


@allure.feature("My Agents")
@allure.story("Agent Cards")
@allure.title("TC_AgentCards_09 — Share button is clickable after hover and opens the share popup")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.my_agents
def test_share_button_opens_popup(logged_in_driver):
    driver = logged_in_driver
    agents_page = MyAgentsPage(driver)
    agents_page.navigate_to_my_agents()

    agents_page.click_filter_tab("All")
    names = agents_page.get_card_names()
    assert names, "Need at least one existing agent"
    target = names[0]

    agents_page.hover_over_card(target)
    agents_page.click_card_share(target)
    dialog_text = agents_page.get_share_dialog_text()
    attach_step_screenshot(driver, "Share popup opened")

    assert dialog_text.strip() != "", "Share popup should open with content"


@allure.feature("My Agents")
@allure.story("Agent Cards")
@allure.title("TC_AgentCards_10 — Share popup displays the correct agent name and description")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.my_agents
def test_share_popup_shows_correct_agent_details(logged_in_driver):
    driver = logged_in_driver
    agents_page = MyAgentsPage(driver)
    agents_page.navigate_to_my_agents()

    agents_page.click_filter_tab("All")
    names = agents_page.get_card_names()
    assert names, "Need at least one existing agent"
    target = names[0]

    agents_page.hover_over_card(target)
    agents_page.click_card_share(target)
    dialog_text = agents_page.get_share_dialog_text()
    attach_step_screenshot(driver, "Share popup agent details")

    print("Share popup text:", dialog_text)
    assert target in dialog_text, f"Expected agent name {target!r} in the share popup, got: {dialog_text!r}"
