from selenium import webdriver


def get_driver(browser):

    if browser.lower() == "chrome":
        driver = webdriver.Chrome()

    elif browser.lower() == "edge":
        driver = webdriver.Edge()

    else:
        raise Exception(f"Browser '{browser}' is not supported")

    driver.maximize_window()
    return driver