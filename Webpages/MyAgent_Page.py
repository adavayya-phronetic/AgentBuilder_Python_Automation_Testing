from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class MyAgentsPage:

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 120)

        self.my_agents_menu = (
            By.XPATH,
            "//a[@href='/agents' and normalize-space()='My Agents']"
        )

        self.prompt_box = (
            By.TAG_NAME,
            "textarea"
        )

        self.create_agent_button = (
            By.XPATH,
            "//button[normalize-space()='Create Agent']"
        )

        self.status_filter_combobox = (
            By.XPATH,
            "//button[@role='combobox']"
        )

        self.status_option_all = (
            By.XPATH,
            "//div[@role='option' and normalize-space()='All']"
        )

    def click_my_agents(self):
        self.wait.until(
            EC.element_to_be_clickable(
                self.my_agents_menu
            )
        ).click()

    def enter_prompt(self, prompt):
        self.wait.until(
            EC.visibility_of_element_located(
                self.prompt_box
            )
        ).send_keys(prompt)

    def click_create_agent(self):
        self.wait.until(
            EC.element_to_be_clickable(
                self.create_agent_button
            )
        ).click()

    def set_status_filter_all(self):
        self.wait.until(
            EC.element_to_be_clickable(self.status_filter_combobox)
        ).click()

        self.wait.until(
            EC.element_to_be_clickable(self.status_option_all)
        ).click()

    def verify_agent_card(self, agent_name):
        card_locator = (
            By.XPATH,
            f"//h3[normalize-space()='{agent_name}']"
        )

        return self.wait.until(
            EC.presence_of_element_located(card_locator)
        ).is_displayed()
