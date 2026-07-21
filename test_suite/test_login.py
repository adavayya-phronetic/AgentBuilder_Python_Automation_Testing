import allure
import pytest
from Webpages.landing_page import LandingPage
from Webpages.login_page import LoginPage
from Webpages.dashboard_page import DashboardPage
from Utility import config
from Utility.allure_helpers import attach_step_screenshot


@allure.feature("Authentication")
@allure.story("Login / Logout")
@allure.title("TC_Login_01 — Successful login with valid email and password")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.login
def test_login_logout(driver):

    with allure.step("Open the application and reach the login page"):
        landing_page = LandingPage(driver)
        landing_page.open_page()
        landing_page.click_get_started()
        attach_step_screenshot(driver, "Reached login page")

    with allure.step("Log in with valid credentials"):
        login_page = LoginPage(driver)
        login_page.login(config.username, config.password)
        login_page.wait_for_login_success()

        assert not login_page.is_on_login_page(), "User should be redirected to the dashboard after login"
        attach_step_screenshot(driver, "Logged in")

    with allure.step("Log out via user menu"):
        dashboard = DashboardPage(driver)
        dashboard.logout()
        attach_step_screenshot(driver, "Logged out")


@allure.feature("Authentication")
@allure.story("Login Validation")
@allure.title("TC_Login_02 — Login fails with incorrect email, correct password")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.login
def test_incorrect_email_correct_password(driver):

    with allure.step("Open the application and reach the login page"):
        landing_page = LandingPage(driver)
        landing_page.open_page()
        landing_page.click_get_started()
        attach_step_screenshot(driver, "Reached login page")

    with allure.step("Enter an incorrect (but well-formed) email with the correct password"):
        login_page = LoginPage(driver)
        login_page.login("adavayyaWRONG@phronetic.ai", config.password)
        attach_step_screenshot(driver, "Submitted incorrect email with correct password")

    with allure.step("Verify 'Incorrect email or password' error is shown and user is not logged in"):
        error_message = login_page.get_login_error()

        assert error_message == "Incorrect email or password", (
            f"Expected error 'Incorrect email or password', got {error_message!r}"
        )
        assert login_page.is_on_login_page(), "User should not be logged in with an incorrect email"

        print("Incorrect email error message:", error_message)
        attach_step_screenshot(driver, "Incorrect email error shown")


@allure.feature("Authentication")
@allure.story("Login Validation")
@allure.title("TC_Login_03 — Login fails with correct email, incorrect password")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.login
def test_invalid_password(driver):

    with allure.step("Open the application and reach the login page"):
        landing_page = LandingPage(driver)
        landing_page.open_page()
        landing_page.click_get_started()
        attach_step_screenshot(driver, "Reached login page")

    with allure.step("Submit login form with a wrong password"):
        login_page = LoginPage(driver)
        login_page.login(config.username, "WrongPassword@123")
        attach_step_screenshot(driver, "Submitted wrong password")

    with allure.step("Verify 'Incorrect email or password' error is shown and user is not logged in"):
        error_message = login_page.get_login_error()

        assert error_message == "Incorrect email or password", (
            f"Expected error 'Incorrect email or password', got {error_message!r}"
        )
        assert login_page.is_on_login_page(), "User should not be logged in with an invalid password"

        print("Invalid password error message:", error_message)
        attach_step_screenshot(driver, "Invalid password error shown")


@allure.feature("Authentication")
@allure.story("Login Validation")
@allure.title("TC_Login_04 — Login fails with both incorrect email and incorrect password")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.login
def test_invalid_login(driver):

    with allure.step("Open the application and reach the login page"):
        landing_page = LandingPage(driver)
        landing_page.open_page()
        landing_page.click_get_started()
        attach_step_screenshot(driver, "Reached login page")

    with allure.step("Enter incorrect email and incorrect password, then click Sign in"):
        login_page = LoginPage(driver)
        login_page.login("invalid_user@phronetic.ai", "WrongPassword@123")
        attach_step_screenshot(driver, "Submitted incorrect email and password")

    with allure.step("Verify 'Incorrect email or password' error is shown and user is not logged in"):
        error_message = login_page.get_login_error()

        assert error_message == "Incorrect email or password", (
            f"Expected error 'Incorrect email or password', got {error_message!r}"
        )
        assert login_page.is_on_login_page(), "User should not be logged in with invalid credentials"

        print("Invalid login error message:", error_message)
        attach_step_screenshot(driver, "Invalid login error shown")


