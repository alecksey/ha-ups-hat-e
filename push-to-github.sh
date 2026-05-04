#!/usr/bin/env bash
# One-shot init + commit + push to https://github.com/alecksey/ha-ups-hat-e.git
# Run from /c/Projects/personal/hacs-ups-hat-e in Git Bash / WSL.
# Requires git installed and authenticated to GitHub (HTTPS PAT or SSH key).
set -euo pipefail

# 1. Wipe any half-initialized .git from the previous session
if [ -d .git ]; then
  echo "Removing stale .git folder..."
  rm -rf .git
fi

# 2. Fresh repo on `main`
echo "Initializing git..."
git init --initial-branch=main
git config user.name  "Oleksii"
git config user.email "delphiworld@gmail.com"

# 3. Stage everything respecting .gitignore
git add -A

# 4. Initial commit
git commit -m "feat: initial release of Waveshare UPS HAT (E) integration

- Config Flow (UI) setup with options flow
- I2C driver (smbus2) + mock driver for development
- DataUpdateCoordinator polling registers 0x02 / 0x03 / 0x10 / 0x20 / 0x30 / 0x50
- 17 sensors (battery, USB-C, cells, status, charge stage, firmware)
- 6 binary sensors (AC, charging, PD, low battery, BQ4050/IP2368 fault)
- ups_hat_e.shutdown service (write 0x55 -> reg 0x01)
- English + Ukrainian translations
- HACS + Hassfest CI validation
- README documents container/I2C permission caveats"

# 5. Remote + push
git remote add origin https://github.com/alecksey/ha-ups-hat-e.git
echo "Pushing to origin/main..."
git push -u origin main

echo "Done."
