import allure
import pytest
from Webpages.landing_page import LandingPage
from Webpages.login_page import LoginPage
from Webpages.dashboard_page import DashboardPage
from Utility import config
from Utility.allure_helpers import attach_step_screenshot


@allure.feature("Authentication")
@allure.story("Login / Logout")
@allure.title("Successful login and logout completes without error")
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
        attach_step_screenshot(driver, "Logged in")

    with allure.step("Log out via user menu"):
        dashboard = DashboardPage(driver)
        dashboard.logout()
        attach_step_screenshot(driver, "Logged out")


@allure.feature("Authentication")
@allure.story("Login Validation")
@allure.title("Invalid email and password combination shows error and stays on login page")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.login
def test_invalid_login(driver):

    with allure.step("Open the application and reach the login page"):
        landing_page = LandingPage(driver)
        landing_page.open_page()
        landing_page.click_get_started()
        attach_step_screenshot(driver, "Reached login page")

    with allure.step("Submit login form with an unregistered email"):
        login_page = LoginPage(driver)
        login_page.login("invalid_user@phronetic.ai", "WrongPassword@123")
        attach_step_screenshot(driver, "Submitted unregistered email")

    with allure.step("Verify error message is shown and user is not logged in"):
        error_message = login_page.get_login_error()

        assert error_message is not None, "Expected an error message for invalid login credentials"
        assert login_page.is_on_login_page(), "User should not be logged in with invalid credentials"

        print("Invalid login error message:", error_message)
        attach_step_screenshot(driver, "Invalid login error shown")


@allure.feature("Authentication")
@allure.story("Login Validation")
@allure.title("Correct email with wrong password shows error and stays on login page")
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

    with allure.step("Verify error message is shown and user is not logged in"):
        error_message = login_page.get_login_error()

        assert error_message is not None, "Expected an error message for invalid password"
        assert login_page.is_on_login_page(), "User should not be logged in with an invalid password"

        print("Invalid password error message:", error_message)
        attach_step_screenshot(driver, "Invalid password error shown")


@allure.feature("Authentication")
@allure.story("Login Validation")
@allure.title("Submitting empty email and password fields shows field-level validation errors")
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

        assert email_error is not None, "Expected validation error for empty email field"
        assert password_error is not None, "Expected validation error for empty password field"
        assert login_page.is_on_login_page(), "User should not be logged in with empty credentials"

        print("Empty email field error:", email_error)
        print("Empty password field error:", password_error)
        attach_step_screenshot(driver, "Empty field errors shown")