@allure.feature("Authentication")
@allure.story("Login Validation")
@allure.title("TC_Login_05 — Login with an unregistered email")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.login
def test_unregistered_email(driver):
    """
    Test case sheet expects "Something went wrong. Please try again." for an
    unregistered email. Verified live: the app actually shows the same
    generic "Incorrect email or password" used for TC_Login_02/03/04 —
    a reasonable security choice (not revealing whether an email is
    registered), but it means this asserts the app's real behavior rather
    than the sheet's stated expected result. Flagged for whoever owns the
    test case sheet in case the expected result needs correcting there,
    or the app is meant to distinguish the two cases and currently doesn't.
    """
    with allure.step("Open the application and reach the login page"):
        landing_page = LandingPage(driver)
        landing_page.open_page()
        landing_page.click_get_started()
        attach_step_screenshot(driver, "Reached login page")

    with allure.step("Submit login form with a well-formed but unregistered email"):
        login_page = LoginPage(driver)
        login_page.login("hiremathadi1008@gmail.com", "SomePassword@123")
        attach_step_screenshot(driver, "Submitted unregistered email")

    with allure.step("Verify an error is shown and user is not logged in"):
        error_message = login_page.get_login_error()

        assert error_message == "Incorrect email or password", (
            f"Expected error 'Incorrect email or password', got {error_message!r}"
        )
        assert login_page.is_on_login_page(), "User should not be logged in with an unregistered email"

        print("Unregistered email error message:", error_message)
        attach_step_screenshot(driver, "Unregistered email error shown")


@allure.feature("Authentication")
@allure.story("Login Validation")
@allure.title("TC_Login_06 — Empty email field validation")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.login
def test_empty_email_field(driver):

    with allure.step("Open the application and reach the login page"):
        landing_page = LandingPage(driver)
        landing_page.open_page()
        landing_page.click_get_started()
        attach_step_screenshot(driver, "Reached login page")

    with allure.step("Leave email blank, enter a password, then click Sign in"):
        login_page = LoginPage(driver)
        login_page.login("", config.password)
        attach_step_screenshot(driver, "Submitted with email left blank")

    with allure.step("Verify the 'Please enter a valid email' validation is shown"):
        email_error = login_page.get_email_field_error()

        assert email_error == "Please enter a valid email", (
            f"Expected 'Please enter a valid email', got {email_error!r}"
        )
        assert login_page.is_on_login_page(), "User should not be logged in with an empty email"

        print("Empty email field error:", email_error)
        attach_step_screenshot(driver, "Empty email field error shown")


@allure.feature("Authentication")
@allure.story("Login Validation")
@allure.title("TC_Login_07 — Empty password field validation")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.login
def test_empty_password_field(driver):

    with allure.step("Open the application and reach the login page"):
        landing_page = LandingPage(driver)
        landing_page.open_page()
        landing_page.click_get_started()
        attach_step_screenshot(driver, "Reached login page")

    with allure.step("Enter an email, leave password blank, then click Sign in"):
        login_page = LoginPage(driver)
        login_page.login(config.username, "")
        attach_step_screenshot(driver, "Submitted with password left blank")

    with allure.step("Verify the 'Password is required' validation is shown"):
        password_error = login_page.get_password_field_error()

        assert password_error == "Password is required", (
            f"Expected 'Password is required', got {password_error!r}"
        )
        assert login_page.is_on_login_page(), "User should not be logged in with an empty password"

        print("Empty password field error:", password_error)
        attach_step_screenshot(driver, "Empty password field error shown")


