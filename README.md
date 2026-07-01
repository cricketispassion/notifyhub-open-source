# NotifyHub

Production-grade open-source notification automation platform.

## Features
- GitHub-managed configuration
- Playwright WhatsApp automation
- Plugin architecture
- Docker-ready
- Dashboard-ready
- Birthday plugin

## Run locally

1. Install dependencies:
   ```powershell
   python -m pip install -r requirements.txt
   ```
2. Run the birthday workflow from a CSV data file:
   ```powershell
   python services/worker/main.py --birthdays data/birthdays.csv
   ```
3. The repo is also configured to run daily via GitHub Actions at the configured send time.
4. Run the smoke test:
   ```powershell
   python -m pytest -q tests/test_worker.py
   ```

See docs/ARCHITECTURE.md for details.

CI note — browser automation

The scheduled workflow runs the Playwright browser automation in headless mode on the runner.

The workflow installs Playwright browsers automatically. If you need to debug Playwright runs locally, install Playwright and its browsers with:

```powershell
python -m pip install playwright
python -m playwright install
```

Persistent login across CI runs

The workflow caches the Playwright `profile` directory used by the Playwright driver so a WhatsApp Web login can persist between runs. The driver stores the profile at `drivers/whatsapp-playwright/profile`.

Notes:
- The cache is restored at the start of the job and saved automatically after the run.
- If the runner's environment changes (OS or cache key), you may need to re-login once to populate the cache.
