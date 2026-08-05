import allure
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


class SignUpPage:

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)

        self.name_input = (
            By.XPATH,
            "//input[@name='name']"
        )

        self.email_input = (
            By.XPATH,
            "//input[@name='email']"
        )

        self.password_input = (
            By.XPATH,
            "//input[@name='password']"
        )

        self.confirm_password_input = (
            By.XPATH,
            "//input[@name='confirmPassword']"
        )

        self.create_account_button = (
            By.XPATH,
            "//button[@type='submit' and normalize-space()='Create account']"
        )

        self.signin_link = (
            By.XPATH,
            "//a[normalize-space()='Sign in']"
        )

        # Per-field required/format errors, shown together on an empty
        # submit; each also appears independently once its own field's
        # rule is violated.
        self.name_error = (
            By.XPATH,
            "//*[contains(@class,'destructive') and contains(text(),'Name must be at least')]"
        )

        # A styled app-level error (same as name/password), not the
        # browser's native email-format validation — that only fires for a
        # non-empty, malformed value (see get_email_validation_message());
        # an empty email is instead caught by the app's own required check.
        self.email_error = (
            By.XPATH,
            "//*[contains(@class,'destructive') and normalize-space()='Please enter a valid email']"
        )

        self.password_requirements_error = (
            By.XPATH,
            "//*[contains(@class,'destructive') and normalize-space()='Password does not meet requirements']"
        )

        self.password_mismatch_error = (
            By.XPATH,
            "//*[contains(@class,'destructive') and normalize-space()='Passwords do not match']"
        )

        # A banner/toast-style error (centered, no per-field styling) rather
        # than a per-field one — distinct class list from the ones above.
        self.duplicate_email_error = (
            By.XPATH,
            "//*[contains(@class,'destructive') and contains(text(),'account with this email already exists')]"
        )

        # Both Password and Confirm Password fields have their own
        # "Show"/"Hide" visibility toggle; index 0 is Password, 1 is
        # Confirm Password.
        self.show_password_buttons = (
            By.XPATH,
            "//button[normalize-space()='Show']"
        )

        self.hide_password_buttons = (
            By.XPATH,
            "//button[normalize-space()='Hide']"
        )

    @allure.step("Fill sign-up form")
    def fill_form(self, name=None, email=None, password=None, confirm_password=None):
        if name is not None:
            field = self.wait.until(EC.visibility_of_element_located(self.name_input))
            field.clear()
            field.send_keys(name)

        if email is not None:
            field = self.wait.until(EC.visibility_of_element_located(self.email_input))
            field.clear()
            field.send_keys(email)

        if password is not None:
            field = self.wait.until(EC.visibility_of_element_located(self.password_input))
            field.clear()
            field.send_keys(password)

        if confirm_password is not None:
            field = self.wait.until(EC.visibility_of_element_located(self.confirm_password_input))
            field.clear()
            field.send_keys(confirm_password)

    @allure.step("Click 'Create account'")
    def click_create_account(self):
        self.wait.until(
            EC.element_to_be_clickable(self.create_account_button)
        ).click()

    @allure.step("Click 'Sign in'")
    def click_signin_link(self):
        self.wait.until(
            EC.element_to_be_clickable(self.signin_link)
        ).click()

    def is_on_signup_page(self):
        return "/signup" in self.driver.current_url

    def get_email_validation_message(self):
        """Returns the browser's native HTML5 constraint-validation message
        for the email field (e.g. a malformed address blocking submission
        before the app's own validation ever runs), or '' if the field
        currently satisfies native validation."""
        email_field = self.driver.find_element(*self.email_input)
        return self.driver.execute_script(
            "return arguments[0].validationMessage;", email_field
        )

    def get_name_error(self, timeout=8):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.name_error)
            ).text
        except TimeoutException:
            return None

    def get_email_error(self, timeout=8):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.email_error)
            ).text
        except TimeoutException:
            return None

    def get_password_requirements_error(self, timeout=8):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.password_requirements_error)
            ).text
        except TimeoutException:
            return None

    def get_password_mismatch_error(self, timeout=8):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.password_mismatch_error)
            ).text
        except TimeoutException:
            return None

    def get_duplicate_email_error(self, timeout=8):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(self.duplicate_email_error)
            ).text
        except TimeoutException:
            return None

    @allure.step("Toggle password visibility")
    def click_show_password(self, index=0):
        buttons = self.wait.until(
            EC.presence_of_all_elements_located(self.show_password_buttons)
        )
        buttons[index].click()

    def is_password_visible(self):
        field = self.driver.find_element(*self.password_input)
        return field.get_attribute("type") == "text"