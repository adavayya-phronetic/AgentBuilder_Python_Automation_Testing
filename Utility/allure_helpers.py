import allure


def attach_step_screenshot(driver, name):
    """Attaches a screenshot of the current browser state to the Allure report.

    Called at the end of every test step so the report has a full,
    reviewable sequence of what the browser actually looked like at each
    stage — useful when the run itself happens too fast to watch live.
    """
    try:
        allure.attach(
            driver.get_screenshot_as_png(),
            name=name,
            attachment_type=allure.attachment_type.PNG
        )
    except Exception as e:
        print(f"Failed to capture step screenshot '{name}': {e}")
