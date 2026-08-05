import allure
import pytest
from Webpages.landing_page import LandingPage
from Webpages.login_page import LoginPage
from Webpages.signup_page import SignUpPage
from Utility import config
from Utility.allure_helpers import attach_step_screenshot


def _open_signup_page(driver):
    LandingPage(driver).open_page()
    LandingPage(driver).click_get_started()
    LoginPage(driver).click_signup()


@allure.feature("Authentication")
@allure.story("Sign Up Validation")
@allure.title("TC_SignUp_01 — Empty form submission shows required-field errors")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.signup
def test_empty_signup_form(driver):

    with allure.step("Reach the Sign Up page"):
        _open_signup_page(driver)
        attach_step_screenshot(driver, "Reached Sign Up page")

    with allure.step("Submit the form with every field empty"):
        signup_page = SignUpPage(driver)
        signup_page.click_create_account()
        attach_step_screenshot(driver, "Submitted empty form")

    with allure.step("Verify Name, Email, and Password errors all appear"):
        name_error = signup_page.get_name_error()
        email_error = signup_page.get_email_error()
        password_error = signup_page.get_password_requirements_error()

        assert name_error == "Name must be at least 2 characters", (
            f"Expected name error 'Name must be at least 2 characters', got {name_error!r}"
        )
        assert email_error == "Please enter a valid email", (
            f"Expected email error 'Please enter a valid email', got {email_error!r}"
        )
        assert password_error == "Password does not meet requirements", (
            f"Expected password error 'Password does not meet requirements', got {password_error!r}"
        )

        assert signup_page.is_on_signup_page(), "User should remain on the Sign Up page after an invalid submit"
        print("Name error:", name_error, "| Email error:", email_error, "| Password error:", password_error)
        attach_step_screenshot(driver, "Required-field errors shown")


@allure.feature("Authentication")
@allure.story("Sign Up Validation")
@allure.title("TC_SignUp_02 — Mismatched passwords are rejected")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.signup
def test_signup_password_mismatch(driver):

    with allure.step("Reach the Sign Up page"):
        _open_signup_page(driver)
        attach_step_screenshot(driver, "Reached Sign Up page")

    with allure.step("Fill the form with two different passwords"):
        signup_page = SignUpPage(driver)
        signup_page.fill_form(
            name="QA Automation",
            email="qa.mismatch.test@phronetic.ai",
            password="Password123!",
            confirm_password="Different123!"
        )
        signup_page.click_create_account()
        attach_step_screenshot(driver, "Submitted mismatched passwords")

    with allure.step("Verify a 'Passwords do not match' error appears"):
        error = signup_page.get_password_mismatch_error()
        assert error == "Passwords do not match", (
            f"Expected 'Passwords do not match', got {error!r}"
        )
        assert signup_page.is_on_signup_page(), "User should remain on the Sign Up page after a password mismatch"
        print("Password mismatch error:", error)
        attach_step_screenshot(driver, "Password mismatch error shown")


@allure.feature("Authentication")
@allure.story("Sign Up Validation")
@allure.title("TC_SignUp_03 — Weak password is rejected")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.signup
def test_signup_weak_password(driver):

    with allure.step("Reach the Sign Up page"):
        _open_signup_page(driver)
        attach_step_screenshot(driver, "Reached Sign Up page")

    with allure.step("Fill the form with a password that doesn't meet requirements"):
        signup_page = SignUpPage(driver)
        signup_page.fill_form(
            name="QA Automation",
            email="qa.weakpw.test@phronetic.ai",
            password="abc",
            confirm_password="abc"
        )
        signup_page.click_create_account()
        attach_step_screenshot(driver, "Submitted weak password")

    with allure.step("Verify a 'Password does not meet requirements' error appears"):
        error = signup_page.get_password_requirements_error()
        assert error == "Password does not meet requirements", (
            f"Expected 'Password does not meet requirements', got {error!r}"
        )
        assert signup_page.is_on_signup_page(), "User should remain on the Sign Up page with a weak password"
        print("Weak password error:", error)
        attach_step_screenshot(driver, "Weak password error shown")


