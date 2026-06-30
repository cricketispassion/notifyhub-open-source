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
