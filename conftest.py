#Pytest fixture for test setup/teardown

import os
import pytest
from Utility.drivers import get_driver
from Utility import config

@pytest.fixture(params=["chrome", "edge"])
def driver(request):
    browser_name = request.param
    driver_instance = get_driver(browser_name)
    driver_instance.get(config.url)

    yield driver_instance

    if request.node.rep_call.failed:
        os.makedirs("Reports/failures", exist_ok=True)
        test_name = request.node.name
        driver_instance.save_screenshot(f"Reports/failures/{test_name}.png")
        with open(f"Reports/failures/{test_name}.html", "w", encoding="utf-8") as f:
            f.write(driver_instance.page_source)

    driver_instance.quit()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)



#!request.param = current value from the params list
#Each time, one value from the list is passed