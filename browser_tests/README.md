# Automated browser integration tests

The workflow `.github/workflows/kiwadoi-ci.yml` runs on pull requests and pushes to main.
It installs Python 3.12, Node.js 24, the locked OCR package and Chromium. It runs
the existing Python suite, checks JavaScript syntax and runs real browser tests
against an isolated local HTTP server on an automatically selected port.

## Local execution (PowerShell, from the repository root)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-browser.txt
npm ci
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe -m unittest discover -v
.\.venv\Scripts\python.exe -m unittest discover -s browser_tests -v
```

No separate server is necessary. On Linux, use the corresponding virtual
environment Python executable and install browser dependencies with
`python -m playwright install --with-deps chromium`.

Tests use only fictional ad copy and generated image fixtures. They cover
navigation, research API rendering, ad analysis, abstention, stale-result
invalidation, unknown permission holds, budget scenario arithmetic, real
local OCR and transcript correction, upload rejection, simulation and mobile
page overflow. Uncaught JavaScript errors fail the test. Screenshots and
logs are uploaded as CI artifacts even if a test fails.

The checks exercise the local application, not the hosted Vercel routing,
production OCR request limits or external links. They are not evidence of
model validity. Verify the specific GitHub commit and workflow conclusion
before merging or claiming tests passed.
