# Changelog

## [Unreleased]

### Fixed
- 2025-11-19: Fixed PyPI version generation to produce clean version numbers (e.g., 0.1.3) instead of post/dev suffixes (e.g., 0.1.3.post1.dev0) when creating releases via GitHub UI by: (1) ensuring the CI workflow checks out the exact tag commit, and (2) resetting any uncommitted changes from linting before building to avoid setuptools_scm detecting a dirty repository.
- 2025-11-19: Fixed ImportError by removing non-existent flow imports (custom_movements_flow, test_sequence_flow, duty_cycle_monitoring_flow, scheduled_duty_cycle_check) from src/progressive_automations_python/__init__.py. These flows only exist in scripts/prefect_flows.py, not in the package module. (Fixes job 55773363544)
- 2025-11-19: tests: Add tests/conftest.py to mock RPi.GPIO in CI so pytest can run in non-Raspberry Pi environments. (Fixes job 55770449647)

## Version 0.1 (development)

- Feature A added
- FIX: nasty bug #1729 fixed
- add your changes here!

- Hardware: Changed GPIO pin assignments - UP: GPIO 18, DOWN: GPIO 17 — 2025-11-18
- Refactor: Centralized GPIO pin constants in `scripts/constants.py` for maintainability — 2025-11-14
- Docs: Added `docs/bill_of_materials.md` (Bill of Materials) — 2025-11-14
- Docs: Added official product links to `docs/bill_of_materials.md` — 2025-11-14
- Docs: Added prices to `docs/bill_of_materials.md` (prices as of 11/6/2025) — 2025-11-14
- Build: Moved publishing to GitHub Actions trusted publisher workflow and
	aligned tooling docs — 2025-11-14
- Fix: Added Raspberry Pi 5 GPIO compatibility using rpi-lgpio library — 2025-11-14
- Docs: Added `docs/raspberry-pi-setup.md` with Pi 5 setup instructions — 2025-11-14
- Fix: Updated requirements.txt to use rpi-lgpio instead of RPi.GPIO for Pi 5 compatibility — 2025-11-14
