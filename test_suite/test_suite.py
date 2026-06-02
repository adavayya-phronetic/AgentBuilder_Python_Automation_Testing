# Purpose: Test login & logout flow using POM

from Webpages.landing_page import LandingPage
from Webpages.login_page import LoginPage
from Webpages.dashboard_page import DashboardPage
from Utility import config


def test_login_logout(driver):

    # Landing Page
    landing_page = LandingPage(driver)

    landing_page.open_page()
    landing_page.click_get_started()

    # Login Page
    login_page = LoginPage(driver)

    login_page.login(
        config.username,
        config.password
    )

    # Dashboard Page
    dashboard = DashboardPage(driver)

    dashboard.logout()