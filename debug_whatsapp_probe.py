from pathlib import Path
from playwright.sync_api import sync_playwright

out_dir = Path(__file__).resolve().parent
screenshot_path = out_dir / 'whatsapp_probe.png'

print('starting playwright...')
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page(viewport={'width': 1440, 'height': 900})
    print('opening whatsapp web...')
    page.goto('https://web.whatsapp.com', wait_until='domcontentloaded', timeout=60000)
    page.wait_for_timeout(15000)
    print('title:', page.title())
    print('url:', page.url)
    print('body_text_snippet:', page.locator('body').inner_text()[:1000])
    page.screenshot(path=str(screenshot_path))
    print('screenshot:', screenshot_path)
    input('Press Enter to close browser...')
    browser.close()
