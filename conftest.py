import os
import subprocess
import threading
from datetime import datetime
from urllib.parse import urlparse
import allure
import pytest
from Webpages.landing_page import LandingPage
from Webpages.login_page import LoginPage
from Utility.drivers import get_driver
from Utility import config


@pytest.fixture(params=["chrome", "edge"])
def driver(request):
    """Function-scoped fresh browser — used by login/auth tests and test_create_agent."""
    browser_name = request.param
    driver_instance = get_driver(browser_name)
    driver_instance.get(config.url)
    yield driver_instance
    # Captured here, before _quit_driver, rather than left to the
    # _capture_screenshot autouse fixture: that fixture is function-scoped
    # like this one, and pytest tears this fixture down first, so by the
    # time _capture_screenshot ran the browser was already killed and every
    # screenshot silently failed with a connection-refused error.
    _capture_test_artifacts(driver_instance, request)
    _quit_driver(driver_instance)


@pytest.fixture(scope="session", params=["chrome", "edge"])
def _session_browser(request):
    """Session-scoped browser — one instance per browser type, shared across agent tests."""
    browser_name = request.param
    driver_instance = get_driver(browser_name)
    # Stashed on the instance so a later crash can be recovered with the
    # same browser — see _recover_dead_driver().
    driver_instance._test_browser_name = browser_name
    driver_instance.get(config.url)
    yield driver_instance
    _quit_driver(driver_instance)


@pytest.fixture(scope="session")
def logged_in_driver(_session_browser):
    """Logs in once per browser session; yields the driver positioned at the app dashboard."""
    LandingPage(_session_browser).open_page()
    LandingPage(_session_browser).click_get_started()
    login_page = LoginPage(_session_browser)
    login_page.login(config.username, config.password)
    # Without this wait, the driver can still be sitting on auth.phronetic.ai
    # (the OAuth callback redirect back to the app hasn't landed yet) when a
    # test's first action hard-navigates via urlparse(current_url) — that
    # then rebuilds the target URL on the AUTH host instead of the app host,
    # producing auth.phronetic.ai's own "Access Blocked: Missing required
    # parameters (client_id or redirect_uri)" page. Confirmed live: this is
    # exactly what was failing the first few dashboard tests in a run.
    login_page.wait_for_login_success()
    yield _session_browser


def _is_driver_alive(driver_instance):
    try:
        _ = driver_instance.current_url
        return True
    except Exception:
        # Deliberately broad: a dead session shows up as InvalidSessionIdException
        # when chromedriver itself is still running, but as a raw connection
        # error (e.g. urllib3.MaxRetryError) when the chromedriver process
        # itself is gone — neither is a case worth distinguishing here, since
        # either way this driver can't be used and needs recovering.
        return False


def _recover_dead_driver(driver_instance):
    """Recreates the browser and logs back in, then rewires driver_instance's
    connection internals (command_executor/session_id/caps) to point at the
    new session. Every reference already held to this same object — page
    objects, the cached session-scoped fixture itself — starts working
    through the new session transparently; nothing else has to change.

    Chrome/chromedriver crashes mid-suite have repeatedly taken down every
    remaining test in the file (and every other file after it, since
    logged_in_driver is session-scoped and shared across the whole pytest
    run) rather than just the one test that hit the crash. This can't
    prevent the crash, but it stops one crash from cascading into
    everything downstream of it.
    """
    browser_name = getattr(driver_instance, "_test_browser_name", "chrome")
    print(f"Detected a dead '{browser_name}' session; recreating it and logging back in...")

    new_driver = get_driver(browser_name)
    new_driver.get(config.url)
    LandingPage(new_driver).open_page()
    LandingPage(new_driver).click_get_started()
    new_login_page = LoginPage(new_driver)
    new_login_page.login(config.username, config.password)
    new_login_page.wait_for_login_success()

    driver_instance.command_executor = new_driver.command_executor
    driver_instance.session_id = new_driver.session_id
    driver_instance.caps = new_driver.caps
    print("Recovered: subsequent tests will use the freshly logged-in session.")


