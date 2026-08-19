import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions

from Utility import config


def _apply_slow_motion(driver, delay_seconds):
    """Pauses for delay_seconds before every low-level WebDriver command.
    Every Selenium call (find_element, click, get, ...) funnels through
    driver.execute(), so patching it here is a single choke point that
    slows the whole suite down uniformly instead of adding a sleep to every
    page object's every action. WebDriverWait's own timeout is wall-clock
    based (time.monotonic()), so this just means fewer, slower polls within
    the same budget — it doesn't shrink an existing wait's timeout window.
    """
    if not delay_seconds:
        return driver

    original_execute = driver.execute

    def _slow_execute(driver_command, params=None):
        time.sleep(delay_seconds)
        return original_execute(driver_command, params)

    driver.execute = _slow_execute
    return driver


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
    driver = _apply_slow_motion(driver, getattr(config, "slow_mo_seconds", 0))
    return driver