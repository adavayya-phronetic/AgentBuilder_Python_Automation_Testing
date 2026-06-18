#Pytest fixture for test setup/teardown

import os
import subprocess
import threading
import pytest
from Utility.drivers import get_driver
from Utility import config

@pytest.fixture(params=["chrome", "edge"])
def driver(request):
    browser_name = request.param
    driver_instance = get_driver(browser_name)
    driver_instance.get(config.url)

    yield driver_instance

    try:
        rep_call = getattr(request.node, "rep_call", None)
        if rep_call is not None:
            test_name = request.node.name
            if rep_call.failed:
                os.makedirs("Screenshot/Failed", exist_ok=True)
                driver_instance.save_screenshot(f"Screenshot/Failed/{test_name}.png")
                with open(f"Screenshot/Failed/{test_name}.html", "w", encoding="utf-8") as f:
                    f.write(driver_instance.page_source)
            elif rep_call.passed:
                os.makedirs("Screenshot/Passed", exist_ok=True)
                driver_instance.save_screenshot(f"Screenshot/Passed/{test_name}.png")
    except Exception as e:
        print(f"Failed to capture test artifacts: {e}")
    finally:
        _quit_driver(driver_instance)


def _quit_driver(driver_instance, timeout=30):
    # driver.quit() can hang, raise, or even return normally without
    # actually closing the browser (e.g. the QUIT command silently fails
    # while the page is still streaming/unresponsive, leaving chromedriver
    # killed but chrome.exe orphaned and visible). So capture the driver
    # process pid up front and always force-kill its process tree
    # afterwards as a guaranteed safety net, regardless of how quit() went.
    try:
        pid = driver_instance.service.process.pid
    except Exception:
        pid = None

    quit_error = []

    def _quit():
        try:
            driver_instance.quit()
        except Exception as e:
            quit_error.append(e)

    quit_thread = threading.Thread(target=_quit, daemon=True)
    quit_thread.start()
    quit_thread.join(timeout=timeout)

    if quit_thread.is_alive():
        print(f"driver.quit() timed out after {timeout}s; force killing driver process tree")
    elif quit_error:
        print(f"driver.quit() failed: {quit_error[0]}; force killing driver process tree")

    if pid is not None:
        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                capture_output=True
            )
        except Exception as e:
            print(f"Failed to force kill driver process tree: {e}")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


def pytest_sessionfinish(session, exitstatus):
    try:
        subprocess.run(
            ["allure", "generate", "Reports/Allure_reports", "-o", "Reports/reports_html", "--clean"],
            capture_output=True,
            shell=True,
        )
    except Exception as e:
        print(f"Failed to generate Allure HTML report: {e}")



#!request.param = current value from the params list
#Each time, one value from the list is passed