@pytest.fixture(autouse=True)
def _recover_shared_session_if_dead(request):
    """Runs before every test, before its own body. If the test uses the
    shared logged_in_driver and that session has already died (from a
    crash during an earlier test), recreates and re-logs-in transparently
    so this test — and everything after it — gets a working browser
    instead of inheriting a permanently dead one. The test whose crash
    actually caused the dead session already failed and stays failed;
    this only protects everything downstream of it.
    """
    if "logged_in_driver" not in request.fixturenames:
        return
    driver_instance = request.getfixturevalue("logged_in_driver")
    if not _is_driver_alive(driver_instance):
        _recover_dead_driver(driver_instance)


def _capture_test_artifacts(driver_instance, request):
    """Takes a pass/fail screenshot (+ page source/URL on failure) for the given driver."""
    rep_call = getattr(request.node, "rep_call", None)
    if rep_call is None or driver_instance is None:
        return

    # Stamped onto every filename so repeated runs of the same test
    # accumulate a new screenshot each time instead of overwriting the
    # previous one.
    timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    test_name = f"{request.node.name}_{timestamp}"
    try:
        screenshot = driver_instance.get_screenshot_as_png()
        page_source = driver_instance.page_source
        current_url = driver_instance.current_url

        if rep_call.failed:
            os.makedirs("Screenshot/Failed", exist_ok=True)
            with open(f"Screenshot/Failed/{test_name}.png", "wb") as f:
                f.write(screenshot)
            with open(f"Screenshot/Failed/{test_name}.html", "w", encoding="utf-8") as f:
                f.write(page_source)

            allure.attach(screenshot, name="Screenshot on failure", attachment_type=allure.attachment_type.PNG)
            allure.attach(page_source, name="Page source on failure", attachment_type=allure.attachment_type.HTML)
            allure.attach(current_url, name="URL on failure", attachment_type=allure.attachment_type.TEXT)

        elif rep_call.passed:
            os.makedirs("Screenshot/Passed", exist_ok=True)
            with open(f"Screenshot/Passed/{test_name}.png", "wb") as f:
                f.write(screenshot)

            allure.attach(screenshot, name="Screenshot on pass", attachment_type=allure.attachment_type.PNG)

    except Exception as e:
        print(f"Failed to capture test artifacts: {e}")


@pytest.fixture(autouse=True)
def _capture_screenshot_then_reset(request):
    """After each test on the shared, session-scoped logged_in_driver: takes a pass/fail
    screenshot of the state the test actually left behind, THEN hard-navigates to /agents so
    the next test starts from a clean browser state. These two used to be separate autouse
    fixtures (_capture_screenshot, _reset_to_agents_page); pytest doesn't guarantee same-scope
    autouse fixtures tear down in declaration order, and in practice the reset was running
    first, so every screenshot showed the generic /agents landing page instead of the test's
    real final state. Combining them into one fixture makes the ordering explicit instead of
    accidental. Tests using the function-scoped `driver` fixture are captured directly in that
    fixture's own teardown instead — see the comment there for why."""
    yield
    if "driver" in request.node.funcargs:
        return

    driver = request.node.funcargs.get("logged_in_driver")
    if driver is None:
        return

    _capture_test_artifacts(driver, request)

    try:
        parsed = urlparse(driver.current_url)
        agents_url = f"{parsed.scheme}://{parsed.netloc}/agents"
        driver.get(agents_url)
    except Exception:
        pass


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
                capture_output=True,
                timeout=15
            )
        except subprocess.TimeoutExpired:
            print(f"taskkill on driver process tree (pid {pid}) timed out after 15s; "
                  f"leaving it to the OS rather than blocking the test run")
        except Exception as e:
            print(f"Failed to force kill driver process tree: {e}")


_FILE_ORDER = [
    "test_signuppage",
    "test_login",
    "test_dashboardpage",
    "test_my_agents",
    "test_agent_buildpage",
    "test_analyticspage",
    "test_chatpage",
    "test_meetpage",
    "test_toolpage",
]


def pytest_collection_modifyitems(items):
    def file_rank(item):
        name = item.fspath.basename
        for i, prefix in enumerate(_FILE_ORDER):
            if prefix in name:
                return i
        return len(_FILE_ORDER)
    items.sort(key=file_rank)


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
