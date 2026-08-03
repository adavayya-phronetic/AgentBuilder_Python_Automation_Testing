import allure
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class DashboardPage:

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)

        self.logout_dropdown = (
            By.XPATH,
            "//span[contains(@title,'@')]"
        )

        self.logout_link = (
            By.XPATH,
            "//div[@role='menuitem' and contains(.,'Sign out')]"
        )

        # Sign out redirects off the dashboard entirely, to the public
        # marketing site (www.phronetic.ai) rather than a fixed in-app URL.
        # That page is a heavier animated/hydrating SPA, so document.readyState
        # turns "complete" well before it actually paints — waiting for a
        # concrete visible element is what actually confirms the render, and
        # avoids a screenshot landing mid-navigation and coming back blank.
        self.marketing_site_get_started = (
            By.XPATH,
            "//*[normalize-space()='Get Started']"
        )

        self.create_agent_button = (
            By.XPATH,
            "//button[contains(normalize-space(.),'Create Agent')]"
        )

    @allure.step("Click 'Create Agent'")
    def click_create_agent(self):
        self.wait.until(
            EC.element_to_be_clickable(self.create_agent_button)
        ).click()
        # Navigates straight to the My Agents prompt page (/agents).
        self.wait.until(EC.url_contains("/agents"))

    @allure.step("Log out via user menu")
    def logout(self):
        self.wait.until(
            EC.element_to_be_clickable(self.logout_dropdown)
        ).click()

        self.wait.until(
            EC.element_to_be_clickable(self.logout_link)
        ).click()

        WebDriverWait(self.driver, 30).until(
            EC.visibility_of_element_located(self.marketing_site_get_started)
        )
