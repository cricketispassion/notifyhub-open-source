from playwright.sync_api import sync_playwright

print('starting')
p = sync_playwright().start()
try:
    browser = p.chromium.launch(headless=False)
    print('launched')
    page = browser.new_page()
    page.goto('https://web.whatsapp.com', wait_until='domcontentloaded', timeout=60000)
    print('title:', page.title)
    print('url:', page.url)
    page.screenshot(path='whatsapp_probe.png')
    input('Press Enter to close browser...')
finally:
    p.stop()
