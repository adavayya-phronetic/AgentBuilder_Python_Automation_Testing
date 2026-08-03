import allure
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


class LoginPage:

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)

        self.username = (
            By.XPATH,
            "//input[@name='email']"
        )

        self.password = (
            By.XPATH,
            "//input[@name='password']"
        )

        self.login_button = (
            By.XPATH,
            "//button[@type='submit' and normalize-space()='Sign in']"
        )

        self.error_message = (
            By.XPATH,
            "//div[contains(@class,'text-destructive') and normalize-space()='Incorrect email or password']"
        )

        self.email_field_error = (
            By.XPATH,
            "//p[contains(@class,'text-destructive') and normalize-space()='Please enter a valid email']"
        )

        self.password_field_error = (
            By.XPATH,
            "//p[contains(@class,'text-destructive') and normalize-space()='Password is required']"
        )

        self.forgot_password_link = (
            By.XPATH,
            "//a[normalize-space()='Forgot password?']"
        )

        self.signup_link = (
            By.XPATH,
            "//a[normalize-space()='Sign up']"
        )

        # An unverified-but-otherwise-correct login redirects to a
        # dedicated /verify-email page (not an inline error on the login
        # form itself) with this message and a code-entry form.
        self.unverified_email_message = (
            By.XPATH,
            "//*[contains(text(),'Your email is not verified')]"
        )

        self.verify_email_button = (
            By.XPATH,
            "//button[normalize-space()='Verify email']"
        )

    @allure.step("Submit login form as {user}")
    def login(self, user, pwd):
        print("Current URL:", self.driver.current_url)

        self.wait.until(
            EC.visibility_of_element_located(self.username)
        ).send_keys(user)

        self.wait.until(
            EC.visibility_of_element_located(self.password)
        ).send_keys(pwd)

        self.wait.until(
            EC.element_to_be_clickable(self.login_button)
        ).click()

    def is_on_login_page(self):
        return "/auth" in self.driver.current_url

    def is_on_verify_email_page(self):
        return "/verify-email" in self.driver.current_url

    def wait_for_verify_email_redirect(self, timeout=20):
        """Waits for the post-login redirect to the /verify-email page to
        complete. Checking is_on_verify_email_page() right after login()
        returns is unreliable — the redirect takes a moment, so a raw
        check fires before the URL has actually changed."""
        WebDriverWait(self.driver, timeout).until(
            EC.url_contains("/verify-email")
        )

    def get_unverified_email_message(self, timeout=10):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.unverified_email_message)
            ).text
        except TimeoutException:
            return None

    def wait_for_login_success(self, timeout=20):
        """Waits for the post-login redirect to finish, using the
        dashboard's user-menu avatar (title contains '@') as the confirming
        signal. A raw URL check right after clicking Sign in is unreliable:
        the OAuth callback URL (.../auth/callback?code=...) also contains
        the substring '/auth', so is_on_login_page() can still read True
        mid-redirect."""
        WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located((By.XPATH, "//span[contains(@title,'@')]"))
        )

    def get_login_error(self, timeout=10):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.error_message)
            ).text
        except TimeoutException:
            return None

    def get_email_field_error(self, timeout=5):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.email_field_error)
            ).text
        except TimeoutException:
            return None

    def get_password_field_error(self, timeout=5):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.password_field_error)
            ).text
        except TimeoutException:
            return None

    def get_email_validation_message(self):
        """Returns the browser's native HTML5 constraint-validation message
        for the email field (e.g. malformed address blocking submission),
        or '' if the field currently satisfies native validation. The email
        input is type="email", so malformed values (missing '@', embedded
        spaces, etc.) never reach the app's own error handling at all —
        this reads the browser's own tooltip text instead."""
        email_field = self.driver.find_element(*self.username)
        return self.driver.execute_script("return arguments[0].validationMessage;", email_field)

    @allure.step("Click 'Forgot password?' link")
    def click_forgot_password(self):
        self.wait.until(
            EC.element_to_be_clickable(self.forgot_password_link)
        ).click()

    @allure.step("Click 'Sign up' link")
    def click_signup(self):
        self.wait.until(
            EC.element_to_be_clickable(self.signup_link)
        ).click()
