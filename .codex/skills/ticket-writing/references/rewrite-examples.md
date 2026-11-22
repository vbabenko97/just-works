# Rewrite examples — Bug, PBI and Spike

Before and after pairs for the ticket types in SKILL.md, with the same rules applied to each.

## Bug — before

Title: **Login bug**

Body:

> Login doesn't work. Please fix ASAP.

## Bug — after

Title: **Fix silent login failure on Chrome 125 / Windows 11**

Body:

**Summary**
Users on Chrome 125 / Windows 11 see no error when login credentials are rejected. The page reloads with the form cleared.

**Steps to reproduce:**
1. Open https://app.example.com/login in Chrome 125 on Windows 11.
2. Enter a valid email and an incorrect password.
3. Click Sign in.

**Actual result**
Page reloads. Form fields cleared. No error banner. Console: `POST /api/auth 401 — empty body`.

**Expected result**
An error banner appears above the form: "Invalid email or password." Form fields remain populated so the user can correct them.

**Environment**
Chrome 125.0.6422.76, Windows 11 23H2, Stage, web client v2.18.0. Reproduced on two accounts.

**Severity:**
Major. Failed logins give no feedback on the affected platform; the workaround is retrying credentials or the password-reset flow.

**Attachments**
`login-failure.mp4`, a screen recording of the failure.

## PBI — before

Title: Add that export thing we discussed

## PBI — after

Title: **Export transaction history to CSV from account settings**

Body:

**Problem**
Finance-facing users currently export transactions by copying rows out of the web table — about 15 minutes per account per month. Reported by the ops team in Slack (18 Apr) and in two customer support tickets.

**Proposed change**
Add a Download CSV button in Settings → Account → Transactions. The file covers the currently selected date range and includes date, amount, merchant, category, and status.

**Acceptance criteria:**
- A Download CSV button appears in Settings → Account → Transactions for signed-in users.
- Clicking the button downloads a CSV with header row: `date, amount, merchant, category, status`.
- The CSV covers the currently selected date range.
- An empty range produces a CSV with header row only.
- Download starts within 2 seconds for ranges up to 10,000 rows.

**Links:**
Parent: ACCT-410, Self-service reporting epic.

## PBI acceptance criteria in Given-When-Then

Given-When-Then for the same CSV export, where the flow branches on row count:

```
- Given a signed-in user on the Transactions page with a date range selected
  When the user clicks Download CSV and the range contains fewer than 10,000 rows
  Then a CSV downloads within 2 seconds with columns: date, amount, merchant, category, status.
- Given a signed-in user with a date range selected
  When the range contains more than 10,000 rows
  Then the user is prompted to narrow the range before download proceeds.
```

## Spike — before

Title: Look at PDF libraries

Body:

> We need PDFs. See what's out there.

## Spike — after

Title: **Pick a PDF generation library for invoice exports**

Body:

**Goal**
Recommend one PDF library to generate styled invoice PDFs from our existing HTML templates. Decision criteria: render fidelity vs the current Chrome reference, bundle size, license compatibility (commercial distribution), active maintenance.

**Method:**
1. Shortlist three libraries based on current industry usage: Puppeteer (headless Chrome), wkhtmltopdf, and Playwright print-to-PDF.
2. Render the current invoice template through each and diff against the Chrome reference.
3. Record output fidelity, render time on a representative sample of 100 invoices, bundle impact, and license terms.
4. Write a one-page recommendation with the tradeoffs.

**Expected output**
A comparison table, a recommendation with reasoning, and three sample PDFs (one per library) attached to this ticket.

**Open questions:**
1. Are we constrained to run this in-process, or can it run as a side-car service?
2. Is the commercial license for wkhtmltopdf a blocker given our distribution model?
