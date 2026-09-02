# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this does

Cron job script that monitors a Google Sheet for changes to specific columns (e.g. STATUS, APPROVED) and sends notification emails: one per changed row to the row owner, and a consolidated summary to a fixed admin list. State between runs is stored in `state.json`.

## Setup

```bash
pip install -r requirements.txt
```

Place your service account key at `credentials.json` (excluded from git). Fill in `config.yaml` with your sheet ID, header row number, column names, and email addresses.

## Running

```bash
python main.py
```

First run establishes a baseline in `state.json` — no emails sent. Subsequent runs diff against the saved state and email on changes.

Cron example:
```
*/15 * * * * /usr/bin/python3 /path/to/main.py >> /var/log/project-id.log 2>&1
```

## Architecture

- `main.py` — orchestrates the full run: fetch → diff → email → save state
- `sheets.py` — Google Sheets API: builds credentials (service account + DWD), fetches rows as dicts keyed by header name, handles header row offset
- `state_manager.py` — load/save `state.json`; `diff()` compares old vs new by row position for monitored columns
- `email_builder.py` — formats per-row and summary email subjects/bodies
- `mailer.py` — SMTP send via Gmail using `smtplib`; opens one connection per run and reuses it for all outbound emails

## Google API requirements

The service account is used **only for reading the sheet** (`spreadsheets.readonly` scope). Email is sent via Gmail SMTP — no Gmail API or domain-wide delegation required.

**Gmail SMTP setup:** enable 2-step verification on the sender Gmail account, then generate an App Password (Google Account → Security → App Passwords). Store it in the `GMAIL_APP_PASSWORD` environment variable — never in `config.yaml`.

## Configuration

All settings live in `config.yaml` — no hardcoded values in code:
- `google.header_row` — 1-indexed row number of the header row
- `google.monitored_columns` — list of column names to watch for changes
- `google.email_column` — column holding the per-row recipient address
- `email.fixed_recipients` — always receive the summary email

## Row keying

Rows are diffed by position (index below the header). If rows can be reordered between runs, add a stable unique-ID column and update `state_manager.diff()` to key on it instead.
