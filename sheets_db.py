import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st
from config import (SHEET_ID, LEADS_SHEET, EMAIL_QUEUE_SHEET, LEAD_COLUMNS,
                    EMAIL_QUEUE_COLUMNS, SETTINGS_SHEET, TEAM_MEMBERS_SHEET, DEFAULT_SETTINGS)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def get_client():
    try:
        # Streamlit Cloud: secrets stored in app settings
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    except Exception:
        # Local: use downloaded JSON file
        creds = Credentials.from_service_account_file("service_account.json", scopes=SCOPES)
    return gspread.authorize(creds)


def get_or_create_worksheet(spreadsheet, name, cols):
    try:
        ws = spreadsheet.worksheet(name)
        # Add any missing columns to existing sheet
        existing_headers = ws.row_values(1)
        for col in cols:
            if col not in existing_headers:
                ws.add_cols(1)
                ws.update_cell(1, len(existing_headers) + 1, col)
                existing_headers.append(col)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=name, rows=1000, cols=len(cols))
        ws.append_row(cols)
    return ws


def get_spreadsheet():
    client = get_client()
    return client.open_by_key(SHEET_ID)


def get_worksheets():
    spreadsheet = get_spreadsheet()
    leads_ws = get_or_create_worksheet(spreadsheet, LEADS_SHEET, LEAD_COLUMNS)
    email_ws = get_or_create_worksheet(spreadsheet, EMAIL_QUEUE_SHEET, EMAIL_QUEUE_COLUMNS)
    return leads_ws, email_ws


# ── LEADS ──────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=30)
def load_leads():
    leads_ws, _ = get_worksheets()
    data = leads_ws.get_all_records()
    if not data:
        return pd.DataFrame(columns=LEAD_COLUMNS)
    df = pd.DataFrame(data)
    for col in LEAD_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[LEAD_COLUMNS]


def append_leads(new_df):
    leads_ws, _ = get_worksheets()
    existing = load_leads()

    if not existing.empty and "place_id" in existing.columns:
        existing_ids = set(existing["place_id"].astype(str).tolist())
        new_df = new_df[~new_df["place_id"].astype(str).isin(existing_ids)]

    if new_df.empty:
        return 0

    rows = new_df[LEAD_COLUMNS].fillna("").values.tolist()
    leads_ws.append_rows(rows, value_input_option="USER_ENTERED")
    load_leads.clear()
    return len(rows)


def update_lead(place_id, updates: dict):
    leads_ws, _ = get_worksheets()
    headers = leads_ws.row_values(1)
    all_values = leads_ws.get_all_values()

    for i, row in enumerate(all_values[1:], start=2):  # skip header
        if len(row) > 0 and row[headers.index("place_id")] == str(place_id):
            for col_name, value in updates.items():
                if col_name in headers:
                    col_idx = headers.index(col_name) + 1
                    leads_ws.update_cell(i, col_idx, str(value))
            break

    load_leads.clear()


def delete_lead(place_id):
    leads_ws, _ = get_worksheets()
    headers = leads_ws.row_values(1)
    all_values = leads_ws.get_all_values()

    for i, row in enumerate(all_values[1:], start=2):
        if len(row) > 0 and row[headers.index("place_id")] == str(place_id):
            leads_ws.delete_rows(i)
            break

    load_leads.clear()


# ── EMAIL QUEUE ────────────────────────────────────────────────────────────────

@st.cache_data(ttl=30)
def load_email_queue():
    _, email_ws = get_worksheets()
    data = email_ws.get_all_records()
    if not data:
        return pd.DataFrame(columns=EMAIL_QUEUE_COLUMNS)
    df = pd.DataFrame(data)
    for col in EMAIL_QUEUE_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[EMAIL_QUEUE_COLUMNS]


def append_email_draft(draft: dict):
    _, email_ws = get_worksheets()
    row = [str(draft.get(col, "")) for col in EMAIL_QUEUE_COLUMNS]
    email_ws.append_row(row, value_input_option="USER_ENTERED")
    load_email_queue.clear()


def update_email_status(place_id, updates: dict):
    _, email_ws = get_worksheets()
    headers = email_ws.row_values(1)
    all_values = email_ws.get_all_values()

    for i, row in enumerate(all_values[1:], start=2):
        if len(row) > 0 and row[headers.index("place_id")] == str(place_id):
            for col_name, value in updates.items():
                if col_name in headers:
                    col_idx = headers.index(col_name) + 1
                    email_ws.update_cell(i, col_idx, str(value))
            break

    load_email_queue.clear()


# ── SETTINGS ───────────────────────────────────────────────────────────────────

@st.cache_data(ttl=60)
def load_settings():
    spreadsheet = get_spreadsheet()
    try:
        ws = spreadsheet.worksheet(SETTINGS_SHEET)
        records = ws.get_all_records()
        settings = dict(DEFAULT_SETTINGS)
        for row in records:
            if row.get("key") and row.get("value") is not None:
                settings[row["key"]] = str(row["value"])
        return settings
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=SETTINGS_SHEET, rows=50, cols=2)
        ws.append_row(["key", "value"])
        for k, v in DEFAULT_SETTINGS.items():
            ws.append_row([k, v])
        return dict(DEFAULT_SETTINGS)


def save_settings(settings: dict):
    spreadsheet = get_spreadsheet()
    try:
        ws = spreadsheet.worksheet(SETTINGS_SHEET)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=SETTINGS_SHEET, rows=50, cols=2)
        ws.append_row(["key", "value"])

    ws.clear()
    ws.append_row(["key", "value"])
    for k, v in settings.items():
        ws.append_row([k, str(v)])
    load_settings.clear()


# ── TEAM MEMBERS ───────────────────────────────────────────────────────────────

@st.cache_data(ttl=60)
def load_team_members():
    spreadsheet = get_spreadsheet()
    try:
        ws = spreadsheet.worksheet(TEAM_MEMBERS_SHEET)
        records = ws.get_all_records()
        return [r["name"] for r in records if r.get("name")]
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=TEAM_MEMBERS_SHEET, rows=50, cols=1)
        ws.append_row(["name"])
        return []


def save_team_members(members: list):
    spreadsheet = get_spreadsheet()
    try:
        ws = spreadsheet.worksheet(TEAM_MEMBERS_SHEET)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=TEAM_MEMBERS_SHEET, rows=50, cols=1)

    ws.clear()
    ws.append_row(["name"])
    for m in members:
        if m.strip():
            ws.append_row([m.strip()])
    load_team_members.clear()
