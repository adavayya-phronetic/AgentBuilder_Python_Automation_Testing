url="https://www.phronetic.ai/developer-platform"
username="adavayya@phronetic.ai"
password="Phroneticai@123"
browser="chrome"

# Seconds paused before every single WebDriver command (click, find, get, ...).
# Selenium normally fires these as fast as the app can respond, which is too
# quick for a human watching the browser to follow along. Set to 0 to run at
# full speed again. Applied centrally in Utility.drivers.get_driver, so it
# slows down every page object uniformly without touching each one.
slow_mo_seconds = 0.15
