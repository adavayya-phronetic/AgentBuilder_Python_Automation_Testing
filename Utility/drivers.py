from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions


def _add_fake_media_stream_flags(options):
    # The Meet tests join a real video call; without these flags Chrome/Edge
    # would show a native camera/microphone permission prompt that Selenium
    # can't interact with, hanging the test. These auto-grant permission
    # using a fake virtual device instead. They're a no-op for every test
    # that never calls getUserMedia().
    options.add_argument("--use-fake-ui-for-media-stream")
    options.add_argument("--use-fake-device-for-media-stream")
    return options


def get_driver(browser):

    if browser.lower() == "chrome":
        driver = webdriver.Chrome(options=_add_fake_media_stream_flags(ChromeOptions()))

    elif browser.lower() == "edge":
        driver = webdriver.Edge(options=_add_fake_media_stream_flags(EdgeOptions()))

    else:
        raise Exception(f"Browser '{browser}' is not supported")

    driver.maximize_window()
    return driver