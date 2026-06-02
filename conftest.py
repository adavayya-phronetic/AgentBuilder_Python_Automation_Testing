#Pytest fixture for test setup/teardown

import pytest
from Utility.drivers import get_driver
from Utility import config

@pytest.fixture(params=["chrome", "edge"])
def driver(request):
    browser_name = request.param
    driver_instance = get_driver(browser_name)
    driver_instance.get(config.url)



    yield driver_instance
    driver_instance.quit()



#!request.param = current value from the params list
#Each time, one value from the list is passed