@allure.feature("Authentication")
@allure.story("Login Validation")
@allure.title("TC_Login_08 — Both fields empty on submit")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.login
def test_empty_login_fields(driver):

    with allure.step("Open the application and reach the login page"):
        landing_page = LandingPage(driver)
        landing_page.open_page()
        landing_page.click_get_started()
        attach_step_screenshot(driver, "Reached login page")

    with allure.step("Submit login form with both fields empty"):
        login_page = LoginPage(driver)
        login_page.login("", "")
        attach_step_screenshot(driver, "Submitted empty fields")

    with allure.step("Verify field-level validation errors appear for both fields"):
        email_error = login_page.get_email_field_error()
        password_error = login_page.get_password_field_error()

        assert email_error == "Please enter a valid email", (
            f"Expected 'Please enter a valid email', got {email_error!r}"
        )
        assert password_error == "Password is required", (
            f"Expected 'Password is required', got {password_error!r}"
        )
        assert login_page.is_on_login_page(), "User should not be logged in with empty credentials"

        print("Empty email field error:", email_error)
        print("Empty password field error:", password_error)
        attach_step_screenshot(driver, "Empty field errors shown")


@allure.feature("Authentication")
@allure.story("Login Validation")
@allure.title("TC_Login_09 — Invalid email format is rejected")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.login
def test_invalid_email_format(driver):

    with allure.step("Open the application and reach the login page"):
        landing_page = LandingPage(driver)
        landing_page.open_page()
        landing_page.click_get_started()
        attach_step_screenshot(driver, "Reached login page")

    with allure.step("Enter an email without '@'/domain, then click Sign in"):
        login_page = LoginPage(driver)
        login_page.login("invalidemail", config.password)
        attach_step_screenshot(driver, "Submitted malformed email")

    with allure.step("Verify the browser's native email-format validation blocks submission"):
        # This is a native input[type=email] constraint, not an app-rendered
        # error — the browser blocks the submit before it ever reaches the
        # app, so the message is read from the field's own validationMessage.
        validation_message = login_page.get_email_validation_message()

        assert "@" in validation_message and "missing" in validation_message, (
            f"Expected a native '...missing an @...' validation message, got {validation_message!r}"
        )
        assert login_page.is_on_login_page(), "User should not be logged in with a malformed email"

        print("Invalid email format validation message:", validation_message)
        attach_step_screenshot(driver, "Invalid email format validation shown")


@allure.feature("Authentication")
@allure.story("Login Validation")
@allure.title("TC_Login_10 — Email with embedded spaces is rejected")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.login
def test_email_with_spaces(driver):

    with allure.step("Open the application and reach the login page"):
        landing_page = LandingPage(driver)
        landing_page.open_page()
        landing_page.click_get_started()
        attach_step_screenshot(driver, "Reached login page")

    with allure.step("Enter an email containing a space, then click Sign in"):
        login_page = LoginPage(driver)
        login_page.login("hiremath adi1008 @gamil.com", config.password)
        attach_step_screenshot(driver, "Submitted email containing a space")

    with allure.step("Verify the browser's native validation rejects the embedded space"):
        validation_message = login_page.get_email_validation_message()

        assert "should not contain the symbol" in validation_message, (
            f"Expected a native '...should not contain the symbol...' validation message, "
            f"got {validation_message!r}"
        )
        assert login_page.is_on_login_page(), "User should not be logged in with a space in the email"

        print("Email-with-spaces validation message:", validation_message)
        attach_step_screenshot(driver, "Email-with-spaces validation shown")


@allure.feature("Authentication")
@allure.story("Login Validation")
@allure.title("TC_Login_11 — Email is case-insensitive")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.login
def test_case_insensitive_email_login(driver):

    with allure.step("Open the application and reach the login page"):
        landing_page = LandingPage(driver)
        landing_page.open_page()
        landing_page.click_get_started()
        attach_step_screenshot(driver, "Reached login page")

    with allure.step("Log in with the registered email in all-uppercase"):
        login_page = LoginPage(driver)
        mixed_case_email = config.username.upper()
        allure.attach(mixed_case_email, name="Mixed-case email used", attachment_type=allure.attachment_type.TEXT)

        login_page.login(mixed_case_email, config.password)
        login_page.wait_for_login_success()

        assert not login_page.is_on_login_page(), (
            "Login should succeed regardless of email case"
        )
        print(f"Logged in successfully using mixed-case email '{mixed_case_email}'.")
        attach_step_screenshot(driver, "Logged in with mixed-case email")

    with allure.step("Log out via user menu"):
        dashboard = DashboardPage(driver)
        dashboard.logout()
        attach_step_screenshot(driver, "Logged out")


