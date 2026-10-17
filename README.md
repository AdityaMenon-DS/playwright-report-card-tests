# Report Card App — Playwright Tests

Python end-to-end tests for a report-card application, prepared for the October 2026 Testing and Automation of Web Apps using Playwright workshop.

The app collects student details, academic information and subject scores, then generates a PDF report. This project checks that valid inputs work, invalid inputs are rejected, grades are calculated correctly, and the downloaded report includes the subjects.

## Test coverage

There are 38 test cases per round, covering:

- Required personal and academic fields
- Email validation
- Adding and removing subjects
- Duplicate subject names, including case and whitespace variations
- Empty subjects and scores outside 0–100
- Grade thresholds and boundary values
- Report preview, average and overall grade
- PDF download and subject-row contents
- Resetting the form

## Setup

Requires Python 3.10 or newer.

```sh
python -m venv .venv
```

Activate the environment in PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Or on macOS/Linux:

```sh
source .venv/bin/activate
```

Install the dependencies and browser:

```sh
python -m pip install -r requirements.txt
python -m playwright install chromium
```

## Run the tests

The default target is the workshop's reference app:

```sh
python -m pytest -v
```

Watch the browser:

```sh
python -m pytest -v --headed
```

To target the intentionally faulty app, use PowerShell:

```powershell
$env:APP_URL='https://cs3002-26t3-workshop-test.onrender.com'
$env:ROUNDS='5'
python -m pytest -v --screenshot only-on-failure
```

On macOS/Linux:

```sh
APP_URL=https://cs3002-26t3-workshop-test.onrender.com ROUNDS=5 python -m pytest -v --screenshot only-on-failure
```

Each test uses a fresh browser context. The test app enables three random faults from a set of eight, so failures can vary between runs. Assertions always describe the correct behaviour; an assertion failure on the faulty app can indicate a reproduced defect. Connection errors and timeouts need separate investigation.

## Findings and validation

During the 11 October 2026 investigation, five categories of faulty behaviour were reproduced:

1. Missing validation for mandatory data.
2. Acceptance of malformed email addresses.
3. Acceptance of duplicate subjects.
4. Incorrect grades at boundary scores.
5. Missing subject rows in downloaded PDFs.

Related mandatory-field failures are grouped together. This is a conservative classification of observed behaviour, not a claim to have identified all eight official fault types.

All 38 tests passed against the reference app using Microsoft Edge on 11 October 2026. The code in this repository preserves that verified test logic. These are historical results; the hosted workshop apps may change or become unavailable.

## Files

- `test.py`: test cases and shared form helpers
- `requirements.txt`: Python dependencies
- `pytest.ini`: makes plain `pytest` discover `test.py`
- `.gitignore`: excludes environments, caches and generated test artifacts

Only fictional student data is used in the tests.

## Workshop context

The demo application and assessment were supplied for the workshop taught by Afnan Ahmad. This repository contains the testing code, not the application source.

- [Reference app](https://cs3002-26t3-workshop.onrender.com/)
- [Faulty app](https://cs3002-26t3-workshop-test.onrender.com/)
- [Playwright Python documentation](https://playwright.dev/python/)
