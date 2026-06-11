"""
sheets_helper.py — Google Sheets como base de datos
Sin dependencias de Microsoft, funciona desde cualquier IP.
"""

import os, io, json
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SHEET_ID   = os.environ.get("GOOGLE_SHEET_ID", "")
SHEET_NAME = "prompts"

COLUMNS = ["id", "nombre", "descripcion", "prompt", "version",
           "cambios", "responsable", "fecha", "categoria", "activo", "precision", "test_file"]


def _client():
    """Build an authenticated gspread client from Streamlit secrets or env."""
    try:
        # Streamlit Cloud: secrets stored as TOML
        creds_dict = dict(st.secrets["gcp_service_account"])
    except Exception:
        # Local: read from GOOGLE_CREDENTIALS_JSON env var (path to file)
        creds_path = os.environ.get("GOOGLE_CREDENTIALS_JSON", "credentials.json")
        with open(creds_path) as f:
            creds_dict = json.load(f)

    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)


def _get_or_create_worksheet(gc):
    """Open the spreadsheet and return (or create) the 'prompts' worksheet."""
    sh = gc.open_by_key(SHEET_ID)
    try:
        ws = sh.worksheet(SHEET_NAME)
    except gspread.exceptions.WorksheetNotFound:
        ws = sh.add_worksheet(title=SHEET_NAME, rows=1000, cols=len(COLUMNS))
        ws.append_row(COLUMNS)
    return ws


def load_from_sheets() -> pd.DataFrame:
    gc = _client()
    ws = _get_or_create_worksheet(gc)
    data = ws.get_all_records(expected_headers=COLUMNS)
    if not data:
        return pd.DataFrame(columns=COLUMNS)
    df = pd.DataFrame(data)
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df


def save_to_sheets(df: pd.DataFrame):
    gc = _client()
    ws = _get_or_create_worksheet(gc)
    ws.clear()
    # Write header + all rows
    values = [COLUMNS] + df[COLUMNS].fillna("").astype(str).values.tolist()
    ws.update(values, "A1")


def upload_test_file(file_bytes: bytes, file_name: str) -> str:
    """
    Upload test file to Google Drive in a 'PromptManager/Tests' folder.
    Returns the file name as reference.
    """
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
    except Exception:
        creds_path = os.environ.get("GOOGLE_CREDENTIALS_JSON", "credentials.json")
        with open(creds_path) as f:
            creds_dict = json.load(f)

    creds   = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    service = build("drive", "v3", credentials=creds)

    # Find or create PromptManager/Tests folder
    def get_or_create_folder(name, parent_id=None):
        q = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        if parent_id:
            q += f" and '{parent_id}' in parents"
        results = service.files().list(q=q, fields="files(id)").execute()
        files = results.get("files", [])
        if files:
            return files[0]["id"]
        meta = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
        if parent_id:
            meta["parents"] = [parent_id]
        f = service.files().create(body=meta, fields="id").execute()
        return f["id"]

    root_id  = get_or_create_folder("PromptManager")
    tests_id = get_or_create_folder("Tests", root_id)

    # Detect MIME type
    ext = file_name.rsplit(".", 1)[-1].lower()
    mime_map = {
        "pdf":  "application/pdf",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "xls":  "application/vnd.ms-excel",
        "csv":  "text/csv",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "txt":  "text/plain",
    }
    mime = mime_map.get(ext, "application/octet-stream")

    media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype=mime)
    service.files().create(
        body={"name": file_name, "parents": [tests_id]},
        media_body=media,
        fields="id",
    ).execute()
    return file_name


def download_test_file(file_name: str) -> bytes:
    from googleapiclient.discovery import build
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
    except Exception:
        creds_path = os.environ.get("GOOGLE_CREDENTIALS_JSON", "credentials.json")
        with open(creds_path) as f:
            creds_dict = json.load(f)

    creds   = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    service = build("drive", "v3", credentials=creds)

    results = service.files().list(
        q=f"name='{file_name}' and trashed=false",
        fields="files(id)",
    ).execute()
    files = results.get("files", [])
    if not files:
        raise FileNotFoundError(f"No se encontró el archivo: {file_name}")

    file_id = files[0]["id"]
    request = service.files().get_media(fileId=file_id)
    buf = io.BytesIO()
    buf.write(request.execute())
    return buf.getvalue()
