import os
import re
import time
from datetime import datetime

import allure


def attach_and_save_screenshot(driver, request, name, png_bytes=None):
    """Like attach_step_screenshot, but also saves the screenshot as its own
    file in Screenshot/Passed, alongside the generic final-state screenshot
    conftest.py captures at test teardown.

    The plain Screenshot/Passed folder only ever gets one screenshot per
    test — whatever is on screen when the test function returns — so a
    meaningful mid-test moment (e.g. a validation error that gets cleaned up
    by a later recovery step) is otherwise only visible in the Allure
    report. Use this instead of attach_step_screenshot for moments worth
    keeping in both places.

    Pass png_bytes when the moment being documented is short-lived (an
    auto-dismissing toast) and was already captured earlier at the exact
    right instant — a screenshot taken fresh, right here, could just as
    easily land after it has faded.
    """
    attach_step_screenshot(driver, name, png_bytes=png_bytes)
    try:
        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        # Step names often contain ':' ('Case 1: ...') which is invalid in
        # Windows filenames (and reserved for NTFS alternate data streams),
        # silently breaking the write — strip anything outside a safe set
        # rather than just spaces.
        safe_name = re.sub(r'[^A-Za-z0-9_-]+', '_', name).strip('_')
        file_name = f"{request.node.name}_{safe_name}_{timestamp}"
        os.makedirs("Screenshot/Passed", exist_ok=True)
        with open(f"Screenshot/Passed/{file_name}.png", "wb") as f:
            f.write(png_bytes if png_bytes is not None else driver.get_screenshot_as_png())
    except Exception as e:
        print(f"Failed to save extra screenshot '{name}': {e}")


def attach_step_screenshot(driver, name, png_bytes=None):
    """Attaches a screenshot of the current browser state to the Allure report.

    Called at the end of every test step so the report has a full,
    reviewable sequence of what the browser actually looked like at each
    stage — useful when the run itself happens too fast to watch live.

    Pass png_bytes to attach an already-captured screenshot instead of
    taking a fresh one now (see attach_and_save_screenshot).
    """
    try:
        allure.attach(
            png_bytes if png_bytes is not None else driver.get_screenshot_as_png(),
            name=name,
            attachment_type=allure.attachment_type.PNG
        )
    except Exception as e:
        print(f"Failed to capture step screenshot '{name}': {e}")


def attach_scrolled_screenshot(driver, element, name):
    """Attaches a screenshot of the element's actual on-screen state, scrolling
    it into view first only if it needs it.

    Panels like the Knowledge Base list scroll internally, so an element that
    exists in the DOM can still sit outside the visible viewport (or clipped
    by its scrollable ancestor) at screenshot time. Checking the element's
    bounding rect against the viewport — rather than scrolling unconditionally
    — avoids extra scroll jitter on the (common) case where it's already
    fully visible, matching what a user would actually see on screen.
    """
    if element is not None:
        try:
            needs_scroll = driver.execute_script(
                """
                const rect = arguments[0].getBoundingClientRect();
                const vw = window.innerWidth || document.documentElement.clientWidth;
                const vh = window.innerHeight || document.documentElement.clientHeight;
                return rect.top < 0 || rect.left < 0 || rect.bottom > vh || rect.right > vw;
                """,
                element
            )
            if needs_scroll:
                driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", element
                )
                # Let the (often animated/smooth) scroll settle before capturing,
                # otherwise the screenshot can land mid-scroll.
                time.sleep(0.3)
        except Exception as e:
            print(f"Scroll-visibility check failed for '{name}': {e}")

    attach_step_screenshot(driver, name)
