def build_row_email(change: dict, config: dict) -> tuple[str, str]:
    row = change["row"]

    shot = row.get("SHOT", "").strip()
    subject = f"VFX Update - BL_VFX_{shot}"

    review_movie_url = row.get("REVIEW MOVIE__url", "").strip()
    review_movie_text = row.get("REVIEW MOVIE", "").strip()
    review_movie_link = review_movie_url or review_movie_text
    review_movie_html = (
        f'<a href="{review_movie_link}">{review_movie_text or review_movie_link}</a>'
        if review_movie_link else ""
    )

    fields = [
        ("STATUS",       row.get("STATUS", "")),
        ("SHOT",         shot),
        ("VERSION",      row.get("VERSION", "")),
        ("REVIEW MOVIE", review_movie_html),
        ("FRAME COUNT",  row.get("FRAME COUNT", "")),
        ("ARTIST",       row.get("ARTIST", "")),
        ("NOTES",        row.get("NOTES", "")),
    ]

    rows_html = "".join(
        f"<tr><td style='padding:4px 12px 4px 0;font-weight:bold;vertical-align:top'>{label}</td>"
        f"<td style='padding:4px 0'>{value}</td></tr>"
        for label, value in fields
    )
    body = f"<table style='font-family:sans-serif;font-size:14px'>{rows_html}</table>"
    return subject, body
