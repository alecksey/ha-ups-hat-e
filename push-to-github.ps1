# One-shot init + commit + push to https://github.com/alecksey/ha-ups-hat-e.git
# Run from C:\Projects\personal\hacs-ups-hat-e in PowerShell.
# Requires git installed and authenticated to GitHub (HTTPS PAT or SSH key).

$ErrorActionPreference = "Stop"

# 1. Wipe any half-initialized .git from the previous session
if (Test-Path ".git") {
    Write-Host "Removing stale .git folder..." -ForegroundColor Yellow
    # -Force handles read-only / hidden files inside .git
    Remove-Item -Recurse -Force ".git"
}

# 2. Fresh repo on `main`
Write-Host "Initializing git..." -ForegroundColor Cyan
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
Write-Host "Pushing to origin/main..." -ForegroundColor Cyan
git push -u origin main

Write-Host "Done." -ForegroundColor Green