@allure.feature("Authentication")
@allure.story("Sign Up Validation")
@allure.title("TC_SignUp_04 — Invalid email format is rejected")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.signup
def test_signup_invalid_email_format(driver):

    with allure.step("Reach the Sign Up page"):
        _open_signup_page(driver)
        attach_step_screenshot(driver, "Reached Sign Up page")

    with allure.step("Fill the form with a malformed email address"):
        signup_page = SignUpPage(driver)
        signup_page.fill_form(
            name="QA Automation",
            email="not-an-email",
            password="Password123!",
            confirm_password="Password123!"
        )
        signup_page.click_create_account()
        attach_step_screenshot(driver, "Submitted malformed email")

    with allure.step("Verify the browser blocks submission natively"):
        # A malformed value never reaches the app's own validation — the
        # email input is type="email", so the browser's own constraint
        # validation blocks it first (same pattern as the login page).
        validation_message = signup_page.get_email_validation_message()
        assert validation_message, "Expected the browser to flag the malformed email as invalid"
        assert signup_page.is_on_signup_page(), "User should remain on the Sign Up page with an invalid email"
        print("Native email validation message:", validation_message)
        attach_step_screenshot(driver, "Malformed email blocked")


@allure.feature("Authentication")
@allure.story("Sign Up Validation")
@allure.title("TC_SignUp_05 — Sign-up with an already-registered email is rejected")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.signup
def test_signup_duplicate_email(driver):

    with allure.step("Reach the Sign Up page"):
        _open_signup_page(driver)
        attach_step_screenshot(driver, "Reached Sign Up page")

    with allure.step("Submit the form using an email that's already registered"):
        signup_page = SignUpPage(driver)
        signup_page.fill_form(
            name="QA Automation",
            email=config.username,
            password="Password123!",
            confirm_password="Password123!"
        )
        signup_page.click_create_account()
        attach_step_screenshot(driver, "Submitted already-registered email")

    with allure.step("Verify an 'account already exists' error appears"):
        error = signup_page.get_duplicate_email_error()
        assert error and "already exists" in error.lower(), (
            f"Expected an 'account with this email already exists' error, got {error!r}"
        )
        assert signup_page.is_on_signup_page(), "User should remain on the Sign Up page for a duplicate email"
        print("Duplicate email error:", error)
        attach_step_screenshot(driver, "Duplicate email error shown")


@allure.feature("Authentication")
@allure.story("Sign Up Navigation")
@allure.title("TC_SignUp_06 — 'Sign in' link navigates back to the Login page")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.signup
def test_signup_signin_link_navigation(driver):

    with allure.step("Reach the Sign Up page"):
        _open_signup_page(driver)
        attach_step_screenshot(driver, "Reached Sign Up page")

    with allure.step("Click 'Sign in'"):
        signup_page = SignUpPage(driver)
        signup_page.click_signin_link()

        login_page = LoginPage(driver)
        assert login_page.is_on_login_page() and not signup_page.is_on_signup_page(), (
            f"Expected to be redirected to the Login page, current URL: {driver.current_url}"
        )
        print("Login page URL:", driver.current_url)
        attach_step_screenshot(driver, "Login page reached")


@allure.feature("Authentication")
@allure.story("Sign Up Usability")
@allure.title("TC_SignUp_07 — Password visibility can be toggled")
@allure.severity(allure.severity_level.MINOR)
@pytest.mark.signup
def test_signup_password_visibility_toggle(driver):

    with allure.step("Reach the Sign Up page and enter a password"):
        _open_signup_page(driver)
        signup_page = SignUpPage(driver)
        signup_page.fill_form(password="Password123!")
        assert not signup_page.is_password_visible(), "Password should be masked by default"
        attach_step_screenshot(driver, "Password entered, masked")

    with allure.step("Click 'Show' and verify the password becomes visible"):
        signup_page.click_show_password(index=0)
        assert signup_page.is_password_visible(), "Password should be revealed as plain text after clicking 'Show'"
        print("Password field type after Show:", "text")
        attach_step_screenshot(driver, "Password revealed")

