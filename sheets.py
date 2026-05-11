from google.oauth2 import service_account
from googleapiclient.discovery import build

_SHEETS_SCOPE = "https://www.googleapis.com/auth/spreadsheets.readonly"


def build_sheets_credentials(credentials_file: str):
    return service_account.Credentials.from_service_account_file(
        credentials_file, scopes=[_SHEETS_SCOPE]
    )


def fetch_rows(config: dict, creds) -> list[dict]:
    """Return data rows as dicts keyed by header name.

    Uses includeGridData so hyperlinks inserted into cells are captured.
    For any column that has a hyperlink, an additional '{column}__url' key
    is added to the row dict containing the hyperlink URL.
    """
    service = build("sheets", "v4", credentials=creds)
    sheet_cfg = config["google"]
    sheet_id = sheet_cfg["sheet_id"]
    sheet_name = sheet_cfg["sheet_name"]
    header_idx = sheet_cfg["header_row"] - 1  # convert to 0-based

    result = (
        service.spreadsheets()
        .get(spreadsheetId=sheet_id, ranges=[sheet_name], includeGridData=True)
        .execute()
    )

    sheet = next(
        s for s in result["sheets"]
        if s["properties"]["title"] == sheet_name
    )
    all_row_data = sheet["data"][0].get("rowData", [])

    if len(all_row_data) <= header_idx:
        return []

    # Extract headers from the header row
    header_cells = all_row_data[header_idx].get("values", [])
    headers = [c.get("formattedValue", "") for c in header_cells]

    rows = []
    for row_data in all_row_data[header_idx + 1:]:
        cells = row_data.get("values", [])
        row = {}
        for i, header in enumerate(headers):
            cell = cells[i] if i < len(cells) else {}
            row[header] = cell.get("formattedValue", "")
            hyperlink = cell.get("hyperlink", "")
            if hyperlink:
                row[f"{header}__url"] = hyperlink
        # Skip entirely empty rows
        if any(v for v in row.values()):
            rows.append(row)

    return rows
