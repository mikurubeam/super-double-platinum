# super-double-platinum

Track your dance competition awards using SMS and Google Sheets.

## Overview

This project provides a local Python web app that:

- Receives SMS messages (webhook or polling) from a Google phone number and parses competition results.
- Stores parsed messages and accounts in a Google Sheet.
- Serves a local frontend showing the stored results.

The frontend is viewable from GitHub (the static HTML files are in `frontend/`), and the live app runs locally.

## Getting Started

### 1) Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Configure Google Sheets access

1. Create a Google Cloud service account with access to Google Sheets.
2. Download the service account JSON key file.
3. Run the setup helper:

```bash
python -m app setup
```

4. Set the spreadsheet ID in your environment (the long ID in the URL of the sheet):

```bash
export DANCE_SPREADSHEET_ID=1A... (your sheet id)
```

### 3) Initialize the spreadsheet

```bash
python -m app init
```

This creates the required worksheets (`Results` and `Accounts`).

### 4) Run locally

```bash
python -m app run
```

Then open http://127.0.0.1:5000 in your browser.

## Using SMS to add results

You can send an SMS to the configured phone number with a simple key/value payload. Example:

```
event: Solo; dancer: Alice; place: 1; score: 9.5
```

If your provider supports webhooks, configure it to POST to:

```
http://127.0.0.1:5000/webhook/sms
```

Payload format:

```json
{ "from": "+1234567890", "message": "event: Solo; dancer: Alice; place: 1" }
```

If webhooks are not available, you can use Google Voice polling (unofficial API):

```bash
python -m app poll-sms
```

## Accounts

Create a new application account (stored encrypted in the Google Sheet):

```bash
python -m app create-account
```

Passwords are hashed with bcrypt.

## Frontend

The frontend is in `frontend/index.html`. When the local app is running it fetches data from `/api/results`.

If you want a version that can be hosted on GitHub Pages (no backend required), use `frontend/github.html`. It fetches the `Results` sheet directly from the Google Sheets API using an API key.

You can view the frontend files directly on GitHub (they are static HTML/CSS/JS).
