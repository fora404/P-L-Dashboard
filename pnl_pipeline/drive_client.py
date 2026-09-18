"""
Read-only Google Drive/Sheets access. No Apps Script equivalent -- this
replaces DriveApp/SpreadsheetApp calls with a service-account-authenticated
Python client. Streamlit never writes anywhere; scopes are read-only.
"""

from __future__ import annotations

import io

import gspread
import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/spreadsheets.readonly",
]


def _load_credentials() -> Credentials:
    info = dict(st.secrets["gcp_service_account"])
    return Credentials.from_service_account_info(info, scopes=SCOPES)


@st.cache_resource(show_spinner=False)
def get_drive_service():
    creds = _load_credentials()
    return build("drive", "v3", credentials=creds, cache_discovery=False)


@st.cache_resource(show_spinner=False)
def get_gspread_client() -> gspread.Client:
    creds = _load_credentials()
    return gspread.authorize(creds)


def list_files_in_folder(drive_service, folder_id: str) -> list[dict]:
    """Lists non-trashed files in a Drive folder, sorted by name (mirrors
    Apps Script's driveFiles.sort(localeCompare))."""
    files = []
    page_token = None
    query = f"'{folder_id}' in parents and trashed=false"
    while True:
        response = drive_service.files().list(
            q=query,
            fields="nextPageToken, files(id, name, size, modifiedTime)",
            pageToken=page_token,
            pageSize=1000,
        ).execute()
        files.extend(response.get("files", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            break
    files.sort(key=lambda f: f["name"])
    return files


def download_file_bytes(drive_service, file_id: str) -> bytes:
    request = drive_service.files().get_media(fileId=file_id)
    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(buf, request)
    done = False
    while not done:
        _status, done = downloader.next_chunk()
    return buf.getvalue()


def read_mapping_master_tabs(gspread_client: gspread.Client, spreadsheet_id: str) -> dict:
    """Returns raw row-lists (not dict-records) for each of the three
    Mapping Master tabs, so mapping_master.py can apply the exact same
    header-index lookup as the Apps Script original and control its own
    date-vs-string defense on the Period column."""
    ss = gspread_client.open_by_key(spreadsheet_id)
    return {
        "sku_rows": ss.worksheet("SKU_MAPPING_MASTER").get_all_values(),
        "bom_rows": ss.worksheet("BOM").get_all_values(),
        "cost_rows": ss.worksheet("COST_HISTORY").get_all_values(),
    }
