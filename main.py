import logging
import os
import re
import sys

import yaml
from dotenv import load_dotenv

load_dotenv()

from email_builder import build_row_email
from mailer import build_smtp, send_email
from sheets import build_sheets_credentials, fetch_rows
from state_manager import diff, load_state, save_state

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)


def _resolve_env_vars(value):
    if isinstance(value, str):
        return re.sub(r"\$\{(\w+)\}", lambda m: os.environ.get(m.group(1), m.group(0)), value)
    if isinstance(value, dict):
        return {k: _resolve_env_vars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_env_vars(v) for v in value]
    return value


def load_config(path: str = "config.yaml") -> dict:
    with open(path) as f:
        return _resolve_env_vars(yaml.safe_load(f))


def main() -> None:
    config = load_config()

    google_cfg = config["google"]
    email_cfg = config["email"]
    state_cfg = config["state"]

    app_password = os.environ.get("GMAIL_APP_PASSWORD")
    if not app_password:
        log.error("GMAIL_APP_PASSWORD environment variable is not set")
        sys.exit(1)

    sheets_creds = build_sheets_credentials(google_cfg["credentials_file"])

    log.info("Fetching sheet data...")
    current_rows = fetch_rows(config, sheets_creds)
    log.info("Fetched %d data rows", len(current_rows))

    print("\n--- ALL ROWS ---")
    for i, row in enumerate(current_rows):
        print(f"  Row {i + 1}: {row}")
    print()

    old_rows = load_state(state_cfg["file"])
    changes = diff(old_rows, current_rows, google_cfg["monitored_columns"])

    if not changes:
        log.info("No changes detected. Saving current state as baseline.")
        save_state(state_cfg["file"], current_rows)
        return

    print("--- CHANGED ROWS ---")
    for change in changes:
        print(f"  Row {change['row_index'] + 1}:")
        for col, vals in change["changes"].items():
            print(f"    {col}: {vals['old']!r} -> {vals['new']!r}")
    print()

    log.info("%d row(s) changed", len(changes))
    sender = email_cfg["sender"]
    artist_col = google_cfg.get("artist_column", "ARTIST")
    artist_statuses = set(google_cfg.get("artist_statuses", []))
    artist_emails = email_cfg.get("artist_emails", {})
    status_recipients = email_cfg.get("status_recipients", {})

    with build_smtp(email_cfg["smtp_host"], email_cfg["smtp_port"], sender, app_password) as smtp:
        for change in changes:
            new_status = change["row"].get("STATUS", "").strip()
            shot = change["row"].get("SHOT", "").strip()
            shot_id = f"BL_VFX_{shot}"

            if new_status in ("_", ""):
                log.info("%s STATUS is unset, no notification sent", shot_id)
                continue

            subject, body = build_row_email(change, config)

            if new_status in artist_statuses:
                artist_name = change["row"].get(artist_col, "").strip()
                artist_email = artist_emails.get(artist_name)
                if artist_email:
                    send_email(smtp, sender, artist_email, subject, body)
                    log.info("%s STATUS -> %r: emailed %s", shot_id, new_status, artist_email)
                else:
                    log.warning("%s has no email mapped for artist %r — add to artist_emails in config", shot_id, artist_name)
            else:
                recipients = status_recipients.get(new_status, [])
                if recipients:
                    for recipient in recipients:
                        send_email(smtp, sender, recipient, subject, body)
                    log.info("%s STATUS -> %r: emailed %s", shot_id, new_status, ", ".join(recipients))
                else:
                    log.warning("%s has no recipients configured for STATUS %r", shot_id, new_status)

    save_state(state_cfg["file"], current_rows)
    log.info("State saved.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.error("Fatal error: %s", e)
        sys.exit(1)