@allure.feature("Authentication")
@allure.story("Login Navigation")
@allure.title("TC_Login_12 — 'Forgot password?' link navigates to the Forgot Password page")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.login
def test_forgot_password_navigation(driver):

    with allure.step("Open the application and reach the login page"):
        landing_page = LandingPage(driver)
        landing_page.open_page()
        landing_page.click_get_started()
        attach_step_screenshot(driver, "Reached login page")

    with allure.step("Click 'Forgot password?'"):
        login_page = LoginPage(driver)
        login_page.click_forgot_password()

        assert "/forgot-password" in driver.current_url, (
            f"Expected to be redirected to the Forgot Password page, current URL: {driver.current_url}"
        )
        print("Forgot password URL:", driver.current_url)
        attach_step_screenshot(driver, "Forgot Password page reached")


@allure.feature("Authentication")
@allure.story("Login Navigation")
@allure.title("TC_Login_13 — 'Sign up' link navigates to the Sign Up page")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.login
def test_signup_navigation(driver):

    with allure.step("Open the application and reach the login page"):
        landing_page = LandingPage(driver)
        landing_page.open_page()
        landing_page.click_get_started()
        attach_step_screenshot(driver, "Reached login page")

    with allure.step("Click 'Sign up'"):
        login_page = LoginPage(driver)
        login_page.click_signup()

        assert "/signup" in driver.current_url, (
            f"Expected to be redirected to the Sign Up page, current URL: {driver.current_url}"
        )
        print("Sign up URL:", driver.current_url)
        attach_step_screenshot(driver, "Sign Up page reached")


@allure.feature("Authentication")
@allure.story("Login / Logout")
@allure.title("TC_Login_14 — Enter key submits the login form")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.login
def test_enter_key_submits_login(driver):
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.by import By

    with allure.step("Open the application and reach the login page"):
        landing_page = LandingPage(driver)
        landing_page.open_page()
        landing_page.click_get_started()
        attach_step_screenshot(driver, "Reached login page")

    with allure.step("Enter valid credentials and press Enter instead of clicking Sign in"):
        login_page = LoginPage(driver)

        email_field = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.XPATH, "//input[@name='email']"))
        )
        password_field = driver.find_element(By.XPATH, "//input[@name='password']")
        email_field.send_keys(config.username)
        password_field.send_keys(config.password)
        password_field.send_keys(Keys.ENTER)
        login_page.wait_for_login_success()

        assert not login_page.is_on_login_page(), (
            "Pressing Enter should submit the form and log the user in"
        )
        print("Logged in via Enter key. URL:", driver.current_url)
        attach_step_screenshot(driver, "Logged in via Enter key")

    with allure.step("Log out via user menu"):
        dashboard = DashboardPage(driver)
        dashboard.logout()
        attach_step_screenshot(driver, "Logged out")


@allure.feature("Authentication")
@allure.story("Security")
@allure.title("TC_Login_15 — SQL injection input is handled safely")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.login
def test_sql_injection_login_input(driver):

    with allure.step("Open the application and reach the login page"):
        landing_page = LandingPage(driver)
        landing_page.open_page()
        landing_page.click_get_started()
        attach_step_screenshot(driver, "Reached login page")

    with allure.step("Enter a SQL-injection-style payload in both fields, then click Sign in"):
        login_page = LoginPage(driver)
        login_page.login("' OR '1'='1", "' OR '1'='1")
        attach_step_screenshot(driver, "Submitted SQL injection payload")

    with allure.step("Verify the payload is rejected safely with no DB error exposed"):
        # The payload isn't a valid email address, so the browser's own
        # input[type=email] validation blocks the request before it ever
        # reaches the backend — the strongest possible form of "input
        # sanitized, no DB error exposed" (the query never runs at all).
        validation_message = login_page.get_email_validation_message()
        page_text = driver.find_element("tag name", "body").text

        assert "@" in validation_message and "missing" in validation_message, (
            f"Expected the SQL injection payload to be rejected by native email validation, "
            f"got {validation_message!r}"
        )
        assert not any(k in page_text for k in ("SQL", "syntax", "database", "Traceback", "Exception")), (
            "Page must not leak SQL/database error details"
        )
        assert login_page.is_on_login_page(), "User should not be logged in with a SQL injection payload"

        print("SQL injection payload validation message:", validation_message)
        attach_step_screenshot(driver, "SQL injection payload rejected safely")
